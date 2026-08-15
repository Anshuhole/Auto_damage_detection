import os
import sys
from pathlib import Path

CURR_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURR_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api():
    print("\n========================================================")
    print("        AutoInspect AI — Full API Test Suite            ")
    print("========================================================")

    print("\n--- 1. Testing Health Endpoint ---")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("Health Status:", res.json())

    print("\n--- 2. Testing /api/predict (File Upload) ---")
    sample_img = Path("backend/static/samples/sample_dent.jpeg")
    assert sample_img.exists(), "Sample test image not found"

    with open(sample_img, "rb") as f:
        files = {"file": (sample_img.name, f, "image/jpeg")}
        data = {"notes": "Test automated inspection verification"}
        res = client.post("/api/predict", files=files, data=data)

    assert res.status_code == 200, f"Predict failed: {res.text}"
    pred_data = res.json()
    print(f"Inspection ID       : {pred_data['id']}")
    print(f"Damage Detected     : {pred_data['damage_display_name']}")
    print(f"Severity Level      : {pred_data['severity']}")
    print(f"Confidence Score    : {pred_data['confidence'] * 100:.1f}%")
    print(f"Estimated Cost Range: ${pred_data['estimated_cost']['min']} - ${pred_data['estimated_cost']['max']} USD")
    print(f"Grad-CAM Image URL  : {pred_data['gradcam_image_url']}")

    insp_id = pred_data["id"]

    print("\n--- 3. Testing /api/history ---")
    res = client.get("/api/history")
    assert res.status_code == 200, f"History failed: {res.text}"
    history_data = res.json()
    print(f"Total History Records: {history_data['total']}")
    assert len(history_data["items"]) > 0

    print("\n--- 4. Testing /api/report/{id}/pdf ---")
    res = client.get(f"/api/report/{insp_id}/pdf")
    assert res.status_code == 200, f"PDF report failed: {res.text}"
    assert res.headers.get("content-type") == "application/pdf"
    print(f"PDF Generated Successfully! Size: {len(res.content)} bytes")

    print("\n--- 5. Testing /api/stats ---")
    res = client.get("/api/stats")
    assert res.status_code == 200, f"Stats failed: {res.text}"
    stats_data = res.json()
    print("Dashboard Stats:", stats_data)

    print("\n>>> ALL API TESTS PASSED PERFECTLY! <<<\n")

if __name__ == "__main__":
    test_api()
