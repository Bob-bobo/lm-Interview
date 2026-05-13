import math

import torch
import torch.nn as nn
from modelscope.models.cv.language_guided_video_summarization.transformer.sub_layers import PositionwiseFeedForward
from modelscope.models.cv.table_recognition.modules.lore_processor import MultiHeadAttention


class EncoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, drop_out):
        self.self_attn = MultiHeadAttention()
        self.feed_forword = PositionwiseFeedForward()
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(drop_out)

    def forward(self, x, mask):
        attn_output = self.self_attn(x, x, x, mask=mask)
        x = self.norm1(x + self.dropout(attn_output))

        ff_output = self.feed_forword(x)
        x = self.norm2(x + self.dropout(ff_output))

        return x


class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super(MultiHeadAttention, self).__init__()
        assert d_model % num_heads == 0, "d_model 必须能被num_heads整除"

        self.d_model = d_model
        self.num_heads = num_heads
        self.num_dims = d_model // num_heads

        # 定义Q、K、V
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def scaled_dot_product_attention(self, Q, K, V, mask=None):
        # 1、计算得分
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.num_dims)

        # 2、应用掩码
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)

        # 3、计算注意力权重
        attn_probs = torch.softmax(attn_scores, dim=-1)

        # 4、加权求和
        output = torch.matmul(attn_probs, V)
        return output

    def split_heads(self, x):
        batch_size, seq_length, d_model = x.size()
        return x.view(batch_size, seq_length, self.num_heads, self.head_dims).transpose(1, 2)

    def combine_heads(self, x):
        batch_size, num_heads, seq_length, head_dims = x.size()
        return x.transpose(1, 2).contiguous().view(batch_size, seq_length, self.num_dims)

    def forward(self, Q, K, V, mask=None):
        Q = self.split_heads(self.W_q(Q))
        K = self.split_heads(self.W_k(K))
        V = self.split_heads(self.W_v(V))

        attn_output = self.scaled_dot_product_attention(Q, K, V, mask)

        output = self.W_o(self.combine_heads(attn_output))
        return output

class PositionWiseFeedForward(nn.Module):
    def __init__(self, d_model, d_ff, dropout=0.1):
        super(PositionWiseFeedForward, self).__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.linear1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.linear2(x)
        return x


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))

        pe = torch.zeros(max_len, d_model)

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)