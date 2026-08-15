import cv2
import numpy as np
from pathlib import Path

def test_crop_and_saliency(img_path):
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]

    # 1. Remove black letterbox padding if present
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    non_black = gray > 15
    rows = np.any(non_black, axis=1)
    cols = np.any(non_black, axis=0)
    
    if np.any(rows) and np.any(cols):
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
    else:
        rmin, rmax, cmin, cmax = 0, h-1, 0, w-1

    crop = img[rmin:rmax+1, cmin:cmax+1]
    ch, cw = crop.shape[:2]
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # 2. Car body mask (ignoring sky and extreme ground)
    car_mask = np.ones((ch, cw), dtype=np.uint8)
    # Suppress top 15% (sky/buildings) and bottom 8% (road edge)
    car_mask[:int(ch*0.12), :] = 0
    car_mask[int(ch*0.92):, :] = 0

    # 3. Compute surface defect anomaly (crumple/dent/scratch/crack)
    blurred = cv2.GaussianBlur(crop_gray, (35, 35), 0)
    residual = np.abs(crop_gray.astype(np.float32) - blurred.astype(np.float32))
    residual *= (car_mask > 0)

    # Local anomaly peak
    peak_val = np.percentile(residual[car_mask > 0], 98)
    damage_score = float(np.mean(residual > 28.0))

    print(f"Path: {Path(img_path).name:<25} -> Letterbox Crop: ({cmin},{rmin}) to ({cmax},{rmax}) | Peak: {peak_val:.1f}, Damage Score: {damage_score:.4f}")

# Test on test images
for p in Path("ml_training/kaggle_car_damage_dataset/test").glob("*/*.*"):
    test_crop_and_saliency(p)
    break
