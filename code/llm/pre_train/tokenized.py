import tiktoken
import torch
from torch.utils.data import Dataset, DataLoader


class Tokenized(Dataset):
    """
    Description: 
    Author: Administrator
    Date: 2026/3/4
    """
    def __init__(self, texts, tokenizer, max_length=512, stride=1):
        self.tokenizer = tokenizer
        self.inputs_ids = []
        self.targets_ids = []

        # 对文本进行分词
        token_ids = tokenizer.encode(texts, allowed_special={'<|endoftext|>'})

        # 使用滑动窗口将图书分块为最大长度的重叠序列
        for i in range(0, len(token_ids) - max_length, stride):
            input_chunk = token_ids[i:i + max_length]
            # 这里目标词段位输入词段的向右移动一位
            target_chunk = token_ids[i + 1: i + max_length + 1]
            self.inputs_ids.append(torch.tensor(input_chunk))
            self.targets_ids.append(torch.tensor(target_chunk))

    def __len__(self):
        return len(self.inputs_ids)

    def __getitem__(self, idx):
        return self.inputs_ids[idx], self.targets_ids[idx]

def create_dataloader(raw_text, batch_size=4, max_length=256, stride=128, shuffle=True, drop_last=True):
    # 2、使用已有的分词器直接使用即可
    tokenizer = tiktoken.get_encoding("gpt2")
    # 创建数据集
    dataset = Tokenized(raw_text, tokenizer, max_length=max_length, stride=stride)
    # 创建加载器
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last)
    return dataloader