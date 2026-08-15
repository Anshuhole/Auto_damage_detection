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

def train_network():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)
    
    data_dir = CURR_DIR / "kaggle_car_damage_dataset"
    
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomAffine(degrees=10, translate=(0.05, 0.05), scale=(0.95, 1.05)),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
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
    
    print(f"Dataset classes: {train_ds.classes}")
    print(f"Train: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)
    
    model = DamageClassifierNet(
        num_damage_classes=len(train_ds.classes),
        num_severity_classes=4,
        pretrained=True
    ).to(device)
    
    # Fine-tune layer4 and classification head
    for param in model.backbone.parameters():
        param.requires_grad = False
    for param in model.backbone.layer4.parameters():
        param.requires_grad = True
        
    criterion_damage = nn.CrossEntropyLoss()
    criterion_sev = nn.CrossEntropyLoss()
    
    optimizer = optim.AdamW([
        {'params': model.backbone.layer4.parameters(), 'lr': 1e-4},
        {'params': model.shared_fc.parameters(), 'lr': 5e-4},
        {'params': model.damage_head.parameters(), 'lr': 1e-3},
        {'params': model.severity_head.parameters(), 'lr': 1e-3}
    ], weight_decay=1e-4)
    
    epochs = 6
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    
    sev_map = {0: 1, 1: 1, 2: 3, 3: 0, 4: 2}
    best_acc = 0.0
    best_weights = copy.deepcopy(model.state_dict())
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        running_correct = 0
        
        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)
            sev_targets = torch.tensor([sev_map.get(int(l.item()), 1) for l in labels], device=device)
            
            optimizer.zero_grad()
            damage_logits, sev_logits = model(inputs)
            loss_d = criterion_damage(damage_logits, labels)
            loss_s = criterion_sev(sev_logits, sev_targets)
            loss = loss_d + 0.5 * loss_s
            
            loss.backward()
            optimizer.step()
            
            _, preds = torch.max(damage_logits, 1)
            running_loss += loss.item() * inputs.size(0)
            running_correct += torch.sum(preds == labels.data)
            
        train_acc = (running_correct.double() / len(train_ds)).item()
        
        # Validation
        model.eval()
        val_correct = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)
                damage_logits, _ = model(inputs)
                _, preds = torch.max(damage_logits, 1)
                val_correct += torch.sum(preds == labels.data)
                
        val_acc = (val_correct.double() / len(val_ds)).item()
        scheduler.step()
        
        print(f"Epoch {epoch+1:02d}/{epochs:02d} | Train Acc: {train_acc*100:.2f}% | Val Acc: {val_acc*100:.2f}%")
        
        if val_acc > best_acc:
            best_acc = val_acc
            best_weights = copy.deepcopy(model.state_dict())
            
    print(f"\nTraining Complete. Best Validation Accuracy: {best_acc*100:.2f}%")
    
    # Save checkpoint
    os.makedirs(os.path.dirname(MODEL_WEIGHTS_PATH), exist_ok=True)
    torch.save(best_weights, str(MODEL_WEIGHTS_PATH))
    print(f"Model saved to: {MODEL_WEIGHTS_PATH}")

if __name__ == "__main__":
    train_network()
