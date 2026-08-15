import cv2
import numpy as np
from pathlib import Path

def test_bilateral_saliency(img_path):
    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]

    # Bilateral filter removes JPEG compression blocking noise
    filtered = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
    gray_f = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)

    # Large scale Gaussian blur to capture true geometric panel shape
    blurred = cv2.GaussianBlur(gray_f, (45, 45), 0)
    structural_defect = np.abs(gray_f.astype(np.float32) - blurred.astype(np.float32))

    # Mask out outer margins
    margin_mask = np.zeros((h, w), dtype=np.float32)
    margin_mask[int(h*0.12):int(h*0.88), int(w*0.06):int(w*0.94)] = 1.0
    structural_defect *= margin_mask

    defect_score = float(np.mean(structural_defect[margin_mask > 0] > 30.0))
    peak_defect = float(np.percentile(structural_defect[margin_mask > 0], 98))

    print(f"Path: {Path(img_path).name:<25} | Defect Score: {defect_score:.4f}, Peak: {peak_defect:.1f}")

print("\n--- Testing Bilateral Filter on All Classes ---")
for cls in ['dent', 'scratch', 'crack', 'shattered_glass', 'no_damage']:
    folder = Path('ml_training/kaggle_car_damage_dataset/test') / cls
    images = list(folder.glob('*.*'))
    if images:
        test_bilateral_saliency(images[0])
