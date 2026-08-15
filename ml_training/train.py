import os
import sys
import time
import copy
import argparse
from pathlib import Path

# Add current directory and backend to sys.path
CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent / "backend"
sys.path.insert(0, str(CURR_DIR))
sys.path.insert(0, str(BACKEND_DIR))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
import matplotlib.pyplot as plt
import numpy as np

from dataset_loader import create_dataloaders
from generate_synthetic_data import generate_dataset, DATA_DIR
from app.ml.classifier import DamageClassifierNet
from app.config import WEIGHTS_DIR, MODEL_WEIGHTS_PATH

def set_seed(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

def train_model(
    data_dir: str,
    epochs: int = 6,
    batch_size: int = 16,
    learning_rate: float = 1e-4,
    save_path: str = str(MODEL_WEIGHTS_PATH)
):
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n========================================================")
    print(f"  AutoInspect AI — ResNet50 Transfer Learning Pipeline  ")
    print(f"========================================================")
    print(f"Training on Device : {device}")
    print(f"Target Epochs      : {epochs}")
    print(f"Batch Size         : {batch_size}")
    print(f"Initial LR         : {learning_rate}")
    print(f"Dataset Directory  : {data_dir}\n")

    # If dataset doesn't exist, generate synthetic dataset first
    if not (Path(data_dir) / "train").exists():
        print("[Dataset Setup] Dataset folder not found. Generating synthetic car damage dataset...")
        generate_dataset(base_dir=Path(data_dir), samples_per_class_train=40, samples_per_class_val=10)

    train_loader, val_loader, test_loader, class_names = create_dataloaders(
        data_dir=data_dir,
        batch_size=batch_size
    )

    print(f"Classes ({len(class_names)}): {class_names}")
    print(f"Training samples   : {len(train_loader.dataset)}")
    print(f"Validation samples : {len(val_loader.dataset)}")
    print(f"Test samples       : {len(test_loader.dataset)}\n")

    # Initialize model with ImageNet pretrained ResNet50 backbone
    model = DamageClassifierNet(
        num_damage_classes=len(class_names),
        num_severity_classes=4,
        pretrained=True
    ).to(device)

    # Loss functions & Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    # History tracking
    history = {
        "train_loss": [], "train_acc": [],
        "val_loss": [], "val_acc": []
    }

    best_model_wts = copy.deepcopy(model.state_dict())
    best_val_acc = 0.0

    start_time = time.time()

    for epoch in range(epochs):
        print(f"Epoch {epoch+1:02d}/{epochs:02d} [LR: {scheduler.get_last_lr()[0]:.6f}]")
        print("-" * 45)

        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
                dataloader = train_loader
            else:
                model.eval()
                dataloader = val_loader

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    damage_logits, _ = model(inputs)
                    _, preds = torch.max(damage_logits, 1)
                    loss = criterion(damage_logits, labels)

                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(dataloader.dataset)
            epoch_acc = (running_corrects.double() / len(dataloader.dataset)).item()

            if phase == "train":
                history["train_loss"].append(epoch_loss)
                history["train_acc"].append(epoch_acc)
            else:
                history["val_loss"].append(epoch_loss)
                history["val_acc"].append(epoch_acc)
                scheduler.step()

                if epoch_acc > best_val_acc:
                    best_val_acc = epoch_acc
                    best_model_wts = copy.deepcopy(model.state_dict())

            print(f"  {phase.capitalize():<5} Loss: {epoch_loss:.4f} | Acc: {epoch_acc*100:.2f}%")

        print()

    time_elapsed = time.time() - start_time
    print(f"Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s")
    print(f"Best Validation Accuracy: {best_val_acc * 100:.2f}%\n")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(best_model_wts, save_path)
    print(f"[Model Saved] Best model checkpoint saved to: {save_path}")

    _plot_training_curves(history, output_path=str(CURR_DIR / "training_history.png"))

    return history

def _plot_training_curves(history, output_path="training_history.png"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    epochs_range = range(1, len(history["train_loss"]) + 1)

    # Loss Plot
    ax1.plot(epochs_range, history["train_loss"], 'o-', color='#0284c7', label='Train Loss', linewidth=2)
    ax1.plot(epochs_range, history["val_loss"], 's--', color='#f43f5e', label='Val Loss', linewidth=2)
    ax1.set_title('Cross-Entropy Loss vs Epochs', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Epoch', fontsize=9)
    ax1.set_ylabel('Loss', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')

    # Accuracy Plot
    ax2.plot(epochs_range, [acc * 100 for acc in history["train_acc"]], 'o-', color='#10b981', label='Train Accuracy', linewidth=2)
    ax2.plot(epochs_range, [acc * 100 for acc in history["val_acc"]], 's--', color='#f59e0b', label='Val Accuracy', linewidth=2)
    ax2.set_title('Classification Accuracy vs Epochs (%)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Epoch', fontsize=9)
    ax2.set_ylabel('Accuracy (%)', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='lower right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[Curves Exported] Loss and Accuracy curves saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train AutoInspect AI ResNet50 Damage Classifier")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR), help="Path to car damage dataset")
    parser.add_argument("--epochs", type=int, default=6, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    args = parser.parse_args()

    train_model(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
