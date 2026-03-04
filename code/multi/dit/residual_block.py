import torch
from torch import nn


class ResidualBlock(nn.Module):
    """
    Description: 构建残差块
    Author: Administrator
    Date: 2026/3/3
    """
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.conv1 = nn.Conv2d(input_dim, output_dim, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(output_dim)
        self.activation1 = nn.ReLU()
        self.conv2 = nn.Conv2d(output_dim, output_dim, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(output_dim)
        self.activation2 = nn.ReLU()
        # 如果输入输出的维度未对齐，通过1维卷积核，对齐维度即可
        if input_dim != output_dim:
            self.shortcut = nn.Sequential(
                nn.Conv2d(input_dim, output_dim, kernel_size=1),
                nn.BatchNorm2d(output_dim),
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, input: torch.Tensor) -> torch.Tensor:
        x = self.bn2(self.conv2(self.activation1(self.bn1(self.conv1(input)))))
        x += self.shortcut(input)
        x = self.activation2(x)
        return x