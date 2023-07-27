import torch
import json
import torch.nn as nn
import numpy as np
from torch.utils.data.distributed import DistributedSampler
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from Model.tools.ProgressBar import ProgressBar
from Model.metric.NERmetric import EntityMetric


def collate_fn(batch):
    all_input_ids, all_attention_mask, all_token_type_ids, all_lens, all_labels, all_pos = map(torch.stack, zip(*batch))
    max_len = max(all_lens).item()
    all_input_ids = all_input_ids[:, :max_len]
    all_attention_mask = all_attention_mask[:, :max_len]
    all_token_type_ids = all_token_type_ids[:, :max_len]
    all_labels = all_labels[:,:max_len]
    all_pos_ids = all_pos[:,:max_len]

    return all_input_ids, all_attention_mask, all_token_type_ids, all_labels, all_lens, all_pos_ids


def NERtest(config, model, test_data, testTexts, tokens, output_path = None):
    all_ret = []
    metric = EntityMetric(config.id2label)
    test_sampler = SequentialSampler(test_data) if config.local_rank == -1 else DistributedSampler(test_data)
    test_dataloader = DataLoader(test_data, sampler=test_sampler, batch_size=config.test_batch_size,
                                 collate_fn=collate_fn)
    pbar = ProgressBar(n_total=len(test_dataloader), desc="test")
    eval_loss = 0
    predict_all = np.array([], dtype=int)
    for step, batch in enumerate(test_dataloader):
        model.eval()
        with torch.no_grad():
            batch = tuple(t.to(config.device) for t in batch)
            inputs = {"input_ids": batch[0], "attention_mask": batch[1], "token_type_ids" : batch[2], "labels" : batch[3]}
            outputs = model(**inputs)
            tmp_eval_loss, logits = outputs[:2]
            # tags = model.crf.viterbi_decode(logits,batch[1])
            tags = model.crf.decode(logits)
            # eval_loss += tmp_eval_loss.item()
            out_label_ids = inputs['labels'].cpu().numpy().tolist()
            input_lens = batch[4].cpu().numpy().tolist()

        for i, label in enumerate(out_label_ids):
            temp_1 = []
            temp_2 = []
            for j, m in enumerate(label):
                if j == 0:
                    continue
                elif j == input_lens[i] - 1:
                    metric.update(pred=temp_2, label=temp_1, tokens = tokens[step*config.test_batch_size+i])
                    ret = metric.output_dict(testTexts[step*config.test_batch_size+i])
                    break
                else:
                    temp_1.append(config.id2label[out_label_ids[i][j]])
                    temp_2.append(config.id2label[tags[i][j]]) 
            all_ret.append(ret)
        pbar(step)
    if output_path is None:
        output_path = config.testoutputpath
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in all_ret:
            if len(record['error']) == 0:
                record.pop('error')
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
