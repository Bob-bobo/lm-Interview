import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import matplotlib.pyplot as plt

# ==================== 设备配置 ====================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"使用设备: {device}")

# ==================== 超参数 ====================
BATCH_SIZE = 128
EPOCHS = 20
LEARNING_RATE = 1e-3
LATENT_DIM = 20       # 隐变量维度 z 的维数
HIDDEN_DIM = 400      # 隐藏层维度
IMG_CHANNELS = 1      # 输入图像通道数（MNIST 灰度图）
IMG_SIZE = 28         # 输入图像尺寸


# ================================================================
#                        模型定义
# ================================================================

class Encoder(nn.Module):
    """
    编码器：将输入图像 x 映射到隐空间分布的参数 (μ, log_σ²)

    输入: x ∈ R^(1×28×28)        （展平后为 784 维向量）
    输出: μ ∈ R^latent_dim,  log_var ∈ R^latent_dim
    """

    def __init__(self, input_dim=784, hidden_dim=400, latent_dim=20):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc_mu = nn.Linear(hidden_dim, latent_dim)       # 均值 μ
        self.fc_log_var = nn.Linear(hidden_dim, latent_dim)   # 对数方差 log(σ²)

    def forward(self, x):
        # x: (batch, 1, 28, 28) -> flatten -> (batch, 784)
        h = F.relu(self.fc1(x))
        mu = self.fc_mu(h)              # 均值，无约束
        log_var = self.fc_log_var(h)     # 对数方差，无约束
        return mu, log_var


class Decoder(nn.Module):
    """
    解码器：从隐变量 z 重构原始输入 x̂

    输入: z ∈ R^latent_dim
    输出: x̂ ∈ R^(1×28×28)
    """

    def __init__(self, latent_dim=20, hidden_dim=400, output_dim=784):
        super().__init__()
        self.fc1 = nn.Linear(latent_dim, hidden_dim)
        self.fc_out = nn.Linear(hidden_dim, output_dim)

    def forward(self, z):
        h = F.relu(self.fc1(z))
        # 使用 sigmoid 将输出映射到 [0,1]，匹配图像像素值范围
        x_recon = torch.sigmoid(self.fc_out(h))
        return x_recon


class VAE(nn.Module):
    """
    变分自编码器

    VAE 的关键在于「重参数化技巧」(Reparameterization Trick)：
      采样 z ~ q(z|x) = N(μ, σ²) 本身是不可微的，
      所以我们改用：
        ε ~ N(0, I)
        z = μ + σ ⊙ ε
      这样梯度可以通过 μ 和 σ 反向传播。
    """

    def __init__(self, input_dim=784, hidden_dim=400, latent_dim=20):
        super().__init__()
        self.encoder = Encoder(input_dim, hidden_dim, latent_dim)
        self.decoder = Decoder(latent_dim, hidden_dim, output_dim=input_dim)

    def reparameterize(self, mu, log_var):
        """
        重参数化技巧：让采样操作可微

        参数:
            mu:       均值，形状 (batch, latent_dim)
            log_var:  对数方差 log(σ²)，形状 (batch, latent_dim)

        返回:
            z:        采样的隐变量，形状 (batch, latent_dim)

        数学推导:
            σ = exp(0.5 * log_var)
            ε ~ N(0, 1)
            z = μ + σ * ε
        """
        std = torch.exp(0.5 * log_var)         # σ = exp(log_var / 2)
        eps = torch.randn_like(std)              # ε ~ N(0, I)
        z = mu + std * eps                       # z = μ + σε
        return z

    def forward(self, x):
        """
        前向传播：编码 -> 重参数化 -> 解码

        返回:
            x_recon:  重构图像
            mu:       编码器输出的均值
            log_var:  编码器输出的对数方差
        """
        mu, log_var = self.encoder(x)
        z = self.reparameterize(mu, log_var)   # 关键步骤！
        x_recon = self.decoder(z)
        return x_recon, mu, log_var

    def sample(self, num_samples, device=device):
        """
        从先验分布 p(z)=N(0,I) 采样，生成新图像（推理/生成阶段）

        这就是 VAE 作为生成模型的强大之处：
        训练好的 VAE 隐空间具有良好结构，直接从 N(0,I) 采样 z，
        通过解码器就能生成有意义的图像。
        """
        z = torch.randn(num_samples, LATENT_DIM).to(device)
        samples = self.decoder(z)
        return samples

    def reconstruct(self, x):
        """
        重构输入图像（编码后再解码）

        用于比较输入与重构结果的差异。
        """
        with torch.no_grad():
            mu, log_var = self.encoder(x)
            z = self.reparameterize(mu, log_var)
            x_recon = self.decoder(z)
        return x_recon


