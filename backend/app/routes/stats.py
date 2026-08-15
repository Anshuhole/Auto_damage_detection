from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InspectionRecord
from app.schemas import StatsResponse
from app.config import DAMAGE_CLASSES, SEVERITY_LEVELS

router = APIRouter(prefix="/api/stats", tags=["Analytics & KPIs"])

@router.get("", response_model=StatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Computes aggregated analytics metrics for the inspector dashboard.
    """
    records = db.query(InspectionRecord).all()
    total = len(records)

    if total == 0:
        return StatsResponse(
            total_inspections=0,
            damaged_count=0,
            clean_count=0,
            damage_rate_percentage=0.0,
            avg_estimated_cost=0.0,
            damage_distribution={k: 0 for k in DAMAGE_CLASSES},
            severity_distribution={k: 0 for k in SEVERITY_LEVELS}
        )

    damaged_count = sum(1 for r in records if r.has_damage)
    clean_count = total - damaged_count
    damage_rate = round((damaged_count / total) * 100, 1)

    costs = [(r.estimated_cost_min + r.estimated_cost_max) / 2.0 for r in records if r.has_damage]
    avg_cost = round(sum(costs) / len(costs), 2) if costs else 0.0

    damage_counts = Counter(r.damage_type for r in records)
    severity_counts = Counter(r.severity for r in records)

    damage_dist = {cls_name: damage_counts.get(cls_name, 0) for cls_name in DAMAGE_CLASSES}
    severity_dist = {sev: severity_counts.get(sev, 0) for sev in SEVERITY_LEVELS}

    return StatsResponse(
        total_inspections=total,
        damaged_count=damaged_count,
        clean_count=clean_count,
        damage_rate_percentage=damage_rate,
        avg_estimated_cost=avg_cost,
        damage_distribution=damage_dist,
        severity_distribution=severity_dist
    )
