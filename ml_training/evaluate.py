import os
import sys
import argparse
from pathlib import Path

# Add current directory and backend to sys.path
CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent / "backend"
sys.path.insert(0, str(CURR_DIR))
sys.path.insert(0, str(BACKEND_DIR))

import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from app.ml.classifier import DamageClassifierNet
from app.config import MODEL_WEIGHTS_PATH, DAMAGE_CLASSES
from dataset_loader import create_dataloaders
from generate_synthetic_data import DATA_DIR

def evaluate_model(weights_path=str(MODEL_WEIGHTS_PATH), data_dir=str(DATA_DIR)):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("\n========================================================")
    print("      AutoInspect AI — Model Evaluation & Metrics       ")
    print("========================================================")
    print(f"Evaluating on Dataset: {data_dir}")
    print(f"Model Checkpoint Path: {weights_path}\n")

    _, _, test_loader, class_names = create_dataloaders(data_dir=data_dir, batch_size=16)

    model = DamageClassifierNet(
        num_damage_classes=len(class_names),
        num_severity_classes=4,
        pretrained=False
    ).to(device)

    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=device))
        print(f"[Model Loader] Loaded weights from: {weights_path}")
    else:
        print(f"[Warning] Weights file not found at {weights_path}. Running with initialized weights.")

    model.eval()

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            damage_logits, _ = model(inputs)
            _, preds = torch.max(damage_logits, 1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    report = classification_report(all_labels, all_preds, target_names=class_names, digits=4)
    print("\nClassification Report:")
    print("-" * 60)
    print(report)

    cm = confusion_matrix(all_labels, all_preds)
    cm_normalized = cm.astype('float') / (cm.sum(axis=1)[:, np.newaxis] + 1e-8)

    plt.figure(figsize=(7, 5.5))
    sns.heatmap(
        cm_normalized, 
        annot=True, 
        fmt=".1%", 
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar=True
    )
    plt.title("Normalized Confusion Matrix — Real-World Car Damage", fontsize=11, fontweight='bold')
    plt.xlabel("Predicted Category", fontsize=9)
    plt.ylabel("Ground Truth Category", fontsize=9)
    plt.xticks(rotation=35, ha="right", fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()

    out_cm_path = str(CURR_DIR / "confusion_matrix.png")
    plt.savefig(out_cm_path, dpi=300)
    plt.close()
    print(f"[Confusion Matrix Saved] Saved plot to: {out_cm_path}")

    macro_f1 = f1_score(all_labels, all_preds, average='macro')
    print(f"Overall Macro F1-Score: {macro_f1:.4f}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AutoInspect AI Damage Classifier")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR), help="Path to car damage dataset")
    parser.add_argument("--weights_path", type=str, default=str(MODEL_WEIGHTS_PATH), help="Path to model weights")
    args = parser.parse_args()

    evaluate_model(weights_path=args.weights_path, data_dir=args.data_dir)
