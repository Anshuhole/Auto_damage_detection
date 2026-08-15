import json
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime
from app.database import Base

class InspectionRecord(Base):
    __tablename__ = "inspections"

    id = Column(String, primary_key=True, index=True)
    image_filename = Column(String, nullable=False)
    original_image_url = Column(String, nullable=False)
    gradcam_image_url = Column(String, nullable=False)
    has_damage = Column(Boolean, default=True)
    damage_type = Column(String, nullable=False)
    damage_display_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities_json = Column(Text, default="{}")
    estimated_cost_min = Column(Float, default=0.0)
    estimated_cost_max = Column(Float, default=0.0)
    repair_details_json = Column(Text, default="{}")
    bounding_box_json = Column(Text, default="[]")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "image_filename": self.image_filename,
            "original_image_url": self.original_image_url,
            "gradcam_image_url": self.gradcam_image_url,
            "has_damage": self.has_damage,
            "damage_type": self.damage_type,
            "damage_display_name": self.damage_display_name,
            "severity": self.severity,
            "confidence": round(self.confidence, 4),
            "probabilities": json.loads(self.probabilities_json or "{}"),
            "estimated_cost": {
                "min": self.estimated_cost_min,
                "max": self.estimated_cost_max,
                "currency": "USD",
                "details": json.loads(self.repair_details_json or "{}")
            },
            "bounding_boxes": json.loads(self.bounding_box_json or "[]"),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