# ================================================================
#                        损失函数
# ================================================================

def vae_loss(x_recon, x, mu, log_var):
    """
    VAE 的损失函数 = 重构损失 + KL 散度

    这本质上就是在最大化证据下界(ELBO)：
        ELBO = E_q[log p(x|z)] - KL(q(z|x) || p(z))

    参数:
        x_recon:  重构图像，形状 (batch, 784)
        x:        原始图像，形状 (batch, 784)
        mu:       均值，形状 (batch, latent_dim)
        log_var:  对数方差，形状 (batch, latent_dim)

    返回:
        total_loss:  总损失（标量）
        recon_loss:  重构损失（用于监控）
        kl_loss:     KL散度（用于监控）
    """

    # ---- 1. 重构损失 (Reconstruction Loss) ----
    # 假设 p(x|z) 是伯努利分布，使用二元交叉熵
    # BCE = -Σ [x_i * log(x̂_i) + (1-x_i) * log(1-x̂_i)]
    recon_loss = F.binary_cross_entropy(x_recon, x, reduction='sum')

    # ---- 2. KL 散度 (KL Divergence) ----
    # KL(q(z|x) || p(z))，其中 q=N(μ,σ²), p=N(0,I)
    # 解析解: KL = -0.5 * Σ (1 + log(σ²) - μ² - σ²)
    #        即:    -0.5 * Σ (1 + log_var - mu² - exp(log_var))
    kl_loss = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())

    total_loss = recon_loss + kl_loss
    return total_loss, recon_loss, kl_loss


# ================================================================
#                        数据加载
# ================================================================

