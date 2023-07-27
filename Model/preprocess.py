import torch
import logging
import copy
import json
import pandas
import nltk
from transformers import BertTokenizerFast, BertTokenizer
from torch.utils.data import TensorDataset


logger = logging.getLogger(__name__)

class InputExample(object):
    def __init__(self, text_a, label):
        self.text_a = text_a
        self.label = label

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        dic = copy.deepcopy(self.__dict__)
        return dic

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

class InputFeatures(object):
    def __init__(self, input_text, input_ids, input_mask,input_len, segment_ids, label_ids, pos_ids, tokens, token_span):
        self.input_len = input_len
        self.input_text = input_text
        self.input_ids = input_ids
        self.input_mask = input_mask
        self.segment_ids = segment_ids
        self.label_ids = label_ids
        self.pos_ids = pos_ids
        self.tokens = tokens
        self.token_span = token_span

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        dic = copy.deepcopy(self.__dict__)
        return dic

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

def convert_examples_to_features(examples,max_seq_length,tokenizer):
    
    features = []
    for (ex_index, example) in enumerate(examples):
        if ex_index % 10000 == 0:
            logger.info("Writing example %d of %d", ex_index, len(examples))
        
        label_ids = example.label
        text = example.text_a
        cls_token="[CLS]"
        sep_token="[SEP]"
        try:
            tokens = tokenizer.tokenize(text)
        except Exception as e:
            text = "1"
            tokens = ["1"]
            label_ids = 0
        if len(tokens) > max_seq_length - 2:
            tokens = tokens[:max_seq_length - 2]
        
        tokens = [cls_token] + tokens+ [sep_token]
        segment_ids = [0] * len(tokens)
        input_ids = tokenizer.convert_tokens_to_ids(tokens)
        input_mask = [1] * len(input_ids)
        
        padding = [0] * (max_seq_length-len(input_ids))
        input_len = len(input_ids)

        input_ids += padding
        input_mask += padding
        segment_ids += padding

        try:
            assert len(input_ids) == max_seq_length
            assert len(input_mask) == max_seq_length
            assert len(segment_ids) == max_seq_length
        except:
            print("[ERROR]: "+ "may be OOV in " + text + " and it will be delete")
            continue

        if ex_index < 5:
            logger.info("*** Example ***")
            logger.info("tokens: %s", " ".join([str(x) for x in tokens]))
            logger.info("input_ids: %s", " ".join([str(x) for x in input_ids]))
            logger.info("input_mask: %s", " ".join([str(x) for x in input_mask]))
            logger.info("segment_ids: %s", " ".join([str(x) for x in segment_ids]))
            logger.info("label_ids: %s", str(label_ids))

        features.append(InputFeatures(input_text=text, 
                                      input_ids=input_ids, 
                                      input_mask=input_mask,
                                      input_len = input_len,
                                      segment_ids=segment_ids, 
                                      label_ids=label_ids,
                                      pos_ids = [],
                                      tokens = [], 
                                      token_span = []))
    return features

