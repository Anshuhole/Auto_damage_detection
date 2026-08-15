from typing import Dict, Any
from app.config import COST_ESTIMATE_MATRIX

LABOR_HOURLY_RATE = 95.0  # Standard auto body repair labor rate in USD

def estimate_repair_cost(damage_type: str, severity: str, confidence: float = 0.9) -> Dict[str, Any]:
    """
    Computes a realistic rule-based estimated repair cost range and itemized breakdown
    based on damage classification, severity level, and detection confidence.
    """
    damage_key = damage_type.lower()
    severity_key = severity.lower()

    if damage_key not in COST_ESTIMATE_MATRIX:
        damage_key = "scratch"

    damage_rules = COST_ESTIMATE_MATRIX[damage_key]

    if severity_key not in damage_rules:
        # Fallback to moderate if severity key not found for this damage type
        severity_key = list(damage_rules.keys())[0]

    rule = damage_rules[severity_key]

    base_min = rule["min"]
    base_max = rule["max"]
    labor_hours = rule.get("labor_hours", 0.0)
    paint_cost = rule.get("paint", 0.0)
    parts_cost = rule.get("parts", 0.0)
    action_desc = rule.get("desc", "Standard vehicle body repair procedure")

    # Slight dynamic adjustment based on confidence score
    confidence_factor = 0.95 + (max(0.5, min(confidence, 1.0)) * 0.1)
    
    final_min = round(base_min * confidence_factor, -1)
    final_max = round(base_max * confidence_factor, -1)

    labor_cost = round(labor_hours * LABOR_HOURLY_RATE, 2)

    return {
        "min": float(final_min),
        "max": float(final_max),
        "currency": "USD",
        "details": {
            "labor_hours": labor_hours,
            "labor_cost": labor_cost,
            "paint_cost": float(paint_cost),
            "parts_cost": float(parts_cost),
            "action_summary": action_desc
        }
    }
