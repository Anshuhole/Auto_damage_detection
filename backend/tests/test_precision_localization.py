import sys
from pathlib import Path
from PIL import Image

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.ml.classifier import get_predictor

def test_localization():
    print("\n========================================================")
    print("  Testing Precision Damage Localization on Real Cars    ")
    print("========================================================\n")

    predictor = get_predictor()
    kaggle_test_dir = Path(__file__).resolve().parent.parent.parent / "ml_training" / "kaggle_car_damage_dataset" / "test"

    for damage_type in ["dent", "scratch", "crack", "shattered_glass", "no_damage"]:
        folder = kaggle_test_dir / damage_type
        images = list(folder.glob("*.*"))
        if images:
            sample_img = images[0]
            pil_img = Image.open(sample_img)
            res = predictor.predict(pil_img)
            boxes = res["bounding_boxes"]
            print(f"Ground Truth : [{damage_type.upper()}]")
            print(f"  • Prediction     : {res['damage_display_name']}")
            print(f"  • Severity       : {res['severity'].upper()}")
            print(f"  • Confidence     : {res['confidence'] * 100:.1f}%")
            print(f"  • Bounding Boxes : {len(boxes)} localized regions")
            for i, box in enumerate(boxes):
                print(f"     [Box {i+1}] ({box['x']*100:.1f}%, {box['y']*100:.1f}%) size {box['width']*100:.1f}% x {box['height']*100:.1f}% (conf: {box['confidence']})")
            print()

if __name__ == "__main__":
    test_localization()
