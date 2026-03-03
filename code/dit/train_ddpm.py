import torch
import torchvision
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision.transforms import Compose, ToTensor, Lambda

from conv_net import ConvNet, UNet
from get_image_loader import get_image_loader
from ddpm import DDPM

unet_cfg = {
        'type': 'UNet',
        'channels': [4, 8, 16, 32, 64],
        'pe_dim': 512,
        'residual': True
    }

def build_network(config: dict, n_steps):
    network_type = config.pop('type')
    if network_type == 'ConvNet':
        network_cls = ConvNet
    elif network_type == 'UNet':
        network_cls = UNet
    else:
        raise ValueError(f'Unknown network type: {network_type}')

    network = network_cls(n_steps, **config)
    return network


def get_dataloader(batch_size):
    transform = Compose([ToTensor(), Lambda(lambda x: (x - 0.5) * 2)])
    dataset = torchvision.datasets.MNIST(root='./data', train=True, transform=transform, download=True)
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)


def train(ddpm: DDPM, net, device, ckpt_path):
    batch_size = 512
    n_epochs = 100
    n_steps = ddpm.n_steps
    # 获取图片数据集
    #dataloader = get_image_loader("data/TINT", batch_size)
    # 获取手写字数据集
    dataloader = get_dataloader(batch_size)
    net = net.to(device)
    loss_fn = nn.MSELoss()
    optimizer = optim.AdamW(
        net.parameters(),
        lr = 3e-4,
        betas = (0.9, 0.999),
        weight_decay = 0.0005
    )

    for epoch in range(n_epochs):
        for batch, (x, _) in enumerate(dataloader):
            current_batch_size = x.shape[0]
            x = x.to(device)
            t = torch.randint(0, n_steps, (current_batch_size,), device = device)
            eps = torch.randn_like(x).to(device)
            x_t = ddpm.sample_forward(x, t, eps)
            eps_theta = net(x_t, t.reshape(current_batch_size, 1))
            loss = loss_fn(eps_theta, eps)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if batch % 100 == 0:
                print(f'Epoch [{epoch}/{n_epochs}], Step [{batch}/{n_steps}], Loss: {loss.item():.4f}')
    torch.save(net.state_dict(), ckpt_path)

def main():
    n_step = 1000
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_path = 'weights/ddpm_model.pth'

    config = unet_cfg
    net = build_network(config, n_step)
    ddpm = DDPM(device, n_step)

    train(ddpm, net, device, model_path)

if __name__ == '__main__':
    main()