import os
from pathlib import Path
from typing import Tuple, Dict, List
import torch
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

CLASSES = ["scratch", "dent", "crack", "shattered_glass", "no_damage"]

def get_data_transforms() -> Dict[str, transforms.Compose]:
    """
    Returns image transformation pipelines for training and validation.
    Training pipeline includes augmentations (flips, slight jitter, rotation) to prevent overfitting.
    """
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    return {"train": train_transform, "val": val_transform, "test": val_transform}


def create_dataloaders(
    data_dir: str,
    batch_size: int = 16,
    num_workers: int = 0
) -> Tuple[DataLoader, DataLoader, DataLoader, List[str]]:
    """
    Creates PyTorch DataLoaders for train, val, and test splits.
    Expects standard ImageFolder directory structure:
        data_dir/
            train/class_name/*.jpg
            val/class_name/*.jpg
            test/class_name/*.jpg
    """
    data_transforms = get_data_transforms()
    base_path = Path(data_dir)

    train_dir = base_path / "train"
    val_dir = base_path / "val"
    test_dir = base_path / "test"

    train_dataset = datasets.ImageFolder(str(train_dir), transform=data_transforms["train"])
    val_dataset = datasets.ImageFolder(str(val_dir), transform=data_transforms["val"])
    test_dataset = datasets.ImageFolder(str(test_dir), transform=data_transforms["test"])

    class_names = train_dataset.classes

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader, test_loader, class_names
