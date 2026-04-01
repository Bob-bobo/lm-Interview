import torch
import torch.nn as nn

# Tensor的基本用法
def tensor_use():
    x = torch.empty(5, 3)  # 其中的值未初始化
    print(torch.tensor([[-3.9719e-23, 1.3130e-42, 0.0000e+00],
                        [0.0000e+00, 0.0000e+00, 0.0000e+00],
                        [0.0000e+00, 0.0000e+00, 0.0000e+00],
                        [0.0000e+00, 0.0000e+00, 0.0000e+00],
                        [0.0000e+00, 0.0000e+00, 0.0000e+00]]))

    x = torch.rand(5, 3)  # 其中的值是在区间 [0, 1) 内均匀分布的随机数。
    print(torch.tensor([[0.1721, 0.5466, 0.7132],
                        [0.8289, 0.5445, 0.3396],
                        [0.0855, 0.5145, 0.2988],
                        [0.5537, 0.6823, 0.0242],
                        [0.4761, 0.9997, 0.8869]]))

    zeros_tensor = torch.zeros(2, 3)  # 创建一个大小为 2x3 的张量，其中所有元素都初始化为 0
    print(torch.tensor([[0., 0., 0.],
                        [0., 0., 0.]]))

    # 创建一个大小为 2x3 的张量，其中所有元素都初始化为 1
    ones_tensor = torch.ones(2, 3)
    print(torch.tensor([[1., 1., 1.],
                        [1., 1., 1.]]))

    # 创建一个大小为 2x3 的张量，其中所有元素都是从标准正态分布中随机抽样得到的
    randn_tensor = torch.randn(2, 3)
    print(torch.tensor([[-1.6176, -0.3406, -0.1306],
                        [-0.9964, 0.5069, 1.5283]]))

    # 直接根据数据创建张量
    x = torch.tensor([5.5, 3])
    print(torch.tensor([5.5000, 3.0000]))

    # 基于现有的张量创建一个新的张量。如果用户没有提供新的值
    x = x.new_ones(5, 3, dtype=torch.double)  # 创建了一个新的大小为 5x3 的张量 不指定任何参数时 元素会被初始化为 1
    x = torch.randn_like(x, dtype=torch.float)
    print(x.new_ones(5, 3, dtype=torch.double))
    print(x)

    x = torch.eye(2, 2)  # 【单位矩阵 2*2】
    print(x)

    # 生成一个形状为 (3, 3) 的张量，元素值在 0 到 9 之间
    random_int_tensor = torch.randint(low=0, high=10, size=(3, 3))
    print(random_int_tensor)

    # 将多个张量按照某个维度堆叠起来时
    tensor1 = torch.tensor([1, 2, 3])
    tensor2 = torch.tensor([4, 5, 6])
    # 使用 torch.stack 沿着新的维度（维度0）堆叠这两个张量
    stacked_tensor = torch.stack((tensor1, tensor2))
    print(stacked_tensor)


def squeeze_use():
    # 扩展 unsqueeze() 方法可以在指定维度上增加一个维度，从而扩展张量的形状。
    # 假设你有一个大小为 28x28 的灰度图像
    image = torch.randn(28, 28)
    # 但是 PyTorch 中要求通道维度在最前面，所以需要添加一个通道维度
    # 使用 unsqueeze 在索引 0 的位置添加一个维度
    # 现在图像的维度是 torch.Size([1, 28, 28])
    image_with_channel = image.unsqueeze(0)
    print(image_with_channel.shape)

    # squeeze() 用于删除张量中大小为 1 的维度。它的作用是压缩张量的维度，但并不改变张量中的元素数量
    # 创建一个大小为 1x3x1x2 的张量
    tensor = torch.randn(1, 3, 1, 2)
    # 使用 squeeze() 方法压缩张量的维度
    squeezed_tensor = tensor.squeeze()
    print("原始张量形状:", tensor.shape)  # 输出: 原始张量形状: torch.Size([1, 3, 1, 2])
    print("压缩后张量形状:", squeezed_tensor.shape)  # 输出: 压缩后张量形状: torch.Size([3, 2])

    # 创建两个大小为 2x3 的张量
    tensor1 = torch.tensor([[1, 2, 3], [4, 5, 6]])
    tensor2 = torch.tensor([[7, 8, 9], [10, 11, 12]])
    # 沿第一维度连接两个张量
    concatenated_tensor = torch.cat((tensor1, tensor2), dim=0)


