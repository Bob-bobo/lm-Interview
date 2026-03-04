from torch import nn

from transformer_norm import LayerNorm
from transformer_multi_attn import TransformerMultiAttn
from transformer_ffn import TransformerFFN


class TransformerBlock(nn.Module):
    """
    Description: 
    Author: Administrator
    Date: 2026/3/4
    """
    def __init__(self, cfg):
        super().__init__()
        self.attn = TransformerMultiAttn(
            d_in = cfg["emb_dim"],
            d_out = cfg["emb_dim"],
            block_size = cfg["ctx_len"],
            num_heads = cfg["num_heads"],
            dropout = cfg["dropout"],
            qkv_bias = cfg["qkv_bias"],
        )
        self.ffn = TransformerFFN(cfg)
        self.norm1 = LayerNorm(cfg["emb_dim"])
        self.norm2 = LayerNorm(cfg["emb_dim"])
        self.drop_resid = nn.Dropout(cfg["dropout"])

    def forward(self, x):
        shortcut = x
        x = self.norm1(x)
        x = self.attn(x)
        x = self.drop_resid(x)
        x = x + shortcut    # 与原始输入块求和

        shortcut = x
        x = self.norm2(x)
        x = self.ffn(x)
        x = self.drop_resid(x)
        x = x + shortcut

        return x