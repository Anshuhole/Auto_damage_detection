from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class CostDetails(BaseModel):
    labor_hours: float
    labor_cost: float
    paint_cost: float
    parts_cost: float
    action_summary: str

class EstimatedCost(BaseModel):
    min: float
    max: float
    currency: str = "USD"
    details: Optional[CostDetails] = None

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    label: str
    confidence: float

class PredictionResponse(BaseModel):
    id: str
    image_filename: str
    original_image_url: str
    gradcam_image_url: str
    has_damage: bool
    damage_type: str
    damage_display_name: str
    severity: str
    confidence: float
    probabilities: Dict[str, float]
    estimated_cost: EstimatedCost
    bounding_boxes: List[BoundingBox] = []
    notes: Optional[str] = None
    created_at: str

class Base64PredictRequest(BaseModel):
    image_base64: str
    filename: Optional[str] = "webcam_capture.jpg"
    notes: Optional[str] = None

class HistoryItem(BaseModel):
    id: str
    image_filename: str
    original_image_url: str
    gradcam_image_url: str
    has_damage: bool
    damage_type: str
    damage_display_name: str
    severity: str
    confidence: float
    estimated_cost: Dict[str, Any]
    created_at: str

class HistoryResponse(BaseModel):
    total: int
    items: List[HistoryItem]

class StatsResponse(BaseModel):
    total_inspections: int
    damaged_count: int
    clean_count: int
    damage_rate_percentage: float
    avg_estimated_cost: float
    damage_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