def convert_NERexamples_to_features(examples,label_list,pos_list,max_seq_length,tokenizer):
        label_map = {label: i for i, label in enumerate(label_list)}
        pos_map = {label: i for i, label in enumerate(pos_list)}
        features = []
        cls_token="[CLS]"
        sep_token="[SEP]"
        for (ex_index, example) in enumerate(examples):
            if ex_index % 10000 == 0:
                logger.info("Writing example %d of %d", ex_index, len(examples))
            if isinstance(example.text_a,list):
                example.text_a = " ".join(example.text_a)
            example.text_a = example.text_a.replace("\n","")
            print(example.text_a)
            text = example.text_a
            #nltk_tokens = nltk.word_tokenize(text)
            nltk_tokens = text.split(' ')
            pos_tags = nltk.pos_tag(nltk_tokens)
            tokens = tokenizer.tokenize(example.text_a)
            #切出来的token的首尾位置
            token_span = tokenizer.encode_plus(example.text_a, return_offsets_mapping=True, add_special_tokens=False)["offset_mapping"]
            i = 0
            continue_flag = 0
            label_ids = []
            pos_ids = []
            for begin_end in token_span:
                end = begin_end[-1]
                #continue_flag标志前一个词是不是非完整的切分词
                if not continue_flag:
                    #如果切出来的token结束位置是空格，代表分词到这里结束
                    if end >= len(text) or text[end] == ' ':
                        label_ids.append(label_map[example.label[i]])
                        pos_ids.append(pos_map[pos_tags[i][-1]])
                        i = i + 1
                    else:
                        label = example.label[i]
                        label_ids.append(label_map[label])
                        pos_ids.append(pos_map[pos_tags[i][-1]])
                        continue_flag = 1
                        if label.startswith('B'):
                            continue_label =  label.replace('B', 'I')
                        else:   
                            continue_label =  label
                else:
                    if end >= len(text) or text[end] == ' ':
                        label_ids.append(label_map[continue_label])
                        pos_ids.append(pos_map[pos_tags[i][-1]])
                        i = i + 1
                        continue_flag = 0
                    else:
                        label_ids.append(label_map[continue_label])
                        pos_ids.append(pos_map[pos_tags[i][-1]])

            # Account for [CLS] and [SEP] with "- 2".
            special_tokens_count = 2
            if len(tokens) > max_seq_length - special_tokens_count:
                tokens = tokens[: (max_seq_length - special_tokens_count)]
                label_ids = label_ids[: (max_seq_length - special_tokens_count)]
                pos_ids = pos_ids[: (max_seq_length - special_tokens_count)]

            tokens += [sep_token]
            label_ids += [label_map['O']]
            pos_ids += [pos_map['']]
            segment_ids = [0] * len(tokens)

            tokens = [cls_token] + tokens
            label_ids = [label_map['O']] + label_ids
            pos_ids = [pos_map['']] + pos_ids
            segment_ids = [0] + segment_ids

            input_ids = tokenizer.convert_tokens_to_ids(tokens)
            input_mask = [1] * len(input_ids)
            input_len = len(label_ids)
            padding = [0] * (max_seq_length-len(input_ids))

            input_ids += padding
            input_mask += padding
            segment_ids += padding
            label_ids += padding
            pos_ids += padding
            tokens.pop(0)
            tokens.pop()
            
            try:
                assert len(input_ids) == max_seq_length
                assert len(input_mask) == max_seq_length
                assert len(segment_ids) == max_seq_length
                assert len(label_ids) == max_seq_length
                assert len(pos_ids) == max_seq_length
            except:
                print("[ERROR]: "+ "may be OOV in " + text + " and it will be delet")
                logger.info("*** Example ***")
                logger.info("tokens: %s", " ".join([str(x) for x in tokens]))
                logger.info("token_span: %s", " ".join([str(x) for x in token_span]))
                logger.info("input_ids: %s", " ".join([str(x) for x in input_ids]))
                logger.info("input_mask: %s", " ".join([str(x) for x in input_mask]))
                logger.info("segment_ids: %s", " ".join([str(x) for x in segment_ids]))
                logger.info("label_ids: %s", " ".join([str(x) for x in label_ids]))
                logger.info("pos_ids: %s", " ".join([str(x) for x in pos_ids]))
                continue
            if ex_index < 5:
                logger.info("*** Example ***")
                logger.info("text: %s", text)
                logger.info("tokens: %s", " ".join([str(x) for x in tokens]))
                logger.info("input_ids: %s", " ".join([str(x) for x in input_ids]))
                logger.info("input_mask: %s", " ".join([str(x) for x in input_mask]))
                logger.info("segment_ids: %s", " ".join([str(x) for x in segment_ids]))
                logger.info("label_ids: %s", " ".join([str(x) for x in label_ids]))
                logger.info("pos_ids: %s", " ".join([str(x) for x in pos_ids]))

            features.append(InputFeatures(input_text=text, input_ids=input_ids, input_mask=input_mask,input_len = input_len,
                                        segment_ids=segment_ids, label_ids=label_ids, pos_ids = pos_ids, tokens = tokens, token_span = token_span))
        return features 