def get_dataloader(batch_size=128):
    """加载 MNIST 数据集"""
    transform = transforms.Compose([
        transforms.ToTensor(),  # 转为 [0,1] 范围的张量
    ])

    train_dataset = datasets.MNIST(
        root='./data', train=True, download=True, transform=transform
    )
    test_dataset = datasets.MNIST(
        root='./data', train=False, download=True, transform=transform
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader


# ================================================================
#                        训练循环
# ================================================================

def train(model, train_loader, optimizer, epoch):
    """训练一个 epoch"""
    model.train()
    train_loss = 0
    train_recon = 0
    train_kl = 0
    num_batches = 0

    for batch_idx, (data, _) in enumerate(train_loader):
        data = data.to(device)
        # 展平图像: (batch, 1, 28, 28) -> (batch, 784)
        data = data.view(data.size(0), -1)

        optimizer.zero_grad()

        # 前向传播
        x_recon, mu, log_var = model(data)

        # 计算损失
        loss, recon, kl = vae_loss(x_recon, data, mu, log_var)

        # 反向传播
        loss.backward()
        optimizer.step()

        # 累计统计
        train_loss += loss.item()
        train_recon += recon.item()
        train_kl += kl.item()
        num_batches += 1

    avg_loss = train_loss / len(train_loader.dataset)
    avg_recon = train_recon / len(train_loader.dataset)
    avg_kl = train_kl / len(train_loader.dataset)

    print(f"  [训练] Epoch {epoch:3d} | "
          f"总损失: {avg_loss:.4f} | "
          f"重构损失: {avg_recon:.4f} | "
          f"KL散度: {avg_kl:.4f}")

    return avg_loss, avg_recon, avg_kl


def evaluate(model, test_loader):
    """在测试集上评估"""
    model.eval()
    test_loss = 0

    with torch.no_grad():
        for data, _ in test_loader:
            data = data.to(device)
            data = data.view(data.size(0), -1)

            x_recon, mu, log_var = model(data)
            loss, _, _ = vae_loss(x_recon, data, mu, log_var)
            test_loss += loss.item()

    avg_loss = test_loss / len(test_loader.dataset)
    print(f"  [测试]         测试损失: {avg_loss:.4f}")
    return avg_loss


# ================================================================
#                        可视化函数
# ================================================================

def visualize_reconstruction(model, test_loader, num_images=8, save_path="reconstruction.png"):
    """
    可视化重构效果：上排是原始图像，下排是重构图像
    """
    model.eval()
    with torch.no_grad():
        # 取一个 batch
        data, labels = next(iter(test_loader))
        data = data.to(device).view(data.size(0), -1)

        # 重构
        x_recon = model.reconstruct(data)

        # 转为图像格式
        originals = data.view(-1, 1, IMG_SIZE, IMG_SIZE).cpu()
        reconstructions = x_recon.view(-1, 1, IMG_SIZE, IMG_SIZE).cpu()

        # 绘图
        fig, axes = plt.subplots(2, num_images, figsize=(num_images * 1.5, 3))
        fig.suptitle("VAE 重构效果\n上排: 原始图像 | 下排: 重构图像", fontsize=13)

        for i in range(num_images):
            axes[0, i].imshow(originals[i].squeeze(), cmap='gray')
            axes[0, i].axis('off')
            axes[1, i].imshow(reconstructions[i].squeeze(), cmap='gray')
            axes[1, i].axis('off')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  📷 重构对比图已保存: {save_path}")


def visualize_generation(model, num_images=64, save_path="generation.png"):
    """
    从先验分布 N(0,I) 采样并生成新图像
    """
    model.eval()
    with torch.no_grad():
        samples = model.sample(num_images).cpu()
        samples = samples.view(-1, 1, IMG_SIZE, IMG_SIZE)

        # 排列为 8×8 网格
        fig, axes = plt.subplots(8, 8, figsize=(8, 8))
        fig.suptitle("VAE 生成的新图像（从 N(0,I) 采样）", fontsize=13)

        for i in range(8):
            for j in range(8):
                idx = i * 8 + j
                axes[i, j].imshow(samples[idx].squeeze(), cmap='gray')
                axes[i, j].axis('off')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  📷 生成图像已保存: {save_path}")


def visualize_latent_space(model, test_loader, save_path="latent_space.png"):
    """
    可视化隐空间分布（使用 t-SNE 降维到 2D）
    """
    model.eval()
    all_z = []
    all_labels = []

    with torch.no_grad():
        for data, labels in test_loader:
            data = data.to(device).view(data.size(0), -1)
            mu, log_var = model.encoder(data)
            z = model.reparameterize(mu, log_var)
            all_z.append(z.cpu().numpy())
            all_labels.append(labels.numpy())

    all_z = torch.cat([torch.tensor(z) for z in all_z]).numpy()
    all_labels = torch.cat([torch.tensor(l) for l in all_labels]).numpy()

    # 如果隐维度 > 2，使用 t-SNE 降维
    if LATENT_DIM > 2:
        try:
            from sklearn.manifold import TSNE
            print("  🔬 使用 t-SNE 将隐空间降维到 2D...")
            tsne = TSNE(n_components=2, random_state=42, perplexity=30)
            z_2d = tsne.fit_transform(all_z[:5000])  # 取前5000个点加速
            labels_2d = all_labels[:5000]
        except ImportError:
            print("  ⚠️  未安装 sklearn，使用前两个隐维度代替")
            z_2d = all_z[:, :2]
            labels_2d = all_labels
    else:
        z_2d = all_z
        labels_2d = all_labels

    # 绘制散点图
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(z_2d[:, 0], z_2d[:, 1], c=labels_2d, cmap='tab10',
                          s=2, alpha=0.6)
    plt.colorbar(scatter, label='数字类别')
    plt.title(f"VAE 隐空间分布（{'t-SNE' if LATENT_DIM > 2 else 'z₁-z₂'}）", fontsize=13)
    plt.xlabel("维度 1")
    plt.ylabel("维度 2")
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📷 隐空间分布图已保存: {save_path}")


def visualize_interpolation(model, test_loader, save_path="interpolation.png"):
    """
    在隐空间中做线性插值，展示 VAE 隐空间的连续性
    """
    model.eval()
    with torch.no_grad():
        # 取两张不同数字的图片
        data, labels = next(iter(test_loader))
        data = data.to(device).view(data.size(0), -1)

        # 找两个不同数字
        idx1, idx2 = 0, 0
        for i in range(len(labels)):
            if labels[i] == 1:
                idx1 = i
                break
        for i in range(len(labels)):
            if labels[i] == 7:
                idx2 = i
                break

        x1 = data[idx1:idx1+1]
        x2 = data[idx2:idx2+1]

        # 编码到隐空间
        mu1, _ = model.encoder(x1)
        mu2, _ = model.encoder(x2)

        # 线性插值
        num_steps = 10
        interpolations = []
        for alpha in torch.linspace(0, 1, num_steps):
            z = (1 - alpha) * mu1 + alpha * mu2
            x_interp = model.decoder(z)
            interpolations.append(x_interp.view(1, IMG_SIZE, IMG_SIZE).cpu())

        # 绘图
        fig, axes = plt.subplots(1, num_steps, figsize=(num_steps * 1.5, 1.5))
        fig.suptitle(f"隐空间插值: 数字 {labels[idx1]} → 数字 {labels[idx2]}",
                     fontsize=13)

        for i, img in enumerate(interpolations):
            axes[i].imshow(img.squeeze(), cmap='gray')
            axes[i].axis('off')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  📷 隐空间插值图已保存: {save_path}")


# ================================================================
#                        绘制训练曲线
# ================================================================

def plot_training_curves(history, save_path="training_curves.png"):
    """绘制训练过程中的损失曲线"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    epochs = range(1, len(history['total_loss']) + 1)

    axes[0].plot(epochs, history['total_loss'], 'b-', linewidth=2)
    axes[0].set_title("总损失", fontsize=12)
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, history['recon_loss'], 'r-', linewidth=2)
    axes[1].set_title("重构损失", fontsize=12)
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Loss")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(epochs, history['kl_loss'], 'g-', linewidth=2)
    axes[2].set_title("KL 散度", fontsize=12)
    axes[2].set_xlabel("Epoch")
    axes[2].set_ylabel("Loss")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📷 训练曲线已保存: {save_path}")


# ================================================================
#                        主函数
# ================================================================

def main():
    print("=" * 60)
    print("  变分自编码器 (VAE) 训练与推理演示")
    print("=" * 60)
    print()

    # ---- 1. 加载数据 ----
    print("📦 加载 MNIST 数据集...")
    train_loader, test_loader = get_dataloader(BATCH_SIZE)
    print(f"  训练集: {len(train_loader.dataset)} 张图像")
    print(f"  测试集: {len(test_loader.dataset)} 张图像")
    print()

    # ---- 2. 创建模型 ----
    print("🏗️  创建 VAE 模型...")
    model = VAE(
        input_dim=IMG_CHANNELS * IMG_SIZE * IMG_SIZE,  # 784
        hidden_dim=HIDDEN_DIM,
        latent_dim=LATENT_DIM
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"  模型参数量: {total_params:,}")
    print(f"  隐变量维度: {LATENT_DIM}")
    print(f"  隐藏层维度: {HIDDEN_DIM}")
    print()

    # ---- 3. 优化器 ----
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # ---- 4. 训练 ----
    print("🚀 开始训练...")
    print("-" * 60)
    history = {'total_loss': [], 'recon_loss': [], 'kl_loss': []}

    for epoch in range(1, EPOCHS + 1):
        total, recon, kl = train(model, train_loader, optimizer, epoch)
        history['total_loss'].append(total)
        history['recon_loss'].append(recon)
        history['kl_loss'].append(kl)

        # 每 5 个 epoch 做一次测试评估
        if epoch % 5 == 0 or epoch == EPOCHS:
            evaluate(model, test_loader)

    print("-" * 60)
    print("✅ 训练完成！")
    print()

    # ---- 5. 保存模型 ----
    model_path = "vae_mnist.pth"
    torch.save(model.state_dict(), model_path)
    print(f"💾 模型已保存: {model_path}")
    print()

    # ---- 6. 可视化结果 ----
    print("📊 生成可视化结果...")
    print()

    # 6.1 训练曲线
    print("📈 [1/4] 绘制训练曲线...")
    plot_training_curves(history, "training_curves.png")

    # 6.2 重构效果
    print("🔄 [2/4] 可视化重构效果...")
    visualize_reconstruction(model, test_loader, num_images=8)

    # 6.3 生成新图像
    print("🎨 [3/4] 从隐空间采样生成新图像...")
    visualize_generation(model, num_images=64)

    # 6.4 隐空间插值
    print("🔀 [4/4] 隐空间插值...")
    visualize_interpolation(model, test_loader)

    # 6.5 隐空间分布（可选，需要 sklearn）
    try:
        print("🔬 [5/5] 可视化隐空间分布...")
        visualize_latent_space(model, test_loader)
    except Exception as e:
        print(f"  ⚠️  跳过隐空间可视化: {e}")

    print()
    print("=" * 60)
    print("  全部完成！生成的图片文件：")
    print("    - training_curves.png  (训练损失曲线)")
    print("    - reconstruction.png    (重构效果对比)")
    print("    - generation.png        (随机生成图像)")
    print("    - interpolation.png     (隐空间插值)")
    print("    - latent_space.png      (隐空间分布)")
    print("=" * 60)


if __name__ == "__main__":
    main()