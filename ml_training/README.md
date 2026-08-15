# AutoInspect AI — Machine Learning Pipeline & Training Guide

This directory contains the complete PyTorch training, evaluation, and visual explainability (Grad-CAM) pipeline for **AutoInspect AI**.

---

## 1. Machine Learning Architecture Overview

```
+---------------------+      +-----------------------------+      +-------------------------------+
|  Input Image (RGB)  | ---> |  ResNet50 Backbone (Layer4) | ---> | Shared FC (512, Dropout=0.35) |
|      (224x224)      |      |  (ImageNet Pre-trained)     |      +---------------+---------------+
+---------------------+      +-----------------------------+                      |
                                            |                                     v
                                            v                     +-------------------------------+
                             +-----------------------------+      | Head 1: Damage Classification |
                             |   Grad-CAM Backward Hook    |      | (Scratch, Dent, Crack, Glass, |
                             | (Target Conv: layer4[-1])   |      |  Clean) - Softmax Probabilities|
                             +--------------+--------------+      +-------------------------------+
                                            |                                     v
                                            v                     +-------------------------------+
                             +-----------------------------+      | Head 2: Severity Estimation   |
                             | Normalized Activation Heatmap|     | (Minor, Moderate, Severe,     |
                             |  + Contour Bounding Boxes   |      |  None)                        |
                             +-----------------------------+      +-------------------------------+
```

### Key Technical Highlights
- **Convolutional Backbone**: Deep Residual Network (`ResNet50`) with 2048-dimensional feature representations.
- **Transfer Learning Strategy**: We freeze early low-level feature extraction stages and fine-tune high-level bottleneck blocks (`layer4`) along with custom classification heads.
- **Loss Formulation**: Weighted Multi-Class Cross-Entropy Loss to handle class imbalances across damage severities.
- **Optimizer & Scheduler**: `AdamW` (learning rate: `1e-4`, weight decay: `1e-4`) with a `CosineAnnealingLR` decay schedule.
- **Explainability**: Gradient-weighted Class Activation Mapping (Grad-CAM) computes gradient flow from the target classification node back to the final convolutional feature maps.

---

## 2. Dataset Preparation

### Option A: Immediate Out-of-the-Box Synthetic Dataset
To train or test immediately without downloading external datasets, run:
```bash
python generate_synthetic_data.py
```
This generates 300+ synthetic vehicle panels with realistic scratch strokes, dent gradients, panel cracks, and glass fractures organized into `data/train/`, `data/val/`, and `data/test/`.

### Option B: Kaggle Real-World Car Damage Datasets
You can download and drop any public Kaggle car damage dataset into `ml_training/data/`:
1. **[Car Damage Detection Dataset (Kaggle)](https://www.kaggle.com/datasets/anujms/car-damage-detection)**
2. **[Vehicle Damage Insurance Claim Dataset (Kaggle)](https://www.kaggle.com/datasets/arunrk7/car-damage-dataset)**
3. **[Cardd: Car Damage Dataset](https://cardd-ust.github.io/)**

Ensure your dataset is organized in standard PyTorch ImageFolder structure:
```
data/
├── train/
│   ├── scratch/
│   ├── dent/
│   ├── crack/
│   ├── shattered_glass/
│   └── no_damage/
├── val/
│   ├── scratch/
│   ├── dent/
│   ...
└── test/
    ├── scratch/
    ├── dent/
    ...
```

---

## 3. Training the Model

Execute the training script:
```bash
python train.py --epochs 10 --batch_size 16 --lr 0.0001
```

During training, the script will:
1. Apply online data augmentations (Random Horizontal Flip, Color Jitter, Rotation).
2. Compute loss and accuracy on training and validation splits.
3. Automatically checkpoint the best weights to `../backend/app/ml/weights/car_damage_resnet50.pth`.
4. Generate `training_history.png` containing loss and accuracy convergence curves.

---

## 4. Model Evaluation & Metrics

To generate confusion matrices, classification reports (Precision, Recall, F1), and test accuracy:
```bash
python evaluate.py
```

Outputs:
- **Classification Report**: Precision, Recall, F1-Score per class.
- **Confusion Matrix**: Saved as `confusion_matrix.png`.
- **Macro F1-Score**: Overall multi-class performance benchmark.

---

## 5. Interactive Jupyter Notebook

For step-by-step exploration, live plots, and Grad-CAM visualizations:
```bash
jupyter notebook model_training.ipynb
```
