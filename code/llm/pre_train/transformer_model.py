import torch
from torch import nn

from transformer_norm import LayerNorm
from transformer_block import TransformerBlock


class TransformerModel(nn.Module):
    """
    Description: 
    Author: Administrator
    Date: 2026/3/4
    """
    def __init__(self, cfg):
        super().__init__()
        self.tok_emb = nn.Embedding(cfg['vocab_size'], cfg['emb_dim'])
        self.pos_emb = nn.Embedding(cfg['ctx_len'], cfg['emb_dim'])
        self.drop_emb = nn.Dropout(cfg['dropout'])

        self.transformer_block = nn.Sequential(
            *[TransformerBlock(cfg) for _ in range(cfg['num_layers'])]
        )

        self.final_norm = LayerNorm(cfg['emb_dim'])
        self.out_head = nn.Linear(cfg['emb_dim'], cfg['vocab_size'], bias=False)

    def forward(self, in_idx):
        _, seq_len = in_idx.shape
        tok_embeds = self.tok_emb(in_idx)
        pos_embeds = self.pos_emb(torch.arange(seq_len, device=in_idx.device))
        x = tok_embeds + pos_embeds
        x = self.transformer_block(x)
        x = self.final_norm(x)
        logits = self.out_head(x)
        return logits