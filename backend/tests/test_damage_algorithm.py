import cv2
import numpy as np
from pathlib import Path
from PIL import Image

def analyze_and_localize_damage(img_path):
    orig = cv2.imread(str(img_path))
    h, w = orig.shape[:2]

    # 1. Strip black letterbox bars
    gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
    non_black = gray > 20
    rows = np.any(non_black, axis=1)
    cols = np.any(non_black, axis=0)

    if np.any(rows) and np.any(cols):
        rmin, rmax = int(np.where(rows)[0][0]), int(np.where(rows)[0][-1])
        cmin, cmax = int(np.where(cols)[0][0]), int(np.where(cols)[0][-1])
    else:
        rmin, rmax, cmin, cmax = 0, h - 1, 0, w - 1

    crop = orig[rmin:rmax+1, cmin:cmax+1]
    ch, cw = crop.shape[:2]
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # 2. Panel mask: ignore sky (top 15%), road (bottom 10%), extreme sides
    panel_mask = np.zeros((ch, cw), dtype=np.uint8)
    panel_mask[int(ch * 0.15):int(ch * 0.88), int(cw * 0.05):int(cw * 0.95)] = 255

    # 3. Surface curvature & defect anomaly
    blurred = cv2.GaussianBlur(crop_gray, (31, 31), 0)
    residual = np.abs(crop_gray.astype(np.float32) - blurred.astype(np.float32))
    residual *= (panel_mask > 0)

    # Focus on true localized anomalies
    valid_res = residual[panel_mask > 0]
    peak_res = float(np.percentile(valid_res, 98)) if len(valid_res) > 0 else 0.0
    defect_density = float(np.mean(valid_res > 32.0)) if len(valid_res) > 0 else 0.0

    print(f"File: {Path(img_path).name:<25} | Peak Anomaly: {peak_res:.1f}, Density: {defect_density:.4f}")

    if defect_density < 0.08 or peak_res < 60.0:
        print("  -> Classification: NO DAMAGE (Pristine Car) | Boxes: 0")
    else:
        # Find the primary damaged panel cluster
        _, thresh = cv2.threshold(np.uint8(residual), int(peak_res * 0.65), 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        if contours:
            x, y, bw, bh = cv2.boundingRect(contours[0])
            # Map back to full image canvas
            bx = (cmin + x) / w
            by = (rmin + y) / h
            bwidth = bw / w
            bheight = bh / h
            print(f"  -> Classification: DAMAGE DETECTED | Box: x={bx*100:.1f}%, y={by*100:.1f}%, size={bwidth*100:.1f}%x{bheight*100:.1f}%")

print("\n--- Testing on Real Images ---")
for p in Path("ml_training/kaggle_car_damage_dataset/test").glob("*/*.*"):
    analyze_and_localize_damage(p)
    break
