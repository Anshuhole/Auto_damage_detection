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
import matplotlib.pyplot as plt
import numpy as np

CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent / "backend"
sys.path.insert(0, str(CURR_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.classifier import DamageClassifierNet
from app.config import MODEL_WEIGHTS_PATH, DAMAGE_CLASSES, SEVERITY_LEVELS

def train_network():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("==========================================================")
    print("  AutoInspect AI — Training ResNet50 on Real Car Damage   ")
    print("==========================================================")
    print("Computation Device:", device)
    
    data_dir = CURR_DIR / "real_dataset"
    if not data_dir.exists():
        print(f"Error: {data_dir} does not exist. Run prepare_real_dataset.py first.")
        return

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomAffine(degrees=10, translate=(0.05, 0.05), scale=(0.95, 1.05)),
        transforms.ColorJitter(brightness=0.18, contrast=0.18, saturation=0.15, hue=0.04),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    train_ds = datasets.ImageFolder(str(data_dir / "train"), transform=train_transform)
    val_ds = datasets.ImageFolder(str(data_dir / "val"), transform=eval_transform)
    test_ds = datasets.ImageFolder(str(data_dir / "test"), transform=eval_transform)
    
    print(f"Dataset classes detected: {train_ds.classes}")
    print(f"Training samples: {len(train_ds)}, Validation: {len(val_ds)}, Test: {len(test_ds)}")
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)
    
    # Class mapping index
    cls_to_idx = train_ds.class_to_idx
    print("Class-to-Index mapping:", cls_to_idx)
    
    # Severity mapping for ground truth targets:
    # 0: scratch -> minor/moderate (0 or 1)
    # 1: dent -> moderate/severe (1 or 2)
    # 2: crack -> moderate (1)
    # 3: shattered_glass -> severe (2)
    # 4: no_damage -> none (3)
    def get_severity_target(damage_cls_idx: int) -> int:
        if damage_cls_idx == cls_to_idx.get("scratch", 0):
            return 0  # minor
        elif damage_cls_idx == cls_to_idx.get("dent", 1):
            return 1  # moderate
        elif damage_cls_idx == cls_to_idx.get("crack", 2):
            return 1  # moderate
        elif damage_cls_idx == cls_to_idx.get("shattered_glass", 3):
            return 2  # severe
        else:
            return 3  # none

    model = DamageClassifierNet(
        num_damage_classes=len(train_ds.classes),
        num_severity_classes=len(SEVERITY_LEVELS),
        pretrained=True
    ).to(device)
    
    # Freeze lower layers, unfreeze layer3 and layer4 for fine-tuning
    for param in model.backbone.parameters():
        param.requires_grad = False
    for param in model.backbone.layer3.parameters():
        param.requires_grad = True
    for param in model.backbone.layer4.parameters():
        param.requires_grad = True
        
    criterion_damage = nn.CrossEntropyLoss(label_smoothing=0.05)
    criterion_severity = nn.CrossEntropyLoss(label_smoothing=0.05)
    
    optimizer = optim.AdamW([
        {'params': model.backbone.layer3.parameters(), 'lr': 3e-5},
        {'params': model.backbone.layer4.parameters(), 'lr': 1e-4},
        {'params': model.shared_fc.parameters(), 'lr': 5e-4},
        {'params': model.damage_head.parameters(), 'lr': 1e-3},
        {'params': model.severity_head.parameters(), 'lr': 1e-3}
    ], weight_decay=1e-4)
    
    epochs = 12
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    
    best_acc = 0.0
    best_weights = copy.deepcopy(model.state_dict())
    
    history = {
        "train_loss": [], "train_acc": [],
        "val_loss": [], "val_acc": []
    }
    
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        running_correct = 0
        total_samples = 0
        
        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            sev_targets = torch.tensor([get_severity_target(int(l.item())) for l in labels], device=device)
            
            optimizer.zero_grad()
            damage_logits, sev_logits = model(inputs)
            
            loss_d = criterion_damage(damage_logits, labels)
            loss_s = criterion_severity(sev_logits, sev_targets)
            loss = loss_d + 0.5 * loss_s
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(damage_logits, 1)
            running_correct += torch.sum(preds == labels.data).item()
            total_samples += inputs.size(0)
            
        scheduler.step()
        epoch_train_loss = running_loss / total_samples
        epoch_train_acc = running_correct / total_samples
        
        # Validation Pass
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_samples = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)
                sev_targets = torch.tensor([get_severity_target(int(l.item())) for l in labels], device=device)
                
                damage_logits, sev_logits = model(inputs)
                loss_d = criterion_damage(damage_logits, labels)
                loss_s = criterion_severity(sev_logits, sev_targets)
                loss = loss_d + 0.5 * loss_s
                
                val_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(damage_logits, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_samples += inputs.size(0)
                
        epoch_val_loss = val_loss / val_samples
        epoch_val_acc = val_correct / val_samples
        
        history["train_loss"].append(epoch_train_loss)
        history["train_acc"].append(epoch_train_acc)
        history["val_loss"].append(epoch_val_loss)
        history["val_acc"].append(epoch_val_acc)
        
        print(f"Epoch [{epoch:02d}/{epochs:02d}] "
              f"Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc*100:.2f}% | "
              f"Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc*100:.2f}%")
              
        if epoch_val_acc > best_acc:
            best_acc = epoch_val_acc
            best_weights = copy.deepcopy(model.state_dict())
            print(f"  --> Saved new best model checkpoint (Val Acc: {best_acc*100:.2f}%)")
            
    elapsed = time.time() - start_time
    print(f"\n[Training Complete] Finished in {elapsed/60:.2f} minutes. Best Validation Accuracy: {best_acc*100:.2f}%")
    
    # Save best model to destination paths
    MODEL_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(best_weights, str(MODEL_WEIGHTS_PATH))
    print(f"[Model Saved] Saved to {MODEL_WEIGHTS_PATH}")
    
    local_weights_path = CURR_DIR / "car_damage_resnet50.pth"
    torch.save(best_weights, str(local_weights_path))
    
    # Test Evaluation
    model.load_state_dict(best_weights)
    model.eval()
    test_correct = 0
    test_total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            damage_logits, _ = model(inputs)
            _, preds = torch.max(damage_logits, 1)
            test_correct += torch.sum(preds == labels.data).item()
            test_total += inputs.size(0)
    test_acc = test_correct / test_total
    print(f"[Test Set Evaluation] Final Test Accuracy: {test_acc*100:.2f}% ({test_correct}/{test_total})")
    
    # Plot training curves
    plt.figure(figsize=(10, 4.5))
    plt.subplot(1, 2, 1)
    plt.plot(history["train_loss"], label="Train Loss", color="#0284c7", linewidth=2)
    plt.plot(history["val_loss"], label="Val Loss", color="#e11d48", linewidth=2)
    plt.title("Loss Convergence", fontsize=11, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    
    plt.subplot(1, 2, 2)
    plt.plot([a * 100 for a in history["train_acc"]], label="Train Acc", color="#0284c7", linewidth=2)
    plt.plot([a * 100 for a in history["val_acc"]], label="Val Acc", color="#10b981", linewidth=2)
    plt.title("Classification Accuracy (%)", fontsize=11, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy %")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(str(CURR_DIR / "training_history.png"), dpi=300)
    plt.close()
    print(f"[Plot Saved] Saved training history plot to {CURR_DIR / 'training_history.png'}")

if __name__ == "__main__":
    train_network()
