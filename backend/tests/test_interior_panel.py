import cv2
import numpy as np
from pathlib import Path

def test_panel_interior_damage(img_path):
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]

    # 1. Focus on vehicle interior door/fender panel zone (middle 60% vertical, middle 70% horizontal)
    panel_roi = img[int(h*0.25):int(h*0.75), int(w*0.15):int(w*0.85)]
    ph, pw = panel_roi.shape[:2]

    gray_roi = cv2.cvtColor(panel_roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_roi, (25, 25), 0)
    diff = np.abs(gray_roi.astype(np.float32) - blurred.astype(np.float32))

    # Detect irregular metal deformation / sharp tear
    irregular_anomaly = diff > 40.0
    anomaly_ratio = float(np.mean(irregular_anomaly))

    # Morphological cluster size
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(np.uint8(irregular_anomaly * 255), cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    max_cluster_area = max([cv2.contourArea(c) for c in contours], default=0)
    cluster_ratio = max_cluster_area / (ph * pw + 1e-5)

    print(f"Path: {Path(img_path).name:<25} | Anomaly: {anomaly_ratio:.4f}, Cluster Ratio: {cluster_ratio:.4f}")

    if cluster_ratio > 0.04 or anomaly_ratio > 0.12:
        print("  -> DAMAGE DETECTED ON PANEL")
    else:
        print("  -> NO DAMAGE (CLEAN PANEL)")

print("\n--- Testing Interior Panel Anomaly ---")
for cls in ['dent', 'scratch', 'crack', 'shattered_glass', 'no_damage']:
    folder = Path('ml_training/kaggle_car_damage_dataset/test') / cls
    images = list(folder.glob('*.*'))
    if images:
        test_panel_interior_damage(images[0])