class dataloader:
    def __init__(self, dtype, config, classifier_path = None):
        self.config = config
        self.NERconfig = config
        if dtype == 'train':
            self.trainpath = self.config.trainpath
            self.examples = self.get_traindata()
        elif dtype == 'NERtrain':
            self.trainpath = self.NERconfig.trainpath
            self.examples = self.get_NERtraindata()
        elif dtype == 'dev':
            self.devpath = self.config.devpath
            self.examples = self.get_devdata()
        elif dtype == 'NERdev':
            self.devpath = self.NERconfig.devpath
            self.examples = self.get_NERdevdata()
        elif dtype == 'NERtest':
            self.testpath = self.NERconfig.testpath
            self.examples = self.get_NERtestdata()
        elif dtype == 'test':
            self.testpath = self.config.testpath
            self.examples = self.get_testdata()
        elif dtype == 'classifier':
            self.testpath = classifier_path
            self.examples = self.get_testdata()
        elif dtype == 'NERclassifier':
            self.testpath = classifier_path
            self.examples = self.get_NERtestdata()


    def get_traindata(self):
        return self.create_examples(self.readText(self.trainpath))
    
    def get_NERtraindata(self):
        return self.create_NERexamples((self.readNERText(self.trainpath)), "train")

    def get_devdata(self):
        return self.create_examples(self.readText(self.devpath))
    
    def get_NERdevdata(self):
        return self.create_NERexamples((self.readNERText(self.devpath)), "dev")

    def get_testdata(self):
        return self.create_examples(self.readtestText(self.testpath))

    def get_NERtestdata(self):
        return self.create_NERexamples((self.readNERText(self.testpath)), "test")
    
    def readtestText(self, path):
        '''
        return testset list[(text,label=0)]
        '''
        Texts = []
        df = pandas.read_csv(path)
        for i in range(len(df)):
            Texts.append((df["text"][i],0))
        return Texts

    def readText(self, path):        
        Texts = []
        df = pandas.read_csv(path)
        ##### Sample imbalance adjustment #####
        df0 = df[df["label"] == 0]
        df1 = df[df["label"] == 1]
        print(">> Sample proportion == True:False {}:{}".format(len(df0),len(df1)))
        for _,row in df0.iterrows():
            Texts.append((row["text"],int(row["label"])))
        count = 0
        for _,row in df1.iterrows():
            if count < len(df0):
                Texts.append((row["text"],int(row["label"])))
                count += 1
            else:
                break
     
        ##### No need to adjust proportion #####
        #for i in range(len(df)):
        #    Texts.append((df["text"][i],int(df["label_Purpose"][i]),int(df["label_Right"][i]),int(df["label_Identity"][i]),int(df["label_Receiver"][i]),int(df["label_Legalbasis"][i]),int(df["label_Storage"][i])))
        return Texts

    def readNERText(self, path):
        lines = []
        with open(path,'r') as f:
            words = []
            labels = [] 
            for line in f:
                if line.startswith("-DOCSTART-") or line == "" or line == "\n":
                    if words:
                        lines.append({"words":words,"labels":labels})
                        words = []
                        labels = []
                else:
                    splits = line.split(" ")
                    words.append(splits[0])
                    if len(splits) > 1:
                        labels.append(splits[-1].replace("\n", ""))
                    else:
                        labels.append("O")
            if words:
                lines.append({"words":words,"labels":labels})
        return lines

    def create_examples(self, lines):
        """
        Creates examples for the training and dev sets.
        """
        examples = []
        for line in lines:
            if len(line) > 2:
                examples.append(InputExample(text_a=line[0], label=[line[1],line[2],line[3],line[4],line[5],line[6]]))
            else:
                examples.append(InputExample(text_a=line[0], label=line[1]))
        return examples

    def create_NERexamples(self, lines, set_type):
        examples = []
        for (i, line) in enumerate(lines):
            text_a= line['words']
            labels = line['labels']
            examples.append(InputExample(text_a=text_a, label=labels))
        return examples

    def load_data(self):
        tokenizer = BertTokenizer.from_pretrained(self.config.bert_path, do_lower_case=self.config.do_lower_case)
        features = convert_examples_to_features(examples=self.examples,max_seq_length=self.config.max_seq_length,tokenizer=tokenizer)
        all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        all_input_mask = torch.tensor([f.input_mask for f in features], dtype=torch.long)
        all_segment_ids = torch.tensor([f.segment_ids for f in features], dtype=torch.long)
        all_label_ids = torch.tensor([f.label_ids for f in features], dtype=torch.long)
        
        all_lens = torch.tensor([f.input_len for f in features], dtype=torch.long)
        allTexts = [f.input_text for f in features]
        dataset = TensorDataset(all_input_ids, all_input_mask, all_segment_ids, all_lens, all_label_ids)
        return dataset, allTexts
    
    def load_NERdata(self):
        tokenizer = BertTokenizerFast.from_pretrained(self.NERconfig.bert_path, do_lower_case=self.NERconfig.do_lower_case)
        features = convert_NERexamples_to_features(examples=self.examples,
                                            tokenizer=tokenizer,
                                            label_list=self.NERconfig.labels,
                                            pos_list=self.NERconfig.pos,
                                            max_seq_length=self.NERconfig.max_seq_length
                                            )
        all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        all_input_mask = torch.tensor([f.input_mask for f in features], dtype=torch.long)
        all_segment_ids = torch.tensor([f.segment_ids for f in features], dtype=torch.long)
        all_label_ids = torch.tensor([f.label_ids for f in features], dtype=torch.long)
        all_pos_ids = torch.tensor([f.pos_ids for f in features], dtype=torch.long)
        all_lens = torch.tensor([f.input_len for f in features], dtype=torch.long)
        allTexts = [f.input_text for f in features]
        allTokens = [f.tokens for f in features]
        dataset = TensorDataset(all_input_ids, all_input_mask, all_segment_ids, all_lens, all_label_ids, all_pos_ids)
        return dataset, allTexts, allTokens

