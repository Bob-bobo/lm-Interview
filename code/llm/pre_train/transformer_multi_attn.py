import torch
from torch import nn


class TransformerMultiAttn(nn.Module):
    """
    Description: 
    Author: Administrator
    Date: 2026/3/4
    """
    def __init__(self, d_in, d_out, block_size, dropout, num_heads, qkv_bias=False):
        super().__init__()
        assert d_out % num_heads == 0

        self.d_out = d_out
        self.num_heads = num_heads
        self.head_dim = d_out // num_heads

        self.W_query = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.W_key = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.W_value = nn.Linear(d_in, d_out, bias=qkv_bias)
        self.out_proj = nn.Linear(d_out, d_out)
        self.dropout = nn.Dropout(p=dropout)
        self.register_buffer('mask', torch.triu(torch.ones(block_size, block_size), diagonal=1))

    def forward(self, x):
        batch, seq_len, _ = x.shape

        # 其中seq_dim为未多头拆分的词维度
        keys = self.W_query(x)
        values = self.W_value(x)
        queries = self.W_key(x)

        # 将其拆分为多头维度，num_head为头数，head_dim为每个头的维度
        keys = keys.view(batch, seq_len, self.num_heads, self.head_dim)
        values = values.view(batch, seq_len, self.num_heads, self.head_dim)
        queries = queries.view(batch, seq_len, self.num_heads, self.head_dim)

        # 转置：seq_len和为num_heads做交换，这样在计算时，可以确保在同一批次和同一头下
        keys = keys.transpose(1, 2)
        values = values.transpose(1, 2)
        queries = queries.transpose(1, 2)

        # 开始做注意力计算
        #atten_scores = queries @ keys.transpose(-2, -1)
        attn_scores = torch.matmul(queries, keys.transpose(-2, -1))
        # 将q和k相乘数据做掩码覆盖
        mask_bool = self.mask.bool()[:seq_len, :seq_len]
        mask_bool = mask_bool.unsqueeze(0).unsqueeze(0)
        attn_scores.masked_fill(mask_bool, float('-inf'))

        attn_weights = torch.softmax(attn_scores / keys.shape[-1] ** 0.5, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # 将num_heads和seq_len交换回最初状态
        context_vec = torch.matmul(attn_weights, values).transpose(1, 2)
        # 再将多个头计算的结果拼接起来
        context_vec = context_vec.contiguous().view(batch, seq_len, self.d_out)
        context_vec = self.out_proj(context_vec)

        return context_vec