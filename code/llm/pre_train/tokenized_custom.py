"""
This module provides a custom tokenizer for demonstration purposes.
"""
import re


class Tokenized_Custom:
    """
    Description: 这个是自定义的分词器，效果不佳，仅靠简单的标点符号做分词，结果就是分词比较粗糙
    Author: Administrator
    Date: 2026/3/4
    """
    def __init__(self, vocab):
        self.str_to_int = vocab
        self.int_to_str = {i: s for s, i in vocab.items()}

    def encoder(self, text):
        """Encodes a string into a list of token IDs."""
        preprocessed = re.split(r'([,curl.?_!"()\']|--|\\s)', text)
        # 这里将空格去除
        preprocessed = [item.strip() for item in preprocessed if item.strip()]
        # 这里将词表中没有的词使用unk标识符替代
        preprocessed = [item if item in self.str_to_int else "<|unk|>" for item in preprocessed]
        # 将分词后的数据转换为int
        ids = [self.str_to_int[s] for s in preprocessed]
        return ids

    def decoder(self, ids):
        """Decodes a list of token IDs back into a string."""
        text = " ".join([self.int_to_str[token_id] for token_id in ids])
        text = re.sub(r'\\s+([,.?_!"()\'])', r'\\1', text)
        return text

def get_vocab(raw_text):
    """Extracts a vocabulary from the raw text."""
    vocab = re.split(r'([,.?_!"()\']|--|\\s)', raw_text)
    # 这里将空格去除
    vocab = [item.strip() for item in vocab if item.strip()]
    return vocab

def create_dataloader_custom():
    """Creates a dataloader for custom tokenization."""
    with open("data/the_tang.txt", encoding="utf-8") as f:
        raw_text = f.read()

    # 1、这是自定义的分词器，略显粗糙，权当学习基本概念
    all_vocabs = get_vocab(raw_text)
    vocabs_list = sorted(list(set(all_vocabs)))   # 对分词的token做排序和去重
    vocabs_list.extend(["<|endoftext|>", "<|unk|>"])
    
    # Create a dictionary mapping tokens to integers
    vocab_dict = {token: i for i, token in enumerate(vocabs_list)}

    tokenize_custom = Tokenized_Custom(vocab_dict)
    text = "you are so beautiful"
    ids = tokenize_custom.encoder(text)
    print("str_to_int: ", ids)
    text = tokenize_custom.decoder(ids)
    print("int_to_str: ", text)