def conv_use():
    # 实际创建卷积层时需指定具体参数值
    conv_layer = nn.Conv2d(
        in_channels=3,  # 输入通道数（如 RGB 图像为 3）
        out_channels=64,  # 输出通道数（卷积核数量）
        kernel_size=3,  # 卷积核大小 3x3
        padding=1  # 输入周围填充 1 层 0（保持输出尺寸）
    )

    # 假设有一个输入张量 input_tensor，维度为 [batch_size, 3, height, width]
    batch_size = 32
    height = 128
    width = 128
    input_tensor = torch.randn(batch_size, 3, height, width)

    # 进行前向传播
    output_tensor = conv_layer(input_tensor)
    print(f"输入尺寸: {input_tensor.shape}")
    print(f"输出尺寸: {output_tensor.shape}")


def shape_use():
    # size 和 shape 都是用来描述张量（tensor）的维度的属性。它们提供了相同的信息，但是在不同的语境中使用。
    # size：size() 是 PyTorch 张量对象的一个方法，用于返回张量的维度。
    # 这个方法返回的是一个包含每个维度大小的元组，元组的长度表示张量的维度。
    # 例如，一个大小为 2x3 的张量，它的 size() 方法会返回 (2, 3)。

    # shape：shape 是一个属性，用于返回张量的维度。
    # 它是一个直接获取张量形状的属性，而不是一个方法。
    # 和 size() 方法一样，shape 也返回一个包含每个维度大小的元组。
    # 例如，一个大小为 2x3 的张量，它的 shape 属性会返回 (2, 3)。

    # dtype:是用来描述张量中元素的数据类型的属性
    import numpy as np
    # 创建一个大小为 2x3 的张量
    tensor = torch.tensor([[1, 2, 3], [4, 5, 6]])
    # 使用 size() 方法获取张量的大小
    size = tensor.size()
    print("Size:", size)  # 输出: Size: torch.Size([2, 3])
    # 使用 shape 属性获取张量的形状
    shape = tensor.shape
    print("Shape:", shape)  # 输出: Shape: torch.Size([2, 3])
    # 创建一个大小为 2x3 的张量，并指定数据类型为双精度浮点数
    tensor = torch.randn(2, 3, dtype=torch.double)
    print(tensor)

    # PyTorch 张量转换为 NumPy 数组
    # 创建一个 PyTorch 张量
    torch_tensor = torch.randn(3, 4)
    # 将 PyTorch 张量转换为 NumPy 数组
    numpy_array = torch_tensor.numpy()
    print(numpy_array)

    # NumPy 数组转换为 PyTorch 张量：
    # 创建一个 NumPy 数组
    numpy_array = np.random.randn(3, 4)
    # 将 NumPy 数组转换为 PyTorch 张量
    torch_tensor = torch.from_numpy(numpy_array)
    print(torch_tensor)

    x = tensor([[-1.2605, 0.6679, 1.0013],
                [-1.2571, -1.1844, -0.7229],
                [2.0382, 2.0700, 1.6898],
                [-0.6017, 1.5209, -1.3384],
                [0.5035, -0.4835, 2.1972]])

    # torch.Size实际上是一个元组，所以它支持所有的元组操作
    x.size()
    torch.Size([5, 3])

    y = torch.rand(5, 3)
    x + y  # 或者 torch.add(x, y)
    torch.add(x, y)

    # 更多张量操作，包括转置（transposing）、索引（indexing）、切片（slicing）、
    # 数学操作（mathematical operations）、线性代数（liner algebra）、随机数（random numbers）

    # 创建一个大小为 3x3 的张量
    tensor = torch.tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    # 切片获取第一行的元素
    first_row = tensor[0, :]
    # 获取第一列的元素
    first_column = tensor[:, 0]

    # 创建一个大小为 2x3 的张量
    tensor = torch.tensor([[1, 2, 3], [4, 5, 6]])
    # 重塑为大小为 3x2 的张量
    reshaped_tensor = tensor.reshape(3, 2)


