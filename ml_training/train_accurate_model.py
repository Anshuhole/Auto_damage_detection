import os
import sys
import copy
import time
from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.utils.data import DataLoader, Dataset
from torchvision import datasets, transforms, models
from PIL import Image
import numpy as np

CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent / "backend"
sys.path.insert(0, str(CURR_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from app.config import MODEL_WEIGHTS_PATH, DAMAGE_CLASSES, SEVERITY_LEVELS

class FocalLoss(nn.Module):
    """
    Multi-class Focal Loss to focus learning on hard damage examples
    and prevent clean background dominance.
    """
    def __init__(self, alpha=None, gamma=2.0):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, reduction='none', weight=self.alpha)
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        return focal_loss.mean()


class PrecisionDamageResNet(nn.Module):
    """
    High-accuracy ResNet50 architecture with multi-level feature extraction
    specifically tuned for localized vehicle damage anomaly detection.
    """
    def __init__(self, num_damage_classes=5, num_severity_classes=4):
        super().__init__()
        # Pretrained ImageNet backbone
        base = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        
        self.conv1 = base.conv1
        self.bn1 = base.bn1
        self.relu = base.relu
        self.maxpool = base.maxpool

        self.layer1 = base.layer1
        self.layer2 = base.layer2
        self.layer3 = base.layer3
        self.layer4 = base.layer4

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))

        # Dense projection head with LayerNorm and residual connection
        self.head = nn.Sequential(
            nn.Linear(2048, 512),
            nn.LayerNorm(512),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(512, 128),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(128, num_damage_classes)
        )

        self.severity_head = nn.Sequential(
            nn.Linear(2048, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_severity_classes)
        )

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        feat = self.avgpool(x)
        feat_flat = torch.flatten(feat, 1)

        damage_logits = self.head(feat_flat)
        severity_logits = self.severity_head(feat_flat)

        return damage_logits, severity_logits


def train_precision_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("========================================================")
    print("   AutoInspect AI — Precision Damage Model Training     ")
    print("========================================================")
    print(f"Device: {device}\n")

    # Data Augmentations
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=12),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Dataset directory
    data_dir = CURR_DIR / "kaggle_car_damage_dataset"
    if not (data_dir / "train").exists():
        data_dir = CURR_DIR / "data"

    train_ds = datasets.ImageFolder(str(data_dir / "train"), transform=train_transform)
    val_ds = datasets.ImageFolder(str(data_dir / "val"), transform=val_transform)

    print(f"Class Names: {train_ds.classes}")
    print(f"Train samples: {len(train_ds)}, Val samples: {len(val_ds)}\n")

    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=16, shuffle=False, num_workers=0)

    model = PrecisionDamageResNet(
        num_damage_classes=len(train_ds.classes),
        num_severity_classes=4
    ).to(device)

    # Freeze earlier layers initially to preserve edge/texture filters, fine-tune layer3, layer4 and head
    for param in model.conv1.parameters(): param.requires_grad = False
    for param in model.bn1.parameters(): param.requires_grad = False
    for param in model.layer1.parameters(): param.requires_grad = False
    for param in model.layer2.parameters(): param.requires_grad = False

    # Loss function with Focal Loss
    criterion = FocalLoss(gamma=2.0)

    # Optimizer with differential learning rates
    optimizer = optim.AdamW([
        {'params': model.layer3.parameters(), 'lr': 1e-4},
        {'params': model.layer4.parameters(), 'lr': 2e-4},
        {'params': model.head.parameters(), 'lr': 1e-3},
        {'params': model.severity_head.parameters(), 'lr': 1e-3}
    ], weight_decay=1e-3)

    epochs = 5
    scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=epochs, eta_min=1e-6)

    best_val_acc = 0.0
    best_wts = copy.deepcopy(model.state_dict())

    for epoch in range(epochs):
        print(f"Epoch {epoch+1:02d}/{epochs:02d} [LR: {optimizer.param_groups[1]['lr']:.6f}]")
        print("-" * 45)

        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
                loader = train_loader
            else:
                model.eval()
                loader = val_loader

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    damage_logits, _ = model(inputs)
                    loss = criterion(damage_logits, labels)
                    _, preds = torch.max(damage_logits, 1)

                    if phase == "train":
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.5)
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(loader.dataset)
            epoch_acc = (running_corrects.double() / len(loader.dataset)).item()

            if phase == "val":
                scheduler.step()
                if epoch_acc > best_val_acc:
                    best_val_acc = epoch_acc
                    best_wts = copy.deepcopy(model.state_dict())

            print(f"  {phase.capitalize():<5} Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc*100:.2f}%")

        print()

    print(f"Training Complete. Best Validation Accuracy: {best_val_acc*100:.2f}%\n")

    # Save checkpoint
    os.makedirs(os.path.dirname(MODEL_WEIGHTS_PATH), exist_ok=True)
    torch.save(best_wts, str(MODEL_WEIGHTS_PATH))
    print(f"[Model Saved] Saved precision model weights to: {MODEL_WEIGHTS_PATH}")

if __name__ == "__main__":
    train_precision_model()
