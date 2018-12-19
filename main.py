# -*- coding: utf-8 -*-

import os
import numpy as np
from tqdm import tqdm
import json as json
import tensorflow as tf

from model import Model
from util import get_record_parser, get_dataset, get_batch_dataset, convert_tokens, evaluate, evaluate_batch


def train(config):
    with open(config.word_emb_file, "r") as fh:
        word_mat = np.array(json.load(fh), dtype=np.float32)
    if config.use_char_emb:
        with open(config.char_emb_file, "r") as fh:
            char_mat = np.array(json.load(fh), dtype=np.float32)
    else:
        char_mat = None
    with open(config.train_eval_file, "r") as fh:
        train_eval_file = json.load(fh)
    with open(config.dev_eval_file, "r") as fh:
        dev_eval_file = json.load(fh)
    with open(config.dev_meta, "r") as fh:
        meta = json.load(fh)
    dev_total = meta["total"]
    
    print("Building model...")
    parser = get_record_parser(config)
    graph = tf.Graph()
    with graph.as_default() as g:
        # 获取训练数据与验证数据
        train_dataset = get_batch_dataset(config.train_record_file, parser, config)
        dev_dataset = get_dataset(config.dev_record_file, parser, config)
        handle = tf.placeholder(tf.string, shape=[])
        iterator = tf.data.Iterator.from_string_handle(handle, train_dataset.output_types, train_dataset.output_shapes)
        # 生成训练数据与验证数据的迭代器
        train_iterator = train_dataset.make_one_shot_iterator()
        dev_iterator = dev_dataset.make_one_shot_iterator()
        # 生成模型结构
        model = Model(config, iterator, word_mat, char_mat, graph = g)
        # 初始化配置
        sess_config = tf.ConfigProto(allow_soft_placement=True)
        sess_config.gpu_options.allow_growth = True

        # 初始化用于early-stopping的评价条件
        patience = 0
        best_f1 = 0.
        best_em = 0.
        
        with tf.Session(config=sess_config) as sess:
            writer = tf.summary.FileWriter(config.log_dir)
            sess.run(tf.global_variables_initializer())
            saver = tf.train.Saver()
            train_handle = sess.run(train_iterator.string_handle())
            dev_handle = sess.run(dev_iterator.string_handle())
            if os.path.exists(os.path.join(config.save_dir, "checkpoint")):
                saver.restore(sess, tf.train.latest_checkpoint(config.save_dir))
            global_step = max(sess.run(model.global_step), 1)  # 初始化全局步长

            for _ in tqdm(range(global_step, config.num_steps + 1)):  # 训练模型
                global_step = sess.run(model.global_step) + 1
                # 每个step更新loss与
                loss, train_op = sess.run([model.loss, model.train_op], feed_dict={handle: train_handle, model.dropout: config.dropout})
                # 每到period，存储batch的loss信息
                if global_step % config.period == 0:
                    loss_sum = tf.Summary(value=[tf.Summary.Value(tag="model/loss", simple_value=loss), ])
                    writer.add_summary(loss_sum, global_step)
                # 每到checkpoint存当前参数
                if global_step % config.checkpoint == 0:
                    # 训练集的评估结果（多个batch）
                    _, summ = evaluate_batch(model, config.val_num_batches, train_eval_file, sess, "train", handle, train_handle)
                    for s in summ:
                        writer.add_summary(s, global_step)
                    
                    # 验证集的评估结果（for early-stopping）
                    metrics, summ = evaluate_batch(model, dev_total // config.batch_size + 1, dev_eval_file, sess, "dev", handle, dev_handle)
                    for s in summ:
                        writer.add_summary(s, global_step)
                    writer.flush()
                    # 判断停步条件
                    dev_f1 = metrics["f1"]
                    dev_em = metrics["exact_match"]
                    if dev_f1 < best_f1 and dev_em < best_em:
                        patience += 1
                        if patience > config.early_stop:
                            break
                    else:
                        patience = 0  # patience连续加10次才能停步，否则重头开始
                        best_em = max(best_em, dev_em)
                        best_f1 = max(best_f1, dev_f1)
                    # 存模型信息
                    filename = os.path.join(config.save_dir, "model_{}.ckpt".format(global_step))
                    saver.save(sess, filename)


def test(config):
    with open(config.word_emb_file, "r") as fh:
        word_mat = np.array(json.load(fh), dtype=np.float32)
    if config.use_char_emb:
        with open(config.char_emb_file, "r") as fh:
            char_mat = np.array(json.load(fh), dtype=np.float32)
    else:
        char_mat = None
    with open(config.test_eval_file, "r") as fh:
        eval_file = json.load(fh)
    with open(config.test_meta, "r") as fh:
        meta = json.load(fh)
    test_total = meta["total"]

    graph = tf.Graph()
    print("Loading model...")
    with graph.as_default() as g:
        # 获取测试数据batch
        test_batch = get_dataset(config.test_record_file, get_record_parser(config, is_test=True), config).make_one_shot_iterator()
        # 生成模型结构
        model = Model(config, test_batch, word_mat, char_mat, trainable=False, graph=g)
        # 初始化配置
        sess_config = tf.ConfigProto(allow_soft_placement=True)
        sess_config.gpu_options.allow_growth = True
        
        with tf.Session(config=sess_config) as sess:
            sess.run(tf.global_variables_initializer())
            saver = tf.train.Saver()
            saver.restore(sess, tf.train.latest_checkpoint(config.save_dir))
            if config.decay < 1.0:
                sess.run(model.assign_vars)
            # 预测数据(一个batch预测)
            losses = []
            answer_dict = {}
            remapped_dict = {}
            for _ in tqdm(range(test_total // config.batch_size + 1)):
                qa_id, loss, yp1, yp2 = sess.run([model.qa_id, model.loss, model.yp1, model.yp2])
                answer_dict_, remapped_dict_ = convert_tokens(eval_file, qa_id.tolist(), yp1.tolist(), yp2.tolist())
                answer_dict.update(answer_dict_)
                remapped_dict.update(remapped_dict_)
                losses.append(loss)
            loss = np.mean(losses)  # 可选观察或弃用
            metrics = evaluate(eval_file, answer_dict)
            with open(config.answer_file, "w") as fh:
                json.dump(remapped_dict, fh)
            print("Exact Match: {}, F1: {}".format(metrics['exact_match'], metrics['f1']))
            
