import io
import json
import uuid
from datetime import datetime
from PIL import Image
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InspectionRecord
from app.schemas import PredictionResponse, Base64PredictRequest
from app.ml.classifier import get_predictor
from app.utils.image_utils import decode_base64_image, save_inspection_images

router = APIRouter(prefix="/api", tags=["Prediction & Inspection"])

@router.post("/predict", response_model=PredictionResponse)
async def predict_damage_upload(
    file: UploadFile = File(...),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Analyzes an uploaded vehicle image: detects damage, classifies type,
    estimates severity, computes Grad-CAM visual heatmap, and estimates repair cost.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (JPEG, PNG, WEBP).")

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

    return _process_and_save_inspection(pil_image, filename=file.filename or "upload.jpg", notes=notes, db=db)


@router.post("/predict/base64", response_model=PredictionResponse)
async def predict_damage_base64(
    request: Base64PredictRequest,
    db: Session = Depends(get_db)
):
    """
    Analyzes a base64 encoded image captured directly from a webcam.
    """
    try:
        pil_image = decode_base64_image(request.image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode base64 image: {str(e)}")

    return _process_and_save_inspection(
        pil_image, 
        filename=request.filename or "webcam_capture.jpg", 
        notes=request.notes, 
        db=db
    )


def _process_and_save_inspection(pil_image: Image.Image, filename: str, notes: str, db: Session) -> dict:
    predictor = get_predictor()
    
    # 1. Run Deep Learning & Grad-CAM pipeline
    result = predictor.predict(pil_image, filename=filename)

    # 2. Generate unique Inspection ID
    today_str = datetime.utcnow().strftime("%Y%m%d")
    short_hash = uuid.uuid4().hex[:6].upper()
    inspection_id = f"INSP-{today_str}-{short_hash}"

    # 3. Save original image and Grad-CAM overlay to static directory
    orig_filename, orig_path, orig_url, gradcam_url = save_inspection_images(
        original_img=pil_image,
        gradcam_img=result["gradcam_pil"],
        prefix=inspection_id
    )

    # 4. Save record to Database
    record = InspectionRecord(
        id=inspection_id,
        image_filename=filename,
        original_image_url=orig_url,
        gradcam_image_url=gradcam_url,
        has_damage=result["has_damage"],
        damage_type=result["damage_type"],
        damage_display_name=result["damage_display_name"],
        severity=result["severity"],
        confidence=result["confidence"],
        probabilities_json=json.dumps(result["probabilities"]),
        estimated_cost_min=result["estimated_cost"]["min"],
        estimated_cost_max=result["estimated_cost"]["max"],
        repair_details_json=json.dumps(result["estimated_cost"]["details"]),
        bounding_box_json=json.dumps(result["bounding_boxes"]),
        notes=notes,
        created_at=datetime.utcnow()
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "image_filename": record.image_filename,
        "original_image_url": record.original_image_url,
        "gradcam_image_url": record.gradcam_image_url,
        "has_damage": record.has_damage,
        "damage_type": record.damage_type,
        "damage_display_name": record.damage_display_name,
        "severity": record.severity,
        "confidence": record.confidence,
        "probabilities": result["probabilities"],
        "estimated_cost": result["estimated_cost"],
        "bounding_boxes": result["bounding_boxes"],
        "notes": record.notes,
        "created_at": record.created_at.isoformat()
    }
