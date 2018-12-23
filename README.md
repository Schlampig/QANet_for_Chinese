# QANet

## Source:
This work is mainly coresponding to:
  * **paper**: [QANet: Combining Local Convolution with Global Self-Attention for Reading Comprehension](https://arxiv.org/abs/1804.09541), [DuReader- a Chinese Machine Reading Comprehension Dataset](https://arxiv.org/abs/1711.05073v2) <br>
  * **code**: a tensorflow implemention from [NLPLearn](https://github.com/NLPLearn/QANet), a tensorflow implemention from [SeanLee97](https://github.com/SeanLee97/QANet_dureader), a keras approach from [ewrfcas](https://github.com/ewrfcas/QANet_keras), a basic introduction for Reading Comprehension (RC) task from [facebookresearch](https://github.com/facebookresearch/DrQA) <br>
  * **embedding dictionary**: [Tencent AI Lab Embedding Corpus for Chinese Words and Phraseshttps](//ai.tencent.com/ailab/nlp/embedding.html) <br>
  * **embedding dictionary example**: Each line of Tencent_AILab_ChineseEmbedding.txt is like \[str, vec(200 dimensions)\] below:
  ```
  ['</s>', '0.002001', '0.002210', '-0.001915', '-0.001639', '0.000683', '0.001511', '0.000470', '0.000106', '-0.001802', '0.001109', '-0.002178', '0.000625', '-0.000376', '-0.000479', '-0.001658', '-0.000941', '0.001290', '0.001513', '0.001485', '0.000799', '0.000772', '-0.001901', '-0.002048', '0.002485', '0.001901', '0.001545', '-0.000302', '0.002008', '-0.000247', '0.000367', '-0.000075', '-0.001492', '0.000656', '-0.000669', '-0.001913', '0.002377', '0.002190', '-0.000548', '-0.000113', '0.000255', '-0.001819', '-0.002004', '0.002277', '0.000032', '-0.001291', '-0.001521', '-0.001538', '0.000848', '0.000101', '0.000666', '-0.002107', '-0.001904', '-0.000065', '0.000572', '0.001275', '-0.001585', '0.002040', '0.000463', '0.000560', '-0.000304', '0.001493', '-0.001144', '-0.001049', '0.001079', '-0.000377', '0.000515', '0.000902', '-0.002044', '-0.000992', '0.001457', '0.002116', '0.001966', '-0.001523', '-0.001054', '-0.000455', '0.001001', '-0.001894', '0.001499', '0.001394', '-0.000799', '-0.000776', '-0.001119', '0.002114', '0.001956', '-0.000590', '0.002107', '0.002410', '0.000908', '0.002491', '-0.001556', '-0.000766', '-0.001054', '-0.001454', '0.001407', '0.000790', '0.000212', '-0.001097', '0.000762', '0.001530', '0.000097', '0.001140', '-0.002476', '0.002157', '0.000240', '-0.000916', '-0.001042', '-0.000374', '-0.001468', '-0.002185', '-0.001419', '0.002139', '-0.000885', '-0.001340', '0.001159', '-0.000852', '0.002378', '-0.000802', '-0.002294', '0.001358', '-0.000037', '-0.001744', '0.000488', '0.000721', '-0.000241', '0.000912', '-0.001979', '0.000441', '0.000908', '-0.001505', '0.000071', '-0.000030', '-0.001200', '-0.001416', '-0.002347', '0.000011', '0.000076', '0.000005', '-0.001967', '-0.002481', '-0.002373', '-0.002163', '-0.000274', '0.000696', '0.000592', '-0.001591', '0.002499', '-0.001006', '-0.000637', '-0.000702', '0.002366', '-0.001882', '0.000581', '-0.000668', '0.001594', '0.000020', '0.002135', '-0.001410', '-0.001303', '-0.002096', '-0.001833', '-0.001600', '-0.001557', '0.001222', '-0.000933', '0.001340', '0.001845', '0.000678', '0.001475', '0.001238', '0.001170', '-0.001775', '-0.001717', '-0.001828', '-0.000066', '0.002065', '-0.001368', '-0.001530', '-0.002098', '0.001653', '-0.002089', '-0.000290', '0.001089', '-0.002309', '-0.002239', '0.000721', '0.001762', '0.002132', '0.001073', '0.001581', '-0.001564', '-0.001820', '0.001987', '-0.001382', '0.000877', '0.000287', '0.000895', '-0.000591', '0.000099', '-0.000843', '-0.000563']
```
<br>

## Dataset
* **source**: The dataset used for this work is mainly from [DuReader Dataset](http://ai.baidu.com/broad/subordinate?dataset=dureader). <br>
* **format**: Training, validation, and test data are stored in three large json files, with the structure like this: json = {'data': lst_data} where lst_data = \[sample_1, sample_2, ..., sample_N\]. In detail, sample_i is expanded as follows: <br>
```
{'title': '', 
 'paragraphs': [{'context': string, 
                 'segmented_context': list, 
                 'qas': [{'question': string, 
                          'segmented_question': list, 
                          'answers': [{'text': string, 
                                       'answer_span': [int_start, int_end]}], 
                                       'id': int_index}]}]}
```
<br>
* **example**: an example sample is given as follows:
```
{'title': '', 'paragraphs': [{'context': '布袋线，为位于台湾台南市新营区与嘉义县布袋镇间，由台湾糖业股份有限公司新营总厂经营之轻便铁路，今既废止。此线为糖业铁路客运化之始，开办于1909年。纵贯线铁路在选线时，在嘉义曾文溪间即有经过盐水港（今盐水）或新营庄（今新营）之议。详见纵贯线(南段)。当时虽曾研议另建新营经由盐水至北门屿（今北门区）之官线铁道支线弥补不足，唯此案未成真。新营＝盐水＝布袋间铁道运输稍后由制糖会社完成，属于盐水港制糖兼办之客运业务。据铁道部之资料，新营庄＝盐水港间五哩三分于1909年（明治42年）5月20日开始营业，亦为台湾首条糖业铁路定期营业线。然而，根据同年3月4日《台湾日日新报》资料，在官方核准开办营业线之前，当时新营-{庄}-＝岸内-{庄}-间即对外办理客运（一日4往复），车资内地人（即日本人）15钱、本岛人（台湾人）10钱；1913年（大正2年）3月8日，营业区间延至布袋嘴（今布袋）。战后布袋线曾进行数次改动。包括糖铁新营车站（原址位于台铁车站旁，今已成停车场）因破烂不堪，1950年迁移百余米至今址。另外，布袋车站因位于市区之外，曾应民众要求，利用盐业铁路（台盐公司所有）延伸营业间区750m至贴近市区的半路店、但仅维持数年。沿线各车站亦有重修，大部份皆非日治时期原貌。布袋线为762mm狭轨铁路，但在新营＝岸内间，另有一条并行之新岸线，为762mm及1067mm轨距之三线轨道。后者可允许台铁货车驶至岸内。新营-厂前-（南信号所）-工作站前-东太子宫-太子宫-南门-盐水-岸内-义竹-埤子头-安溪寮-前东港-振寮-布袋（-半路店）支线：东子宫-纸浆厂', 'segmented_context': ['布袋', '线', '，', '为', '位于', '台湾', '台南市', '新', '营区', '与', '嘉义县', '布袋镇', '间', '，', '由', '台湾糖业', '股份', '有限公司', '新营', '总厂', '经营', '之', '轻便', '铁路', '，', '今', '既', '废止', '。', '此线', '为', '糖业', '铁路', '客运', '化之始', '，', '开办', '于', '1909', '年', '。', '纵贯线', '铁路', '在', '选线', '时', '，', '在', '嘉义', '曾文溪', '间', '即', '有', '经过', '盐水', '港', '（', '今', '盐水', '）', '或', '新营', '庄', '（', '今', '新营', '）', '之议', '。', '详见', '纵贯线', '(', '南段', ')', '。', '当时', '虽', '曾', '研议', '另', '建新', '营', '经由', '盐水', '至', '北门', '屿', '（', '今', '北门', '区', '）', '之', '官线', '铁道', '支线', '弥补', '不足', '，', '唯', '此案', '未成', '真', '。', '新营', '＝', '盐水', '＝', '布袋', '间', '铁道', '运输', '稍后', '由', '制糖', '会社', '完成', '，', '属于', '盐水', '港', '制糖', '兼办', '之', '客运', '业务', '。', '据', '铁道部', '之', '资料', '，', '新营', '庄', '＝', '盐水', '港间', '五哩', '三分', '于', '1909', '年', '（', '明治', '42', '年', '）', '5', '月', '20', '日', '开始', '营业', '，', '亦', '为', '台湾', '首条', '糖业', '铁路', '定期', '营业', '线', '。', '然而', '，', '根据', '同年', '3', '月', '4', '日', '《', '台湾', '日日', '新报', '》', '资料', '，', '在', '官方', '核准', '开办', '营业', '线', '之前', '，', '当时', '新营', '-', '{', '庄', '}', '-', '＝', '岸内', '-', '{', '庄', '}', '-', '间', '即', '对外', '办理', '客运', '（', '一日', '4', '往复', '）', '，', '车资', '内地', '人', '（', '即', '日本', '人', '）', '15', '钱', '、', '本岛人', '（', '台湾人', '）', '10', '钱', '；', '1913', '年', '（', '大正', '2', '年', '）', '3', '月', '8', '日', '，', '营业', '区间', '延至', '布袋', '嘴', '（', '今', '布袋', '）', '。', '战后', '布袋', '线', '曾', '进行', '数次', '改动', '。', '包括', '糖铁', '新营', '车站', '（', '原址', '位于', '台铁', '车站', '旁', '，', '今', '已成', '停车场', '）', '因', '破烂不堪', '，', '1950', '年', '迁移', '百余米', '至今', '址', '。', '另外', '，', '布袋', '车站', '因', '位于', '市区', '之外', '，', '曾应', '民众', '要求', '，', '利用', '盐业', '铁路', '（', '台盐', '公司', '所有', '）', '延伸', '营业', '间区', '750m', '至', '贴近', '市区', '的', '半路', '店', '、', '但仅', '维持', '数年', '。', '沿线', '各', '车站', '亦', '有', '重修', '，', '大部份', '皆', '非日治', '时期', '原貌', '。', '布袋', '线为', '762mm', '狭轨', '铁路', '，', '但', '在', '新营', '＝', '岸内间', '，', '另有', '一条', '并行', '之新', '岸线', '，', '为', '762mm', '及', '1067mm', '轨距', '之', '三线', '轨道', '。', '后者', '可', '允许', '台铁', '货车', '驶至岸', '内', '。', '新营', '-', '厂前', '-', '（', '南', '信号', '所', '）', '-', '工作站', '前', '-', '东', '太子', '宫', '-', '太子', '宫', '-', '南门', '-', '盐水', '-', '岸内', '-', '义竹', '-', '埤子头', '-', '安溪', '寮', '-', '前', '东港', '-', '振', '寮', '-', '布袋', '（', '-', '半路', '店', '）', '支线', '：', '东', '子宫', '-', '纸浆厂'], 'qas': [{'question': '布袋线是哪家公司经营的轻便铁路？', 'segmented_question': ['布袋', '线', '是', '哪家', '公司', '经营', '的', '轻便', '铁路', '？'], 'answers': [{'text': '台湾糖业股份有限公司新营总厂', 'answer_span': [15, 19]}], 'id': 157}]}]}
```
<br>

## Requirements
  * Python>=3.5
  * TensorFlow>=1.5
  * NumPy
  * tqdm
  * ujson

## TODO
- [x] Simplize the code in model.py, layer.py, utils.py, main.py 
- [x] Add prepare.py for training and testing DuReader-based Dataset 
- [x] Train and test a weak baseline
- [x] Write predict.py and preprocess.py (for operate predicted questions and contexts)
- [ ] Train and test a strong baseline
- [ ] Run a demo on a special domain
