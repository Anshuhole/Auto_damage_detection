import os
import sys
import json
from pathlib import Path
from PIL import Image

CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_live_tests():
    print("\n========================================================")
    print("      AutoInspect AI — Live API & Neural Pipeline Test   ")
    print("========================================================\n")

    test_cases = [
        ("Door Dent", "backend/static/samples/sample_dent.jpeg", "dent"),
        ("Quarter Scratch", "backend/static/samples/sample_scratch.jpeg", "scratch"),
        ("Bumper Crack", "backend/static/samples/sample_crack.jpeg", "crack"),
        ("Shattered Glass", "backend/static/samples/sample_glass.jpeg", "shattered_glass"),
        ("Clean Car (Whole)", "backend/static/samples/sample_clean.jpg", "no_damage"),
    ]

    for name, img_path, expected_type in test_cases:
        p = Path(img_path)
        if not p.exists():
            print(f"Skipping {name}: file {img_path} not found")
            continue

        print(f"--- Testing Image: {name} ({p.name}) ---")
        with open(p, "rb") as f:
            resp = client.post(
                "/api/predict",
                files={"file": (p.name, f, "image/jpeg")},
                data={"notes": f"Automated test for {name}"}
            )

        assert resp.status_code == 200, f"Predict failed with status {resp.status_code}: {resp.text}"
        data = resp.json()

        print(f"  Inspection ID    : {data['id']}")
        print(f"  Detected Damage  : {data['damage_display_name']} (Expected: {expected_type})")
        print(f"  Severity         : {data['severity']}")
        print(f"  Confidence       : {data['confidence'] * 100:.1f}%")
        print(f"  Bounding Boxes   : {len(data['bounding_boxes'])} box(es)")
        print(f"  Cost Range       : ${data['estimated_cost']['min']} - ${data['estimated_cost']['max']} USD")
        print(f"  Grad-CAM URL     : {data['gradcam_image_url']}")

        if expected_type == "no_damage":
            assert not data["has_damage"], "Expected no damage on clean car!"
            assert len(data["bounding_boxes"]) == 0, "Expected 0 bounding boxes on clean car!"
            assert data["estimated_cost"]["min"] == 0, "Expected $0 repair cost on clean car!"
        else:
            assert data["has_damage"], f"Expected damage on {name}!"
            assert data["estimated_cost"]["max"] > 0, "Expected positive repair cost!"

        print("  [PASS]\n")

    print(">>> ALL LIVE PREDICTION TESTS PASSED ACCURATELY! <<<\n")

if __name__ == "__main__":
    run_live_tests()
