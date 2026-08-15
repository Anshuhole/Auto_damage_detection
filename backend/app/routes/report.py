import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InspectionRecord
from app.utils.pdf_generator import generate_pdf_report

router = APIRouter(prefix="/api/report", tags=["PDF Reports"])

@router.get("/{inspection_id}/pdf")
def download_inspection_pdf(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates and returns an official downloadable PDF inspection report.
    """
    record = db.query(InspectionRecord).filter(InspectionRecord.id == inspection_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Inspection record not found.")

    inspection_dict = record.to_dict()

    try:
        pdf_path = generate_pdf_report(inspection_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Generated PDF report file could not be located.")

    filename = f"AutoInspect_Report_{inspection_id}.pdf"
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
