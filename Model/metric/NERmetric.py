import torch
from collections import Counter
import IPython

class EntityMetric(object):
    def __init__(self, id2label):
        self.id2label = id2label
        self.reset() 

    def reset(self):
        self.origins = []
        self.founds = []
        self.rights = []
        self.recalls = []
        ### Change
        self.flush_origins = []
        self.flush_founds = []
        self.flush_rights = []

    """ 
    def get_entities(self, seq, id2label, tokens):
        Gets entities from sequence.
        note: BIO
        Args:
            seq (list): sequence of labels.
        Returns:
            list: list of (chunk_type, chunk_start, chunk_end).
        Example:
            seq = ['B-PER', 'I-PER', 'O', 'B-LOC']
            get_entity_bio(seq)
            #output
            [['PER', 0,1], ['LOC', 3, 3]]
        
        chunks = []
        chunk = [-1, -1, -1]
        count = 0
        for index, tag in enumerate(seq):
            if not isinstance(tag, str):
                tag = id2label[tag]
            if index != len(seq) - 1 and tokens[index].startswith('##'):
                count = count + 1
                chunk[2] = index - count
            else:
                if tag.startswith("B-"):
                    if chunk[2] != -1:
                        chunks.append(chunk)
                    chunk = [-1, -1, -1]
                    chunk[1] = index - count
                    chunk[0] = tag.split('-')[1]
                    chunk[2] = index - count
                    if index == len(seq) - 1:
                        chunks.append(chunk)
                elif tag.startswith('I-') and chunk[1] != -1:
                    _type = tag.split('-')[1]
                    if _type == chunk[0]:
                        chunk[2] = index - count
                    if index == len(seq) - 1:
                        chunks.append(chunk)
                else:
                    if chunk[2] != -1:
                        chunks.append(chunk)
                    if index+1 <= len(seq) - 1 and tokens[index+1].startswith('##') and seq[index+1].startswith("B-"):
                        chunk[1] = index - count
                        chunk[0] = seq[index+1].split('-')[1]
                        chunk[2] = index - count
                    else:
                        chunk = [-1, -1, -1]
        return chunks
    """
    
    def get_entity_bio(self, seq, id2label, tokens):
        '''
        From sequence get entities
        Args:
            seq(list):sequence of labels
            id2label(dict):id to label mapping
            tokens(list):list of subwords after tokenization
        Output:
            list of entity(entity[0]:label_type,entity[1]:start_index,entity[2]:end_index)
        single_words:model may label meaningless single word as a complete label
        words:list of words before tokenization
        '''
        single_words = ['the','such','any','you','to','your','my','this','used','be','if','these','a','for','unless','after','so','their','can','i']
        words = [token for token in tokens if not token.startswith('##')]
        entities = []
        entity = [-1, -1, -1]
        single_indx = -1
        single_tag = ""
        for indx, tag in enumerate(seq):
            if not isinstance(tag, str):
                tag = id2label[tag]
            if tag.startswith("B-"):
                if entity[2] != -1 :
                    if entity[1] == entity[2] and words[entity[1]].lower() in single_words:
                        single_indx = entity[1]
                        single_tag = entity[0]
                    else:
                        if single_indx == entity[1]-1 and single_tag == entity[0]:
                            entity[1] = single_indx
                        entities.append(entity)
                entity = [-1, -1, -1]
                entity[1] = indx
                entity[0] = tag.split('-')[1]
                entity[2] = indx
                if indx == len(seq) - 1 and (entity[1] != entity[2] or words[entity[1]].lower() not in single_words):
                    if single_indx == entity[1]-1 and single_tag == entity[0]:
                        entity[1] = single_indx
                    entities.append(entity)
            elif tag.startswith('I-') and entity[1] != -1:
                label_type = tag.split('-')[1]
                if label_type == entity[0]:
                    entity[2] = indx

                if indx == len(seq) - 1 and (entity[1] != entity[2] or words[entity[1]].lower() not in single_words):
                    if single_indx == entity[1]-1 and single_tag == entity[0]:
                        entity[1] = single_indx
                    entities.append(entity)
            else:
                if entity[2] != -1 :
                    if entity[1] == entity[2] and words[entity[1]].lower() in single_words:
                        single_indx = entity[1]
                        single_tag = entity[0]
                    else:
                        if single_indx == entity[1]-1 and single_tag == entity[0]:
                            entity[1] = single_indx
                        entities.append(entity)
                entity = [-1, -1, -1]
        return entities

    def combine_subword_label(slef, seq, tokens):
        '''
        make subword labels consistent
        Args:
            seq(list):sequence of labels
            tokens(list):list of subwords after tokenization
        Output:
            seq(list):sequence of labels
        '''
        labels = []
        label = ''
        for index, token in enumerate(tokens):
            if tokens[index].startswith('##'):
                if (seq[index].startswith('B') or seq[index].startswith('I')) and label.startswith('O'):
                    label = seq[index]
            else:
                if label != '':
                    labels.append(label)
                label = seq[index]
            if index == len(seq) - 1:
                labels.append(label)
        return labels

    def compute(self, origin, found, right, recall):
        '''
        Compute Recall,Precision,F1
        '''
        recall_score = 0 if origin == 0 else (recall / origin)
        precision = 0 if found == 0 else (right / found)
        f1 = 0. if recall_score + precision == 0 else (2 * precision * recall_score) / (precision + recall_score)
        return recall_score, precision, f1

    def result(self):
        '''
        Compute Recall and Precision for each label_type
        '''
        class_info = {}
        origin_counter = Counter([x[0] for x in self.origins])
        found_counter = Counter([x[0] for x in self.founds])
        right_counter = Counter([x[0] for x in self.rights])
        recall_counter = Counter([x[0] for x in self.recalls])
        for label_type, count in origin_counter.items():    ## type is the type of each label, and count is the number of each label
            origin = count
            found = found_counter.get(label_type, 0)
            right = right_counter.get(label_type, 0)
            recall = recall_counter.get(label_type, 0)
            recall, precision, f1 = self.compute(origin, found, right, recall)
            class_info[label_type] = {"acc": round(precision, 4), 'recall': round(recall, 4), 'f1': round(f1, 4)}
        origin = len(self.origins)
        found = len(self.founds)
        right = len(self.rights)
        recall = len(self.recalls)
        recall, precision, f1 = self.compute(origin, found, right, recall)
        return {'acc': precision, 'recall': recall, 'f1': f1}, class_info
    
    def output_dict(self, text_a):
        """
        Output predict results,labels and the difference from the actual annotation
        Args:
            text_a: original text
        Output:
            ret_dict[text]: original text
            ret_dict[predict]: predict entity
            ret_dict[real]: actual annotation
            ret_dict[label]: predict entity index
            ret_dict[error]: difference from the actual annotation           
        """
        ret_dict = {}
        ret_dict['text'] = ''.join(text_a)
        words = ''.join(text_a).split(' ')
        ret_dict['predict'] = {}
        ret_dict['real'] = {}
        ret_dict['label'] = []
        ret_dict['error'] = []
        for i in self.flush_founds:
            if i[0] not in ret_dict['predict']: # if the label hasn't appear in this sentence
                ret_dict['predict'][i[0]] = [words[i[1]:i[2]+1]]
            else:
                ret_dict['predict'][i[0]].append(words[i[1]:i[2]+1])
            ret_dict['label'].append([i[1], i[2]+1, i[0]])
            hit = 0
            for j in self.flush_origins:
                if i[0] == j[0]:
                    if (i[1] <= j[1] and i[2] >= j[2]) or (i[1] >= j[1] and i[2] <= j[2]):
                        hit = 1
                    if i[0] == "Purpose" or i[0] == "Right":
                        if abs(i[1]-j[1]) < 3 and abs(i[2]-j[2]) < 3:
                            hit = 1
                    elif i[0] == "Receiver" or i[0] == "Storage":
                        if abs(i[1]-j[1]) < 2 and abs(i[2]-j[2]) < 2:
                            hit = 1
                    else:
                        if i[1] == j[1] and i[2] == j[2]:
                            hit = 1
            if hit != 1:
               ret_dict['error'].append([i[1], i[2]+1, i[0],words[i[1]:i[2]+1]]) 
        for i in self.flush_origins:
            if i[0] not in ret_dict['real']:
                ret_dict['real'][i[0]] = [words[i[1]:i[2]+1]]
            else:
                ret_dict['real'][i[0]].append(words[i[1]:i[2]+1])

        return ret_dict

    def compute_hit(self, pre_entities, label_entities):
        '''
        Determines whether the predicted label can match annotation 
        '''
        hit_entity = []
        recall_entity = []
        for pre_entity in pre_entities:
            for label_entity in label_entities:
                if pre_entity[0] == label_entity[0]:
                    if (pre_entity[1] >= label_entity[1] and pre_entity[2] <= label_entity[2]) or (pre_entity[1] <= label_entity[1] and pre_entity[2] >= label_entity[2]):
                        hit_entity.append(pre_entity)
                        if label_entity not in recall_entity:
                           recall_entity.append(label_entity) 
                        continue
                    if pre_entity[0] == "Purpose" or pre_entity[0] == "Right":
                        if abs(pre_entity[1]-label_entity[1]) < 3 and abs(pre_entity[2]-label_entity[2]) < 3:
                            hit_entity.append(pre_entity)
                            if label_entity not in recall_entity:
                                recall_entity.append(label_entity) 
                    elif pre_entity[0] == "Receiver" or pre_entity[0] == "Storage":
                        if abs(pre_entity[1]-label_entity[1]) < 2 and abs(pre_entity[2]-label_entity[2]) < 2:
                            hit_entity.append(pre_entity)
                            if label_entity not in recall_entity:
                                recall_entity.append(label_entity) 
                    else:
                        if pre_entity[1] == label_entity[1] and pre_entity[2] == label_entity[2]:
                            hit_entity.append(pre_entity)
                            if label_entity not in recall_entity:
                               recall_entity.append(label_entity) 
        return hit_entity,recall_entity 

    def update(self, label, pred, tokens):
        '''
        According to label and pred get hit_entity
        Args:
            label(list): predic label of BIO
            pred(list): annotation of BIO
            tokens(list): list of subwords after tokenization
        '''
        self.flush_origins = []
        self.flush_founds = []
        self.flush_rights = []
        #print("label_path",label)
        #print("pred_path",pred)
        #print("tokens",tokens)
        label = self.combine_subword_label(label, tokens)
        pred = self.combine_subword_label(pred, tokens)
        label_entities = self.get_entity_bio(label, self.id2label, tokens)
        pre_entities = self.get_entity_bio(pred, self.id2label, tokens)
        self.origins.extend(label_entities)
        self.founds.extend(pre_entities)
        hit_entities, recall_entities = self.compute_hit(pre_entities, label_entities)
        self.rights.extend(hit_entities)
        self.recalls.extend(recall_entities)
        self.flush_origins.extend(label_entities)
        self.flush_founds.extend(pre_entities)

    

      




