import torch
import torch.nn as nn
import numpy as np
from torch.utils.data.distributed import DistributedSampler
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from sklearn import metrics
from Model.tools.ProgressBar import ProgressBar
import os

def collate_fn(batch):
    all_input_ids, all_attention_mask, all_token_type_ids, all_lens, all_labels = map(torch.stack, zip(*batch))
    max_len = max(all_lens).item()
    all_input_ids = all_input_ids[:, :max_len]
    all_attention_mask = all_attention_mask[:, :max_len]
    all_token_type_ids = all_token_type_ids[:, :max_len]
    all_labels = all_labels[:]

    return all_input_ids, all_attention_mask, all_token_type_ids, all_labels

def test(config, model, test_data, testTexts, output_path = None):
    test_sampler = SequentialSampler(test_data) if config.local_rank == -1 else DistributedSampler(test_data)
    test_dataloader = DataLoader(test_data, sampler=test_sampler, batch_size=config.test_batch_size,collate_fn=collate_fn)
    pbar = ProgressBar(n_total=len(test_dataloader), desc="test")
    predict_all = np.array([], dtype=int)
    for step, batch in enumerate(test_dataloader):
        model.eval()
        with torch.no_grad():
            batch = tuple(t.to(config.device) for t in batch)
            inputs = {"input_ids": batch[0], "attention_mask": batch[1]}
            labels = batch[3]
            outputs = model(**inputs)
            predic = torch.max(outputs.data, 1)[1].cpu().numpy()
            predict_all = np.append(predict_all, predic)
        pbar(step)
    if output_path is None:
        output_path = config.testoutputpath
    with open(output_path, 'w', encoding='utf-8') as f:
        for t in zip(testTexts, predict_all):
            f.write(t[0] + ',' + str(t[1]) + '\n')
