import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import InspectionRecord
from app.schemas import HistoryResponse, HistoryItem, PredictionResponse
from app.config import BASE_DIR

router = APIRouter(prefix="/api/history", tags=["Inspection History"])

@router.get("", response_model=HistoryResponse)
def get_inspection_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    damage_type: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of past vehicle inspections with optional filtering.
    """
    query = db.query(InspectionRecord)

    if damage_type and damage_type != "all":
        query = query.filter(InspectionRecord.damage_type == damage_type)

    if severity and severity != "all":
        query = query.filter(InspectionRecord.severity == severity)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (InspectionRecord.id.ilike(search_pattern)) | 
            (InspectionRecord.image_filename.ilike(search_pattern)) |
            (InspectionRecord.damage_display_name.ilike(search_pattern))
        )

    total_count = query.count()
    records = query.order_by(desc(InspectionRecord.created_at)).offset(offset).limit(limit).all()

    items = []
    for r in records:
        d = r.to_dict()
        items.append(HistoryItem(
            id=d["id"],
            image_filename=d["image_filename"],
            original_image_url=d["original_image_url"],
            gradcam_image_url=d["gradcam_image_url"],
            has_damage=d["has_damage"],
            damage_type=d["damage_type"],
            damage_display_name=d["damage_display_name"],
            severity=d["severity"],
            confidence=d["confidence"],
            estimated_cost=d["estimated_cost"],
            created_at=d["created_at"]
        ))

    return HistoryResponse(total=total_count, items=items)


@router.get("/{inspection_id}")
def get_inspection_by_id(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full details for a single inspection by its ID.
    """
    record = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    return record.to_dict()


@router.delete("/{inspection_id}")
def delete_inspection(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """
    Deletes an inspection record and removes its associated image files.
    """
    record = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    # Try removing local image files
    for url_field in [record.original_image_url, record.gradcam_image_url]:
        if url_field:
            local_path = os.path.join(BASE_DIR, url_field.lstrip("/").replace("/", os.sep))
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception:
                    pass

    db.delete(record)
    db.commit()

    return {"message": "Inspection deleted successfully", "id": inspection_id}
