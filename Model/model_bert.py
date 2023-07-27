import torch.nn as nn
import torch.nn.functional as F
from transformers.models.bert.modeling_bert import *
from torch.nn.utils.rnn import pad_sequence
from torchcrf import CRF
import IPython

class Model(BertPreTrainedModel):

    def __init__(self, config):
        super(Model, self).__init__(config)      
        self.bert = BertModel(config)           
        for param in self.bert.parameters():
            param.requires_grad = True           
        self.fc = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, input_ids, attention_mask=None, token_type_ids=None,labels=None):
        out = self.bert(input_ids, attention_mask=attention_mask)
        pooled = out['pooler_output']
        out = self.fc(pooled)
        return out

class NERModel(BertPreTrainedModel):

    def __init__(self, config):
        super(NERModel, self).__init__(config)      
        self.bert = BertModel(config)           
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)
        self.crf = CRF(config.num_labels, batch_first=True)
        

    def forward(self, input_ids, token_type_ids=None, attention_mask=None,labels=None,pos_ids=None,):
        outputs =self.bert(input_ids = input_ids,attention_mask=attention_mask,token_type_ids=token_type_ids)
        sequence_output = outputs[0]
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)
        outputs = (logits,)
        if labels is not None:
            loss_mask = labels.gt(-1)
            loss = self.crf(logits, labels, attention_mask.byte()) * (-1)
            outputs = (loss,) + outputs
        return outputs # (loss), scores
    