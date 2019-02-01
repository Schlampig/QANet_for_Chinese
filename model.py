# -*- coding: utf-8 -*-

import tensorflow as tf
from layers import initializer, regularizer, highway, conv, residual_block, mask_logits, optimized_trilinear_for_attention, total_params


class Model(object):
    def __init__(self, config, batch=None, word_mat=None, trainable=True, opt=True, demo=False, graph=None):
        self.config = config
        self.demo = demo
        self.graph = graph if graph is not None else tf.Graph()
        with self.graph.as_default():
            y1 = [[0, 0]]
            y2 = [[0, 0]]
            self.global_step = tf.get_variable('global_step', shape=[], dtype=tf.int32, initializer=tf.constant_initializer(0), trainable=False)
            self.dropout = tf.placeholder_with_default(0.0, (), name="dropout")
            if self.demo:
                self.c = tf.placeholder(tf.int32, [1, None], "context")
                self.q = tf.placeholder(tf.int32, [1, None], "question")
                self.y1 = y1
                self.y2 = y2
                self.qa_id = tf.cast(list(range(1)), tf.int32)
            else:
                self.c, self.q, self.y1, self.y2, self.qa_id = batch.get_next()

            self.word_mat = tf.constant(word_mat, dtype=tf.float32)

            self.c_mask = tf.cast(self.c, tf.bool)
            self.q_mask = tf.cast(self.q, tf.bool)
            self.c_len = tf.reduce_sum(tf.cast(self.c_mask, tf.int32), axis=1)
            self.q_len = tf.reduce_sum(tf.cast(self.q_mask, tf.int32), axis=1)
            if opt:
                N = config.batch_size if not self.demo else 1
                self.c_maxlen = tf.reduce_max(self.c_len)
                self.q_maxlen = tf.reduce_max(self.q_len)
                self.c = tf.slice(self.c, [0, 0], [N, self.c_maxlen])
                self.q = tf.slice(self.q, [0, 0], [N, self.q_maxlen])
                self.c_mask = tf.slice(self.c_mask, [0, 0], [N, self.c_maxlen])
                self.q_mask = tf.slice(self.q_mask, [0, 0], [N, self.q_maxlen])
                self.y1 = tf.slice(self.y1, [0, 0], [N, self.c_maxlen])
                self.y2 = tf.slice(self.y2, [0, 0], [N, self.c_maxlen])
            else:
                if self.demo:
                    self.c_maxlen = tf.reduce_max(self.c_len)
                    self.q_maxlen = tf.reduce_max(self.q_len)
                else:
                    self.c_maxlen = config.para_limit
                    self.q_maxlen = config.ques_limit

            self.forward()
            total_params()

            if trainable:
                self.lr = tf.minimum(config.learning_rate, 0.001 / tf.log(999.) * tf.log(tf.cast(self.global_step, tf.float32) + 1))
                self.opt = tf.train.AdamOptimizer(learning_rate = self.lr, beta1 = 0.8, beta2 = 0.999, epsilon = 1e-7)
                grads = self.opt.compute_gradients(self.loss)
                gradients, variables = zip(*grads)
                capped_grads, _ = tf.clip_by_global_norm(gradients, config.grad_clip)
                self.train_op = self.opt.apply_gradients(zip(capped_grads, variables), global_step=self.global_step)

    def forward(self):
        config = self.config
        N, PL, QL, d, nh = config.batch_size if not self.demo else 1, self.c_maxlen, self.q_maxlen, config.hidden, config.num_heads

        with tf.variable_scope("Input_Embedding_Layer"):
            c_emb = tf.nn.dropout(tf.nn.embedding_lookup(self.word_mat, self.c), 1.0 - self.dropout)
            q_emb = tf.nn.dropout(tf.nn.embedding_lookup(self.word_mat, self.q), 1.0 - self.dropout)
            c_emb = highway(c_emb, size = d, scope = "highway", dropout = self.dropout, reuse = None)
            q_emb = highway(q_emb, size = d, scope = "highway", dropout = self.dropout, reuse = True)

        with tf.variable_scope("Embedding_Encoder_Layer"):
            c = residual_block(c_emb,
                               num_blocks=1,
                               num_conv_layers=4,
                               kernel_size=7,
                               mask=self.c_mask,
                               num_filters=d,
                               num_heads=nh,
                               seq_len=self.c_len,
                               scope="Encoder_Residual_Block",
                               bias=False,
                               dropout=self.dropout)
            q = residual_block(q_emb,
                               num_blocks=1,
                               num_conv_layers=4,
                               kernel_size=7,
                               mask=self.q_mask,
                               num_filters=d,
                               num_heads=nh,
                               seq_len=self.q_len,
                               scope="Encoder_Residual_Block",
                               reuse=True, # Share the weights between passage and question
                               bias=False,
                               dropout=self.dropout)

        with tf.variable_scope("Context_to_Query_Attention_Layer"):
            S = optimized_trilinear_for_attention([c, q], self.c_maxlen, self.q_maxlen, input_keep_prob = 1.0 - self.dropout)
            mask_q = tf.expand_dims(self.q_mask, 1)
            S_ = tf.nn.softmax(mask_logits(S, mask=mask_q))
            mask_c = tf.expand_dims(self.c_mask, 2)
            S_T = tf.transpose(tf.nn.softmax(mask_logits(S, mask=mask_c), dim=1), (0, 2, 1))
            self.c2q = tf.matmul(S_, q)
            self.q2c = tf.matmul(tf.matmul(S_, S_T), c)
            attention_outputs = [c, self.c2q, c * self.c2q, c * self.q2c]

        with tf.variable_scope("Model_Encoder_Layer"):
            inputs = tf.concat(attention_outputs, axis=-1)
            self.enc = [conv(inputs, d, name="input_projection")]
            for i in range(3):
                if i % 2 == 0:  # dropout every 2 blocks
                    self.enc[i] = tf.nn.dropout(self.enc[i], 1.0 - self.dropout)
                self.enc.append(residual_block(self.enc[i],
                                               num_blocks=7,
                                               num_conv_layers=2,
                                               kernel_size=5,
                                               mask=self.c_mask,
                                               num_filters=d,
                                               num_heads=nh,
                                               seq_len=self.c_len,
                                               scope="Model_Encoder",
                                               bias=False,
                                               reuse=True if i > 0 else None,
                                               dropout=self.dropout))

        with tf.variable_scope("Output_Layer"):
            start_logits = tf.squeeze(conv(tf.concat([self.enc[1], self.enc[2]],axis=-1), 1, bias=False, name="start_pointer"), -1)
            end_logits = tf.squeeze(conv(tf.concat([self.enc[1], self.enc[3]],axis=-1), 1, bias=False, name="end_pointer"), -1)
            self.logits = [mask_logits(start_logits, mask=self.c_mask), mask_logits(end_logits, mask=self.c_mask)]
            logits1, logits2 = [l for l in self.logits]

            outer = tf.matmul(tf.expand_dims(tf.nn.softmax(logits1), axis=2), tf.expand_dims(tf.nn.softmax(logits2), axis=1))
            outer = tf.matrix_band_part(outer, 0, -1)
            self.yp1 = tf.argmax(tf.reduce_max(outer, axis=2), axis=1)
            self.yp2 = tf.argmax(tf.reduce_max(outer, axis=1), axis=1)
            losses = tf.nn.softmax_cross_entropy_with_logits(logits=logits1, labels=self.y1)
            losses2 = tf.nn.softmax_cross_entropy_with_logits(logits=logits2, labels=self.y2)
            self.loss = tf.reduce_mean(losses + losses2)

        if config.l2_norm is not None:
            variables = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
            l2_loss = tf.contrib.layers.apply_regularization(regularizer, variables)
            self.loss += l2_loss

        if config.decay is not None:
            self.var_ema = tf.train.ExponentialMovingAverage(config.decay)
            ema_op = self.var_ema.apply(tf.trainable_variables())
            with tf.control_dependencies([ema_op]):
                self.loss = tf.identity(self.loss)

                self.assign_vars = []
                for var in tf.global_variables():
                    v = self.var_ema.average(var)
                    if v:
                        self.assign_vars.append(tf.assign(var,v))

    def get_loss(self):
        return self.loss

    def get_global_step(self):
        return self.global_step
