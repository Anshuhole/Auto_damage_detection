import os
import sys
import shutil
import random
import urllib.request
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

CURR_DIR = Path(__file__).resolve().parent
TARGET_DATA_DIR = CURR_DIR / "real_dataset"
KAGGLE_SOURCE_DIR = Path(r"C:\Users\VISHNU\.cache\kagglehub\datasets\anujms\car-damage-detection\versions\1\data1a")

CLASSES = ["scratch", "dent", "crack", "shattered_glass", "no_damage"]

def setup_directories():
    if TARGET_DATA_DIR.exists():
        shutil.rmtree(TARGET_DATA_DIR)
    for split in ["train", "val", "test"]:
        for cls_name in CLASSES:
            (TARGET_DATA_DIR / split / cls_name).mkdir(parents=True, exist_ok=True)

def categorize_real_damage(cv_img_bgr: np.ndarray) -> str:
    h, w = cv_img_bgr.shape[:2]
    gray = cv2.cvtColor(cv_img_bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(cv_img_bgr, cv2.COLOR_BGR2HSV)
    _, s_ch, v_ch = cv2.split(hsv)
    
    # 1. Non-paint / tire suppression
    tire_mask = (s_ch < 55) & (v_ch < 95)
    tire_dilated = cv2.dilate(tire_mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    paint_mask = (tire_dilated == 0).astype(np.float32)
    
    margin_y = max(4, int(h * 0.02))
    margin_x = max(4, int(w * 0.02))
    paint_mask[:margin_y, :] = 0
    paint_mask[-margin_y:, :] = 0
    paint_mask[:, :margin_x] = 0
    paint_mask[:, -margin_x:] = 0
    
    paint_area = float(np.sum(paint_mask > 0)) + 1e-5
    
    # 2. Glass region (windshield / window mesh)
    glass_roi = gray[int(h*0.10):int(h*0.50), int(w*0.20):int(w*0.80)]
    glass_edges = cv2.Canny(glass_roi, 80, 200) if glass_roi.size > 0 else np.zeros((1, 1))
    glass_density = float(np.mean(glass_edges > 0))
    
    # 3. Scratch & Paint Abrasion Energy (Multi-scale TopHat & BlackHat)
    k1 = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
    k2 = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    tophat = cv2.max(cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, k1), cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, k2))
    blackhat = cv2.max(cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k1), cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k2))
    scratch_raw = cv2.max(tophat, blackhat).astype(np.float32)
    scratch_map = scratch_raw * paint_mask
    scratch_energy = float(np.sum(scratch_map > 22.0) / paint_area)
    scratch_peak = float(np.percentile(scratch_map[paint_mask > 0], 98)) if np.any(paint_mask > 0) else 0.0
    
    # 4. Surface curvature & dent shadow depth
    blur = cv2.GaussianBlur(gray, (45, 45), 0)
    dent_raw = cv2.absdiff(gray, blur).astype(np.float32)
    dent_map = dent_raw * paint_mask
    dent_energy = float(np.sum(dent_map > 30.0) / paint_area)
    dent_peak = float(np.percentile(dent_map[paint_mask > 0], 98)) if np.any(paint_mask > 0) else 0.0
    
    # 5. Linear scuffs & cracks
    edges = cv2.Canny(gray, 45, 140)
    edges_paint = edges * paint_mask.astype(np.uint8)
    edge_density = float(np.sum(edges_paint > 0) / paint_area)
    
    if glass_density > 0.20 and edge_density > 0.08:
        return "shattered_glass"
    elif scratch_energy > 0.12 or (scratch_energy > 0.05 and scratch_peak > 55.0):
        return "scratch"
    elif dent_energy > 0.10 or dent_peak > 65.0:
        return "dent"
    elif edge_density > 0.06:
        return "crack"
    elif scratch_energy > 0.03:
        return "scratch"
    else:
        return "dent"

def augment_image(pil_img: Image.Image, method: int) -> Image.Image:
    if method == 0:
        return pil_img.transpose(Image.FLIP_LEFT_RIGHT)
    elif method == 1:
        enhancer = ImageEnhance.Brightness(pil_img)
        return enhancer.enhance(random.uniform(0.85, 1.18))
    elif method == 2:
        enhancer = ImageEnhance.Contrast(pil_img)
        return enhancer.enhance(random.uniform(0.88, 1.22))
    elif method == 3:
        enhancer = ImageEnhance.Color(pil_img)
        return enhancer.enhance(random.uniform(0.88, 1.15))
    elif method == 4:
        return pil_img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.7)))
    else:
        return pil_img.rotate(random.choice([-5, -2, 2, 5]), resample=Image.BICUBIC, fillcolor=(128, 128, 128))

