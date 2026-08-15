import os
import random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CLASSES = ["scratch", "dent", "crack", "shattered_glass", "no_damage"]

def draw_synthetic_car(width=300, height=200, base_color=None):
    """Generates a realistic stylized base car silhouette and body panel."""
    if base_color is None:
        colors = [
            (35, 45, 60),    # Midnight Blue
            (180, 20, 20),   # Crimson Red
            (40, 40, 42),    # Charcoal
            (210, 215, 220), # Metallic Silver
            (240, 240, 245), # Glacier White
            (20, 75, 45),    # Racing Green
        ]
        base_color = random.choice(colors)

    img = Image.new("RGB", (width, height), (220, 225, 230))
    draw = ImageDraw.Draw(img)

    # Asphalt background / Ground shadow
    draw.rectangle([0, int(height * 0.72), width, height], fill=(65, 70, 75))
    draw.ellipse([int(width * 0.1), int(height * 0.7), int(width * 0.9), int(height * 0.85)], fill=(35, 40, 45))

    # Car Body Outline
    body_points = [
        (int(width * 0.12), int(height * 0.65)),
        (int(width * 0.15), int(height * 0.48)),
        (int(width * 0.28), int(height * 0.42)),
        (int(width * 0.42), int(height * 0.25)),
        (int(width * 0.68), int(height * 0.25)),
        (int(width * 0.82), int(height * 0.45)),
        (int(width * 0.88), int(height * 0.65)),
        (int(width * 0.12), int(height * 0.65)),
    ]
    draw.polygon(body_points, fill=base_color)

    # Cabin / Windows
    window_color = (25, 35, 45)
    cabin_points = [
        (int(width * 0.32), int(height * 0.42)),
        (int(width * 0.44), int(height * 0.28)),
        (int(width * 0.66), int(height * 0.28)),
        (int(width * 0.78), int(height * 0.42)),
    ]
    draw.polygon(cabin_points, fill=window_color)

    # Window divider
    draw.line([int(width * 0.52), int(height * 0.28), int(width * 0.52), int(height * 0.42)], fill=base_color, width=4)

    # Headlight & Taillight
    draw.ellipse([int(width * 0.13), int(height * 0.52), int(width * 0.18), int(height * 0.58)], fill=(255, 240, 150))
    draw.ellipse([int(width * 0.83), int(height * 0.52), int(width * 0.87), int(height * 0.58)], fill=(220, 30, 30))

    # Wheels
    wheel_radius = int(height * 0.15)
    for wx in [int(width * 0.25), int(width * 0.75)]:
        wy = int(height * 0.68)
        # Tire
        draw.ellipse([wx - wheel_radius, wy - wheel_radius, wx + wheel_radius, wy + wheel_radius], fill=(20, 20, 20))
        # Rim
        rim_r = int(wheel_radius * 0.55)
        draw.ellipse([wx - rim_r, wy - rim_r, wx + rim_r, wy + rim_r], fill=(180, 185, 190))

    return img

def apply_damage(img: Image.Image, damage_type: str) -> Image.Image:
    """Applies realistic visual damage artifacts according to damage classification."""
    if damage_type == "no_damage":
        return img

    cv_img = np.array(img)
    h, w, _ = cv_img.shape

    # Choose random damage center (biased towards car body)
    cx = random.randint(int(w * 0.25), int(w * 0.75))
    cy = random.randint(int(h * 0.35), int(h * 0.65))

    if damage_type == "scratch":
        # Multi-stroke sharp lines with white/grey highlight and dark shadow
        for _ in range(random.randint(3, 8)):
            sx = cx + random.randint(-30, 30)
            sy = cy + random.randint(-20, 20)
            ex = sx + random.randint(-60, 60)
            ey = sy + random.randint(-15, 25)
            cv2.line(cv_img, (sx, sy), (ex, ey), (230, 230, 235), random.randint(1, 3), cv2.LINE_AA)
            cv2.line(cv_img, (sx+1, sy+1), (ex+1, ey+1), (30, 30, 30), 1, cv2.LINE_AA)

    elif damage_type == "dent":
        # Radial gradient dark shadow & highlight distortion
        radius = random.randint(25, 45)
        overlay = cv_img.copy()
        cv2.circle(overlay, (cx, cy), radius, (20, 20, 25), -1)
        cv2.circle(overlay, (cx - 5, cy - 5), int(radius * 0.7), (200, 200, 210), 2)
        cv_img = cv2.addWeighted(cv_img, 0.6, overlay, 0.4, 0)

    elif damage_type == "crack":
        # Jagged fracture line with branching
        curr_x, curr_y = cx, cy
        for _ in range(random.randint(6, 12)):
            next_x = curr_x + random.randint(-15, 20)
            next_y = curr_y + random.randint(-10, 25)
            cv2.line(cv_img, (curr_x, curr_y), (next_x, next_y), (15, 15, 20), 2, cv2.LINE_AA)
            cv2.line(cv_img, (curr_x + 1, curr_y), (next_x + 1, next_y), (220, 220, 230), 1, cv2.LINE_AA)
            if random.random() > 0.6:
                branch_x = curr_x + random.randint(-15, 15)
                branch_y = curr_y + random.randint(5, 20)
                cv2.line(cv_img, (curr_x, curr_y), (branch_x, branch_y), (20, 20, 25), 1, cv2.LINE_AA)
            curr_x, curr_y = next_x, next_y

    elif damage_type == "shattered_glass":
        # Window/spiderweb glass shatter on cabin region
        cx_win = random.randint(int(w * 0.35), int(w * 0.65))
        cy_win = random.randint(int(h * 0.28), int(h * 0.40))
        num_rays = random.randint(10, 16)
        radius = random.randint(20, 40)
        for i in range(num_rays):
            angle = (2 * np.pi / num_rays) * i + random.uniform(-0.1, 0.1)
            ex = int(cx_win + radius * np.cos(angle))
            ey = int(cy_win + radius * np.sin(angle))
            cv2.line(cv_img, (cx_win, cy_win), (ex, ey), (240, 245, 255), 1, cv2.LINE_AA)
        for r in [int(radius * 0.3), int(radius * 0.6), radius]:
            cv2.circle(cv_img, (cx_win, cy_win), r, (220, 230, 245), 1, cv2.LINE_AA)

    return Image.fromarray(cv_img)

def generate_dataset(base_dir=DATA_DIR, samples_per_class_train=40, samples_per_class_val=10):
    """Generates the structured dataset splits."""
    splits = {
        "train": samples_per_class_train,
        "val": samples_per_class_val,
        "test": samples_per_class_val
    }

    for split_name, count in splits.items():
        for cls_name in CLASSES:
            folder = base_dir / split_name / cls_name
            folder.mkdir(parents=True, exist_ok=True)

            print(f"[Dataset Generator] Generating {count} images for split '{split_name}' -> class '{cls_name}'...")
            for i in range(count):
                base = draw_synthetic_car()
                damaged = apply_damage(base, cls_name)
                # Add minor noise / resize to 224x224
                resized = damaged.resize((224, 224), Image.Resampling.LANCZOS)
                out_path = folder / f"{cls_name}_{i:04d}.jpg"
                resized.save(out_path, quality=90)

    print(f"\n[Dataset Generator] Successfully generated full synthetic dataset in: {base_dir}")

if __name__ == "__main__":
    generate_dataset()
