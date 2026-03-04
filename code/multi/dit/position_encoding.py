import torch
from torch import nn


class PositionEncoding(nn.Module):
    """
    Description: 网络结构的位置编码信息
    Author: Administrator
    Date: 2026/3/3
    """
    def __init__(self, max_seq_len: int, d_model: int):
        super().__init__()
        assert d_model % 2 == 0

        pe = torch.zeros(max_seq_len, d_model)
        i_seq = torch.linspace(0, max_seq_len - 1, max_seq_len)
        # 这里将d_model数据折半，因为一半为sin数据一半为cos
        j_seq = torch.linspace(0, d_model - 2, d_model // 2)
        # 将i和j两个一维数据，转换为两个二维网络矩阵，这两个矩阵行为i的长度，列为j的长度
        pos, two_i = torch.meshgrid(i_seq, j_seq)
        pe_2i = torch.sin(pos / 10000 ** (two_i / d_model))
        pe_2j = torch.cos(pos / 10000 ** (two_i / d_model))
        pe = torch.stack((pe_2i, pe_2j), dim=-1).reshape(max_seq_len, d_model)

        self.embedding = nn.Embedding(max_seq_len, d_model)
        self.embedding.weight.data.copy_(pe)
        self.embedding.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.embedding(x)