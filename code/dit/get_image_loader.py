import torch
from pathlib import Path
from typing import Optional, Tuple, Any

from PIL import Image
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


class PreprocessedImageDataset(Dataset):
    def __init__(self, root_dir: str,
                 transform: Optional[transforms.Compose] = None,
                 is_train: bool = True):
        self.root_dir = Path(root_dir)
        self.is_train = is_train

        self.image_paths = sorted([
            p for ext in ('*.jpeg', '*.jpg')
            for p in  self.root_dir.rglob(ext)
        ])

        if not self.image_paths:
            raise ValueError('No images found')
        self.transform = transform or self._get_default_transform()

    def _get_default_transform(self) -> transforms.Compose:
        return transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.1),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
            transforms.RandomApply([
                transforms.RandomAffine(
                    degrees=5,
                    translate=(0.02, 0.02),
                    scale=(0.98, 1.02),
                    interpolation=Image.BICUBIC
                )
            ], p=0.3),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path = self.image_paths[idx]

        try:
            img = Image.open(img_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # 应用变换
            tensor = self.transform(img)
            return tensor, 0
        except Exception as e:
            print(f"Error loading image: {img_path}: {e}")

def get_image_loader(
        data_dir: str,
        batch_size: int = 20,
        num_workers: int = 8
) -> DataLoader[Any]:
    full_dataset = PreprocessedImageDataset(root_dir=data_dir)

    common_kwargs = {
        'batch_size': batch_size,
        'num_workers': num_workers,
        'pin_memory': True,
        'prefetch_factor': 3,
        'persistent_workers': True,
        'drop_last': True
    }

    return DataLoader(
        dataset=full_dataset, shuffle=True, **common_kwargs
    )