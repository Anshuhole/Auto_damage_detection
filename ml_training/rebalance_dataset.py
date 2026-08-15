import random
import shutil
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent / "kaggle_car_damage_dataset"
CLASSES = ["scratch", "dent", "crack", "shattered_glass", "no_damage"]

def rebalance_splits(dataset_dir: Path = DATASET_DIR, train_ratio=0.75, val_ratio=0.15):
    random.seed(42)
    print("Rebalancing dataset splits for balanced training, validation, and testing...")

    # Collect all images per class from across all current subfolders
    class_images = {c: [] for c in CLASSES}
    for img_path in dataset_dir.glob("**/*.*"):
        if img_path.is_file() and img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            parent_name = img_path.parent.name.lower()
            for c in CLASSES:
                if c in parent_name or (c == "no_damage" and ("whole" in parent_name or "clean" in parent_name)):
                    class_images[c].append(img_path)
                    break

    # Temporary directory for clean redistribution
    temp_dir = dataset_dir.parent / "temp_kaggle_balanced"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    for split in ["train", "val", "test"]:
        for c in CLASSES:
            (temp_dir / split / c).mkdir(parents=True, exist_ok=True)

    for c, files in class_images.items():
        # Remove duplicates
        unique_files = list(set(files))
        random.shuffle(unique_files)
        
        n_total = len(unique_files)
        if n_total == 0:
            print(f"Warning: No images found for class {c}")
            continue

        n_train = max(1, int(n_total * train_ratio))
        n_val = max(1, int(n_total * val_ratio))
        
        train_files = unique_files[:n_train]
        val_files = unique_files[n_train:n_train + n_val]
        test_files = unique_files[n_train + n_val:]
        if not test_files:
            test_files = val_files[:max(1, len(val_files)//2)]

        for f in train_files:
            shutil.copy2(f, temp_dir / "train" / c / f.name)
        for f in val_files:
            shutil.copy2(f, temp_dir / "val" / c / f.name)
        for f in test_files:
            shutil.copy2(f, temp_dir / "test" / c / f.name)

    # Replace original dataset directory with balanced one
    shutil.rmtree(dataset_dir)
    shutil.move(str(temp_dir), str(dataset_dir))

    print("\n========================================================")
    print("  Kaggle Real-World Dataset Balanced Distribution       ")
    print("========================================================")
    for split in ["train", "val", "test"]:
        print(f" Split: [{split.upper()}]")
        for cls_folder in (dataset_dir / split).glob("*"):
            if cls_folder.is_dir():
                count = len(list(cls_folder.glob("*.*")))
                print(f"   • {cls_folder.name:<16}: {count} real photos")
    print("========================================================\n")

if __name__ == "__main__":
    rebalance_splits()
