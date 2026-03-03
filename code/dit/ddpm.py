import torch



class DDPM:
    def __init__(self, device, n_steps: int,
                 min_beta: float = 0.0001, max_beta: float = 0.02):
        # 马尔科夫链中的betas数据
        betas = torch.linspace(min_beta, max_beta, n_steps).to(device)
        alphas = 1.0 - betas
        alphas_bars = torch.empty_like(alphas)
        product = 1
        # 对betas反向数据alphas做乘积，获得乘积和数据
        for i, alpha in enumerate(alphas):
            product *= alpha
            alphas_bars[i] = product

        self.device = device
        self.n_steps = n_steps
        self.alphas = alphas
        self.betas = betas
        self.alphas_bars = alphas_bars

    def sample_forward(self, x, t, eps=None):
        """

        :param x: 输入的样本x
        :param t: 输入的加噪步数t，跳多少步
        :param eps: 要添加的噪音信息，如果为空，重新生成一个
        :return: 加噪后的图片信息
        """
        # 调整alpha现状
        alphas_bar = self.alphas_bars[t].reshape(-1, 1, 1, 1)
        if eps is None:
            eps = torch.randn_like(alphas_bar)
        res = eps * torch.sqrt(1 - alphas_bar) + torch.sqrt(alphas_bar) * x
        return res

    def sample_backward(self, image_shape, net, device, simple_var=True):
        """

        :param image_shape: 采样时的图片大小，三维信息
        :param net: 噪音预测的UNet网络
        :param device: 推理使用的设备
        :param simple_var:
        :return: 图像信息
        """
        x = torch.randn(image_shape).to(device)
        net = net.to(device)
        net.eval()
        # 这里从step-1到0步骤，做逐步去噪操作
        for t in range(self.n_steps - 1, -1, -1):
            x = self.sample_backward_step(x, t, net, simple_var)
        return x

    def sample_backward_step(self, x, t, net, simple_var):
        """

        :param x: 图像信息，第一次调用时完全是个符合高斯分布的噪音图像
        :param t: 去噪的步数，由steps-1缩减到0
        :param net: 去噪推理网络
        :param simple_var:
        :return:
        """
        n = x.shape[0]
        # 将步数填充到整个t_tensor
        t_tensor = torch.tensor([t] * n, dtype=torch.long).to(x.device).unsqueeze(1)
        eps = net(x, t_tensor)

        if t == 0:
            noise = 0
        else:
            # 如果使用简单的预测，直接获取方差信息var即可
            if simple_var:
                var = self.betas[t]
            else:
                # 这里使用的就是采样过程正规的方差信息
                var = (1 - self.alphas_bars[t - 1]) / (1 - self.alphas_bars[t]) * self.betas[t]
            noise = torch.randn_like(x)
            noise *= torch.sqrt(var)
        # 采样过程的均值数据，其中eps就是预测模型得到的结果
        mean = (x - (1 - self.alphas[t]) / torch.sqrt(1 - self.alphas[t]) * eps) / torch.sqrt(self.alphas[t])
        x = mean + noise
        return x