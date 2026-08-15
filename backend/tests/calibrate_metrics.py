import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def analyze_damage(cv_img_bgr):
    gray = cv2.cvtColor(cv_img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 1. High-frequency edge map
    edges = cv2.Canny(gray, 80, 200)
    sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(sobelx**2 + sobely**2)

    # 2. Line detection with high threshold
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=60, minLineLength=40, maxLineGap=6)
    num_long_lines = len(lines) if lines is not None else 0

    # 3. Dent shadow & lighting depression
    blurred = cv2.GaussianBlur(gray, (45, 45), 0)
    shadow_diff = np.abs(gray.astype(np.float32) - blurred.astype(np.float32))
    dent_depression_score = float(np.mean(shadow_diff > 35.0))

    # 4. Glass radial fracture detection
    center_cabin = edges[int(h*0.2):int(h*0.6), int(w*0.25):int(w*0.75)]
    cabin_edge_density = float(np.mean(center_cabin > 0)) if center_cabin.size > 0 else 0.0

    # 5. Clean surface reflection
    clean_surface_uniformity = float(np.mean(grad_mag < 25.0))

    print(f"Metrics: long_lines={num_long_lines}, dent_dep={dent_depression_score:.4f}, cabin_edges={cabin_edge_density:.4f}, clean_unif={clean_surface_uniformity:.4f}")

kaggle_test_dir = Path("ml_training/kaggle_car_damage_dataset/test")
for damage_type in ["dent", "scratch", "crack", "shattered_glass", "no_damage"]:
    images = list((kaggle_test_dir / damage_type).glob("*.*"))
    if images:
        img = cv2.imread(str(images[0]))
        print(f"\n--- Testing Category: {damage_type.upper()} ---")
        analyze_damage(img)
