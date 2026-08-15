import cv2
import numpy as np
from pathlib import Path

def test_paint_damage_saliency(img_path):
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]

    # Convert to LAB / HSV color space to decouple paint color from illumination
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)

    # Focus on middle vehicle paint body (middle 45% vertical, middle 70% horizontal)
    # This completely avoids tires (bottom 25%) and roof/sky (top 20%)
    paint_roi = l_chan[int(h*0.22):int(h*0.68), int(w*0.15):int(w*0.85)]
    ph, pw = paint_roi.shape[:2]

    # Local texture deviation on paint
    blurred_l = cv2.GaussianBlur(paint_roi, (25, 25), 0)
    paint_defect = np.abs(paint_roi.astype(np.float32) - blurred_l.astype(np.float32))

    # Genuine damage creates high local variance spikes (> 45 on L channel)
    damage_spikes = paint_defect > 42.0
    spike_density = float(np.mean(damage_spikes))

    # Cluster detection
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    closed = cv2.morphologyEx(np.uint8(damage_spikes * 255), cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    max_area = max([cv2.contourArea(c) for c in contours], default=0)
    cluster_pct = (max_area / (ph * pw + 1e-5)) * 100.0

    print(f"File: {Path(img_path).name:<25} | Spike Density: {spike_density:.4f}, Largest Cluster: {cluster_pct:.1f}%")

    if cluster_pct > 3.5 or spike_density > 0.08:
        print("  >>> [DAMAGE DETECTED]")
    else:
        print("  >>> [CLEAN CAR / NO DAMAGE]")

print("\n--- Testing Paint Damage Saliency ---")
for cls in ['dent', 'scratch', 'crack', 'shattered_glass', 'no_damage']:
    folder = Path('ml_training/kaggle_car_damage_dataset/test') / cls
    images = list(folder.glob('*.*'))
    if images:
        test_paint_damage_saliency(images[0])
