import torch
import torchvision
from torch import nn
from torch.utils.data import DataLoader
from torchvision import transforms

from vit import ViT


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = 100.0 * correct / total
    return epoch_loss, epoch_acc

def main():
    batch_size = 128
    epochs = 20
    lr = 3e-4
    weight_decay = 1e-4
    num_workers = 2
    load_path = "best_vit_cifar10.pth"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    test_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.4914, 0.4822, 0.4465)),
    ])

    test_dataset = torchvision.datasets.CIFAR10(
        root="./data",
        train=False,
        download=True,
        transform=test_transform
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )

    model = ViT(
        img_size=32,
        patch_size=4,
        in_channels=3,
        num_classes=10,
        embed_dim=256,
        depth=6,
        num_heads=8,
        mlp_ratio=4.0,
        dropout=0.1
    ).to(device)

    criterion = nn.CrossEntropyLoss()

    for i in range(epochs):
        test_loss, test_acc = evaluate(
            model, test_loader, criterion, device
        )

    print(f"Test Loss: {test_loss:.4f} | Test Acc: {test_acc:.2f}% | ")

if __name__ == "__main__":
    main()