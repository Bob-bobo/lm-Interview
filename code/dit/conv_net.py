import torch
from torch import nn

from residual_block import residual_block
from position_encoding import position_encoding


def get_image_shape():
    return (3, 64, 64)

def build_network(config: dict, n_steps):
    network_type = config.pop('type')
    if network_type == 'ConvNet':
        network_cls = conv_net
    elif network_type == 'UNet':
        network_cls = unet
    else:
        raise ValueError(f'Unknown network type: {network_type}')

    network = network_cls(n_steps, **config)
    return network

class conv_net(nn.Module):
    """
    Description: Conv-Net网络结构
    Author: Administrator
    Date: 2026/3/3
    """
    def __init__(self, n_steps, intermediate_channels = [10, 20, 40],
                 pe_dim = 10, insert_t_to_all_layers = False):
        super().__init__()
        C, H, W = get_image_shape()
        self.pe = position_encoding(n_steps, pe_dim)
        self.pe_linear = nn.ModuleList()
        self.all_t = insert_t_to_all_layers
        # 是否需要给所有层插入位置信息，如果不需要则插入一层即可
        if not insert_t_to_all_layers:
            self.pe_linear.append(nn.Linear(pe_dim, C))

        self.residual_block = nn.ModuleList()
        pre_channel = C
        for channel in intermediate_channels:
            self.residual_block.append(residual_block(pre_channel, channel))
            if insert_t_to_all_layers:
                self.pe_linear.append(nn.Linear(pre_channel, channel))
            else:
                self.pe_linear.append(None)
            pre_channel = channel
        self.output_layer = nn.Conv2d(pre_channel, C, kernel_size=3, stride=1, padding=1)

    def forward(self, x: torch.Tensor, t) -> torch.Tensor:
        n = t.shape[0]
        t = self.pe(t)
        for m_x, m_t in zip(self.residual_block, self.pe_linear):
            if m_t is not None:
                pe = m_t(t).reshape(n, -1, 1, 1)
                x = x + pe
            x = m_x(x)
        x = self.output_layer(x)
        return x


class unet(nn.Module):
    def __init__(self, n_steps, channels=[10, 20, 40, 80],
                 pe_dim = 10, residual = False) -> None:
        super().__init__()
        C, H, W = get_image_shape()
        layers = len(channels)
        Hs, Ws = [H], [W]
        cH, cW = H, W
        # 提前预判每层特征图尺寸，默认按照步长2的长度做下采样和上采样
        for _ in range(layers - 1):
            cH //= 2
            cW //= 2
            Hs.append(cH)
            Ws.append(cW)

        self.pe = position_encoding(n_steps, pe_dim)
        self.encoder = nn.ModuleList()
        self.decoder = nn.ModuleList()
        self.pe_linear_en = nn.ModuleList()
        self.pe_linear_de = nn.ModuleList()
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        prev_channel = C
        # 下采样，通道最后维度不使用
        for channel, cH, cW in zip(channels[0:-1], Hs[0:-1], Ws[0:-1]):
            self.pe_linear_en.append(
                nn.Sequential(nn.Linear(pe_dim, prev_channel),
                              nn.ReLU(),
                              nn.Linear(prev_channel, prev_channel),
                            ))
            self.encoder.append(nn.Sequential(
                unet_block((prev_channel, cH, cW),
                           prev_channel,
                           channel,
                           residual=residual),
                unet_block((channel, cH, cW),
                           channel,
                           channel,
                           residual=residual)
            ))
            self.downs.append(nn.Conv2d(channel, channel, kernel_size=2, stride=2))
            prev_channel = channel
        # 中间层，即不是上采样也不是下采样的通道层，所以单独拎出来写
        self.pe_mid = nn.Linear(pe_dim, prev_channel)
        channel = channels[-1]
        self.mid = nn.Sequential(
            unet_block((prev_channel, Hs[-1], Ws[-1]),
                       prev_channel,
                       channel,
                       residual=residual),
            unet_block((channel, Hs[-1], Ws[-1]),
                       channel,
                       channel,
                       residual=residual)
        )
        prev_channel = channel
        # 上采样
        for channel, cH, cW in zip(channels[-2::-1], Hs[-2::-1], Ws[-2::-1]):
            self.pe_linear_de.append(nn.Linear(pe_dim, prev_channel))
            self.ups.append(nn.ConvTranspose2d(prev_channel, channel, kernel_size=2, stride=2))
            self.decoder.append(nn.Sequential(
                unet_block((channel * 2, cH, cW),
                           channel * 2,
                           channel,
                           residual=residual),
                unet_block((channel, cH, cW),
                           channel,
                           channel,
                           residual=residual)
            ))
            prev_channel = channel

        self.conv_out = nn.Conv2d(prev_channel, C, kernel_size=3, stride=1, padding=1)

    def forward(self, x: torch.Tensor, t) -> torch.Tensor:
        n = t.shape[0]
        t = self.pe(t)
        encoder_outs = []
        for pe_linear, encoder, down in zip(self.pe_linear_en, self.encoder, self.downs):
            pe = pe_linear(t).reshape(n, -1, 1, 1)
            x = encoder(x + pe)     # 输入和位置编码简单相加
            encoder_outs.append(x)
            x = down(x)
        pe = self.pe_mid(t).reshape(n, -1, 1, 1)
        x = self.mid(x + pe)
        for pe_linear, decoder, up, encoder_out in zip(self.pe_linear_de, self.decoder, self.ups, encoder_outs):
            pe = pe_linear(t).reshape(n, -1, 1, 1)
            x = up(x)
            # 下采样的值
            pad_x = encoder_out[2] - x.shape[2]
            pad_y = encoder_out[3] - x.shape[3]
            x = F.pad(x, (pad_x // 2, pad_x - pad_x // 2, pad_y // 2, pad_y - pad_y // 2))
            x = torch.cat((encoder_out, x), dim=1)
            x = decoder(x + pe)
        x = self.conv_out(x)
        return x

# unet网络结构block
class unet_block(nn.Module):
    def __init__(self, shape, in_c, out_c, residual = False) -> None:
        super().__init__()
        self.ln = nn.LayerNorm(shape)
        self.conv1 = nn.Conv2d(in_c, out_c, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(out_c, out_c, kernel_size=3, stride=1, padding=1)
        self.activation = nn.ReLU()
        self.residual = residual
        if residual:
            if in_c != out_c:
                self.residual_conv = nn.Identity()
            else:
                self.residual_conv = nn.Conv2d(in_c, out_c, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv2(self.activation(self.conv1(self.ln(x))))
        if self.residual:
            out += self.residual_conv(x)
        out = self.activation(out)
        return out