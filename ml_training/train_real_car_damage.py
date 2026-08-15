import os
import sys
import copy
import time
from pathlib import Path
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt

CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent / "backend"
sys.path.insert(0, str(CURR_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from app.ml.classifier import DamageClassifierNet
from app.config import MODEL_WEIGHTS_PATH, DAMAGE_CLASSES, SEVERITY_LEVELS


def categorize_damaged_image(img_path: Path) -> int:
    """
    Deterministically determines damage class index based on visual defect signatures:
    0: scratch, 1: dent, 2: crack, 3: shattered_glass
    """
    img = cv2.imread(str(img_path))
    if img is None:
        return 1  # default to dent

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Cabin windshield area (top center)
    cabin = gray[int(h * 0.18):int(h * 0.48), int(w * 0.25):int(w * 0.75)]
    cabin_edges = cv2.Canny(cabin, 95, 230) if cabin.size > 0 else np.zeros((1, 1))
    glass_density = float(np.mean(cabin_edges > 0))

    # 2. Linear scratches (sharp thin scuffs)
    edges = cv2.Canny(gray, 75, 190)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=45, minLineLength=35, maxLineGap=8)
    num_lines = len(lines) if lines is not None else 0

    # 3. Body panel deformation / dent shadows
    blurred = cv2.GaussianBlur(gray, (41, 41), 0)
    diff = np.abs(gray.astype(np.float32) - blurred.astype(np.float32))
    panel_diff = diff[int(h * 0.18):int(h * 0.82), int(w * 0.10):int(w * 0.90)]
    dent_anomaly = float(np.mean(panel_diff > 38.0)) if panel_diff.size > 0 else 0.0

    # 4. Bumper crack density
    bumper_edges = edges[int(h * 0.60):, :]
    bumper_density = float(np.mean(bumper_edges > 0)) if bumper_edges.size > 0 else 0.0

    if glass_density > 0.18 and num_lines > 12:
        return 3  # shattered_glass
    elif num_lines >= 14 and dent_anomaly < 0.05:
        return 0  # scratch
    elif bumper_density > 0.12 and dent_anomaly < 0.06:
        return 2  # crack
    elif dent_anomaly > 0.04 or num_lines < 8:
        return 1  # dent
    elif num_lines >= 8:
        return 0  # scratch
    else:
        return 2  # crack


class RealCarDamageDataset(Dataset):
    def __init__(self, root_dir: Path, split: str = "training", transform=None):
        self.transform = transform
        self.samples = []  # tuple of (image_path, damage_label, severity_label)

        split_dir = root_dir / split
        damage_dir = split_dir / "00-damage"
        whole_dir = split_dir / "01-whole"

        # 1. Damaged car images
        if damage_dir.exists():
            damage_imgs = list(damage_dir.glob("*.JPEG")) + list(damage_dir.glob("*.jpg")) + list(damage_dir.glob("*.png"))
            for img_p in damage_imgs:
                dmg_cls = categorize_damaged_image(img_p)
                # Assign realistic severity based on damage class
                if dmg_cls == 3:  # shattered_glass
                    sev_cls = 2  # severe
                elif dmg_cls == 1:  # dent
                    sev_cls = 1 if np.random.rand() > 0.4 else 2  # moderate or severe
                elif dmg_cls == 2:  # crack
                    sev_cls = 1  # moderate
                else:  # scratch
                    sev_cls = 0 if np.random.rand() > 0.3 else 1  # minor or moderate
                self.samples.append((str(img_p), dmg_cls, sev_cls))

        # 2. Whole / clean car images
        if whole_dir.exists():
            whole_imgs = list(whole_dir.glob("*.JPEG")) + list(whole_dir.glob("*.jpg")) + list(whole_dir.glob("*.png"))
            for img_p in whole_imgs:
                self.samples.append((str(img_p), 4, 3))  # class 4: no_damage, severity 3: none

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, dmg_lbl, sev_lbl = self.samples[idx]
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            # Fallback black image if file corrupt
            img = Image.new("RGB", (224, 224), (0, 0, 0))

        if self.transform:
            img = self.transform(img)

        return img, torch.tensor(dmg_lbl, dtype=torch.long), torch.tensor(sev_lbl, dtype=torch.long)


def train_real_car_damage():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("\n========================================================")
    print("  AutoInspect AI — Training ResNet50 on Real Vehicles   ")
    print("========================================================")
    print(f"Device: {device}\n")

    kaggle_cache = Path("C:/Users/VISHNU/.cache/kagglehub/datasets/anujms/car-damage-detection/versions/1/data1a")
    if not kaggle_cache.exists():
        print(f"Error: Dataset not found at {kaggle_cache}")
        return

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_ds = RealCarDamageDataset(kaggle_cache, split="training", transform=train_transform)
    val_ds = RealCarDamageDataset(kaggle_cache, split="validation", transform=val_transform)

    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0)

    print(f"Training Samples   : {len(train_ds)} total")
    print(f"Validation Samples : {len(val_ds)} total\n")

    # Compute class weights to balance losses
    labels = [s[1] for s in train_ds.samples]
    class_counts = np.bincount(labels, minlength=5)
    print(f"Training Class Distribution: {dict(zip(DAMAGE_CLASSES, class_counts))}")

    weights = 1.0 / (class_counts.astype(np.float32) + 1e-5)
    weights = weights / np.sum(weights) * 5.0
    class_weights_tensor = torch.tensor(weights, dtype=torch.float32).to(device)

    # Initialize model
    model = DamageClassifierNet(
        num_damage_classes=5,
        num_severity_classes=4,
        pretrained=True
    ).to(device)

    criterion_dmg = nn.CrossEntropyLoss(weight=class_weights_tensor)
    criterion_sev = nn.CrossEntropyLoss()

    optimizer = optim.AdamW([
        {'params': model.backbone.layer4.parameters(), 'lr': 1e-4},
        {'params': model.shared_fc.parameters(), 'lr': 3e-4},
        {'params': model.damage_head.parameters(), 'lr': 6e-4},
        {'params': model.severity_head.parameters(), 'lr': 6e-4}
    ], weight_decay=1e-4)

    # Freeze earlier layers for fast, robust transfer learning
    for name, param in model.backbone.named_parameters():
        if not name.startswith("layer4"):
            param.requires_grad = False

    epochs = 5
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    best_wts = copy.deepcopy(model.state_dict())
    best_val_acc = 0.0

    history = {
        "train_loss": [], "val_loss": [],
        "train_acc": [], "val_acc": []
    }

    start_time = time.time()

    for epoch in range(epochs):
        print(f"Epoch {epoch+1:02d}/{epochs:02d} [LR: {optimizer.param_groups[0]['lr']:.6f}]")
        print("-" * 48)

        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
                loader = train_loader
            else:
                model.eval()
                loader = val_loader

            running_loss = 0.0
            running_correct_dmg = 0
            running_correct_binary = 0

            for inputs, dmg_labels, sev_labels in loader:
                inputs = inputs.to(device)
                dmg_labels = dmg_labels.to(device)
                sev_labels = sev_labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    dmg_logits, sev_logits = model(inputs)
                    loss_dmg = criterion_dmg(dmg_logits, dmg_labels)
                    loss_sev = criterion_sev(sev_logits, sev_labels)
                    total_loss = loss_dmg + (0.5 * loss_sev)

                    _, dmg_preds = torch.max(dmg_logits, 1)

                    if phase == "train":
                        total_loss.backward()
                        optimizer.step()

                running_loss += total_loss.item() * inputs.size(0)
                running_correct_dmg += torch.sum(dmg_preds == dmg_labels.data)

                # Binary damage detection accuracy (damage vs whole)
                bin_preds = (dmg_preds != 4).long()
                bin_targets = (dmg_labels != 4).long()
                running_correct_binary += torch.sum(bin_preds == bin_targets.data)

            epoch_loss = running_loss / len(loader.dataset)
            epoch_acc_dmg = (running_correct_dmg.double() / len(loader.dataset)).item()
            epoch_acc_bin = (running_correct_binary.double() / len(loader.dataset)).item()

            if phase == "train":
                history["train_loss"].append(epoch_loss)
                history["train_acc"].append(epoch_acc_dmg)
            else:
                history["val_loss"].append(epoch_loss)
                history["val_acc"].append(epoch_acc_dmg)
                scheduler.step()

                if epoch_acc_bin > best_val_acc or (epoch_acc_bin == best_val_acc and epoch_acc_dmg > best_val_acc):
                    best_val_acc = epoch_acc_bin
                    best_wts = copy.deepcopy(model.state_dict())

            print(f"  {phase.capitalize():<5} Loss: {epoch_loss:.4f} | Damage Accuracy: {epoch_acc_dmg*100:.2f}% | Binary (Damage/Clean): {epoch_acc_bin*100:.2f}%")

        print()

    elapsed = time.time() - start_time
    print(f"[Training Complete in {elapsed:.1f}s] Best Validation Binary Accuracy: {best_val_acc*100:.2f}%")

    # Save model weights
    os.makedirs(os.path.dirname(MODEL_WEIGHTS_PATH), exist_ok=True)
    torch.save(best_wts, str(MODEL_WEIGHTS_PATH))
    print(f"[Weights Saved] Successfully saved checkpoint to: {MODEL_WEIGHTS_PATH}")

    # Plot training history
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history["train_loss"], label="Train Loss", color="#0284c7")
    plt.plot(history["val_loss"], label="Val Loss", color="#f43f5e")
    plt.title("Convergence Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot([a * 100 for a in history["train_acc"]], label="Train Acc %", color="#0284c7")
    plt.plot([a * 100 for a in history["val_acc"]], label="Val Acc %", color="#10b981")
    plt.title("Classification Accuracy (%)")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = CURR_DIR / "training_history.png"
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[Plot Saved] Training curves saved to: {plot_path}\n")


if __name__ == "__main__":
    train_real_car_damage()
