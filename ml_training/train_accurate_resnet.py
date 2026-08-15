import os
import sys
import copy
import time
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent / "backend"
sys.path.insert(0, str(CURR_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.classifier import DamageClassifierNet
from app.config import MODEL_WEIGHTS_PATH, DAMAGE_CLASSES

def train_on_kaggle_data():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("\n========================================================")
    print("  Training ResNet50 Directly on Kaggle Real Car Dataset ")
    print("========================================================\n")

    data_dir = CURR_DIR / "kaggle_car_damage_dataset"

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_ds = datasets.ImageFolder(str(data_dir / "train"), transform=train_transform)
    val_ds = datasets.ImageFolder(str(data_dir / "val"), transform=val_transform)
    test_ds = datasets.ImageFolder(str(data_dir / "test"), transform=val_transform)

    print(f"Dataset Classes: {train_ds.classes}")
    print(f"Train: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}\n")

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)

    model = DamageClassifierNet(
        num_damage_classes=len(train_ds.classes),
        num_severity_classes=4,
        pretrained=True
    ).to(device)

    # Freeze earlier layers, fine-tune layer3, layer4 and classification heads
    for param in model.backbone.conv1.parameters(): param.requires_grad = False
    for param in model.backbone.bn1.parameters(): param.requires_grad = False
    for param in model.backbone.layer1.parameters(): param.requires_grad = False
    for param in model.backbone.layer2.parameters(): param.requires_grad = False

    criterion_damage = nn.CrossEntropyLoss()
    criterion_sev = nn.CrossEntropyLoss()

    optimizer = optim.AdamW([
        {'params': model.backbone.layer3.parameters(), 'lr': 1e-4},
        {'params': model.backbone.layer4.parameters(), 'lr': 2e-4},
        {'params': model.shared_fc.parameters(), 'lr': 5e-4},
        {'params': model.damage_head.parameters(), 'lr': 1e-3},
        {'params': model.severity_head.parameters(), 'lr': 1e-3}
    ], weight_decay=1e-4)

    epochs = 4
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    best_acc = 0.0
    best_wts = copy.deepcopy(model.state_dict())

    # Map class index to default severity (0: minor, 1: moderate, 2: severe, 3: none)
    sev_map = {0: 1, 1: 1, 2: 3, 3: 0, 4: 2}

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
            running_correct = 0

            for inputs, labels in loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                sev_targets = torch.tensor([sev_map.get(int(l.item()), 1) for l in labels], device=device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    damage_logits, sev_logits = model(inputs)
                    loss_d = criterion_damage(damage_logits, labels)
                    loss_s = criterion_sev(sev_logits, sev_targets)
                    loss = loss_d + 0.5 * loss_s

                    _, preds = torch.max(damage_logits, 1)

                    if phase == "train":
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_correct += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(loader.dataset)
            epoch_acc = (running_correct.double() / len(loader.dataset)).item()

            if phase == "val":
                scheduler.step()
                if epoch_acc > best_acc:
                    best_acc = epoch_acc
                    best_wts = copy.deepcopy(model.state_dict())

            print(f"  {phase.capitalize():<5} Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc*100:.2f}%")

        print()

    print(f"\n[Training Complete] Best Validation Accuracy: {best_acc*100:.2f}%")

    # Evaluate on Test set
    model.load_state_dict(best_wts)
    model.eval()
    test_correct = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            damage_logits, _ = model(inputs)
            _, preds = torch.max(damage_logits, 1)
            test_correct += torch.sum(preds == labels.data)

    test_acc = (test_correct.double() / len(test_ds)).item()
    print(f"[Test Set Evaluation] Final Test Accuracy: {test_acc*100:.2f}%\n")

    # Save checkpoint
    os.makedirs(os.path.dirname(MODEL_WEIGHTS_PATH), exist_ok=True)
    torch.save(best_wts, str(MODEL_WEIGHTS_PATH))
    print(f"[Model Saved] Saved high-accuracy weights to: {MODEL_WEIGHTS_PATH}")

if __name__ == "__main__":
    train_on_kaggle_data()