def embedding_use():
    # nn.Embedding 层的实现基于矩阵乘法，其内部维护一个由随机初始化的词向量组成的矩阵。
    # 假设词汇表大小为10000，每个词语被表示为一个长度为100的向量
    vocab_size = 10000
    embedding_dim = 100
    # 创建一个 Embedding 层
    embedding_layer = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim)
    # 假设有一个输入张量 input_indices，包含了一批词语的索引
    input_indices = torch.LongTensor([[1, 2, 3], [4, 5, 6]])
    # 将输入张量传递给 Embedding 层
    embedded_vectors = embedding_layer(input_indices)
    print(embedded_vectors.shape)  # 输出: torch.Size([2, 3, 100])


def argmax_use():
    # torch.argmax() 是 PyTorch 中一个用于在指定维度上找到张量中最大值的索引的函数。
    # 具体来说，torch.argmax() 返回沿着指定维度（dim 参数指定）上最大值的索引。
    # 在这里，dim=1 表示在第一个维度（通常是列）上进行操作。
    # 定义预测结果为张量（Tensor）
    pred = torch.tensor([
        [0.1, 0.8, 0.1],  # 样本1的预测结果，最大值索引为1
        [0.3, 0.2, 0.5],  # 样本2的预测结果，最大值索引为2
        [0.5, 0.4, 0.1]  # 样本3的预测结果，最大值索引为0
    ])

    # 在 dim=1 维度（行方向）上找到最大值的索引
    result = torch.argmax(pred, dim=1)
    print(result)  # 输出：tensor([1, 2, 0])


if __name__ == "__main__":
    # 简单做一个交易分类
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader

    # 1. 数据预处理
    # 有了处理好的数据集,包含特征和标签
    """
    获取历史交易数据,包括交易金额、时间、地点、账户信息等特征。
    对数据进行清洗,处理缺失值、异常值等。
    将类别标签(正常、可疑、洗钱)编码为数值,如0、1、2。
    """

    # 模拟数据（实际需替换为真实数据）
    num_train = 1000
    num_test = 200
    input_size = 10  # 假设特征维度为10
    train_features = torch.randn(num_train, input_size)
    train_labels = torch.randint(0, 3, (num_train,))  # 0、1、2三类
    test_features = torch.randn(num_test, input_size)
    test_labels = torch.randint(0, 3, (num_test,))


    # 自定义数据集
    class TransactionDataset(Dataset):
        def __init__(self, features, labels):
            self.features = features
            self.labels = labels

        def __len__(self):
            return len(self.labels)

        def __getitem__(self, idx):
            return self.features[idx], self.labels[idx]


    # 2. 构建模型
    # 定义神经网络模型
    class TransactionClassifier(nn.Module):
        def __init__(self, input_size, hidden_size, num_classes):
            super(TransactionClassifier, self).__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(hidden_size, num_classes)

        def forward(self, x):
            out = self.fc1(x)
            out = self.relu(out)
            out = self.fc2(out)
            return out


    # 3. 训练模型
    # 准备数据
    train_dataset = TransactionDataset(train_features, train_labels)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

    # 初始化模型、损失函数和优化器
    input_size = train_features.shape[1]
    hidden_size = 64
    num_classes = 3  # 正常、可疑、洗钱
    model = TransactionClassifier(input_size, hidden_size, num_classes)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 训练循环
    num_epochs = 100
    for epoch in range(num_epochs):
        running_loss = 0.0
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f'Epoch {epoch + 1}, Loss: {running_loss / len(train_loader)}')

    # 4. 评估模型
    # 准备测试数据
    test_dataset = TransactionDataset(test_features, test_labels)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # 评估模型
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print(f'Accuracy: {100 * correct / total}%')

    # 5. 模型部署
    # 导出模型权重
    torch.save(model.state_dict(), 'transaction_classifier.pth')
    new_transaction = torch.randn(1, input_size)  # 批量大小为1，特征维度匹配模型

    # 推理代码
    model.load_state_dict(torch.load('transaction_classifier.pth'))
    model.eval()
    with torch.no_grad():
        output = model(new_transaction)
        _, predicted = torch.max(output.data, 1)
        print(f'Predicted class: {predicted.item()}')  # 0: 正常, 1: 可疑, 2: 洗钱