def build_dataset():
    print("==========================================================")
    print("  Building Balanced Real-World Automotive Damage Dataset  ")
    print("==========================================================")
    setup_directories()
    
    if not KAGGLE_SOURCE_DIR.exists():
        print(f"Error: {KAGGLE_SOURCE_DIR} not found.")
        return
        
    # 1. Whole / Pristine Clean Cars
    clean_imgs = list((KAGGLE_SOURCE_DIR / "training" / "01-whole").glob("*.*")) + \
                 list((KAGGLE_SOURCE_DIR / "validation" / "01-whole").glob("*.*"))
    random.seed(42)
    random.shuffle(clean_imgs)
    
    print(f"Processing {len(clean_imgs)} real pristine car photos...")
    for idx, img_p in enumerate(clean_imgs[:450]):
        split = "train" if idx < 320 else ("val" if idx < 385 else "test")
        dest = TARGET_DATA_DIR / split / "no_damage" / f"real_clean_{idx:04d}{img_p.suffix.lower()}"
        shutil.copy2(img_p, dest)
        
    # 2. Damaged Cars
    damage_imgs = list((KAGGLE_SOURCE_DIR / "training" / "00-damage").glob("*.*")) + \
                  list((KAGGLE_SOURCE_DIR / "validation" / "00-damage").glob("*.*"))
    random.shuffle(damage_imgs)
    
    categorized = {"scratch": [], "dent": [], "crack": [], "shattered_glass": []}
    
    print(f"Analyzing {len(damage_imgs)} real damage photographs...")
    for img_p in damage_imgs:
        cv_img = cv2.imread(str(img_p))
        if cv_img is None:
            continue
        cat = categorize_real_damage(cv_img)
        categorized[cat].append(img_p)
        
    print("\nCategorization Counts:")
    for k, v in categorized.items():
        print(f"  {k}: {len(v)} images")
        
    # Target 300 samples in train for each damage class
    target_train_count = 300
    for cat, img_list in categorized.items():
        if not img_list:
            continue
        random.shuffle(img_list)
        val_count = max(25, int(len(img_list) * 0.12))
        test_count = max(20, int(len(img_list) * 0.08))
        train_list = img_list[:max(1, len(img_list) - val_count - test_count)]
        val_list = img_list[len(train_list):len(train_list) + val_count]
        test_list = img_list[len(train_list) + val_count:]
        
        # Save validation
        for i, p in enumerate(val_list):
            shutil.copy2(p, TARGET_DATA_DIR / "val" / cat / f"val_{cat}_{i:04d}{p.suffix.lower()}")
        # Save test
        for i, p in enumerate(test_list):
            shutil.copy2(p, TARGET_DATA_DIR / "test" / cat / f"test_{cat}_{i:04d}{p.suffix.lower()}")
            
        # Save train
        saved_train = 0
        for i, p in enumerate(train_list):
            shutil.copy2(p, TARGET_DATA_DIR / "train" / cat / f"train_{cat}_{saved_train:04d}{p.suffix.lower()}")
            saved_train += 1
            
        # Augment to target_train_count
        aug_idx = 0
        while saved_train < target_train_count and len(train_list) > 0:
            src_p = train_list[aug_idx % len(train_list)]
            try:
                with Image.open(src_p) as pil_img:
                    pil_img = pil_img.convert("RGB")
                    aug_img = augment_image(pil_img, aug_idx % 6)
                    aug_dest = TARGET_DATA_DIR / "train" / cat / f"train_aug_{cat}_{saved_train:04d}.jpg"
                    aug_img.save(aug_dest, quality=92)
                    saved_train += 1
            except Exception:
                pass
            aug_idx += 1

    print("\nFinal Balanced Dataset Summary:")
    print("=" * 60)
    for split in ["train", "val", "test"]:
        counts = {c: len(list((TARGET_DATA_DIR / split / c).glob("*.*"))) for c in CLASSES}
        print(f"  {split.upper():<6}: {counts} (Total: {sum(counts.values())})")

if __name__ == "__main__":
    build_dataset()
