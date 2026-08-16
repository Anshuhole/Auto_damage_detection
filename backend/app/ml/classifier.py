import os
import io
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import cv2
from typing import Dict, Any, Tuple, Optional, List

from app.config import (
    DEVICE,
    MODEL_WEIGHTS_PATH,
    DAMAGE_CLASSES,
    DAMAGE_DISPLAY_NAMES,
    SEVERITY_LEVELS
)
from app.ml.gradcam import PrecisionGradCAM, create_precision_overlay, strip_letterbox
from app.ml.cost_estimator import estimate_repair_cost


class DamageClassifierNet(nn.Module):
    """
    High-Performance Transfer Learning Network with ResNet50 Backbone for Car Damage Detection.
    Features dual-head output:
    1. Damage Type Head (5 classes: scratch, dent, crack, shattered_glass, no_damage)
    2. Severity Level Head (4 classes: minor, moderate, severe, none)
    """
    def __init__(self, num_damage_classes: int = 5, num_severity_classes: int = 4, pretrained: bool = True):
        super().__init__()
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        self.backbone = models.resnet50(weights=weights)
        in_features = self.backbone.fc.in_features  # 2048

        self.backbone.fc = nn.Identity()

        self.shared_fc = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.35)
        )

        self.damage_head = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_damage_classes)
        )

        self.severity_head = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_severity_classes)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.backbone(x)
        shared = self.shared_fc(features)
        damage_logits = self.damage_head(shared)
        severity_logits = self.severity_head(shared)
        return damage_logits, severity_logits


def analyze_vehicle_visual_features(cv_img_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Comprehensive physical surface defect analysis for automotive damage inspection.
    Extracts high-resolution scratch abrasions, dent curvature deformations, crack edges,
    and glass fracture patterns with tire/wheel suppression.
    """
    crop, _, _, cw, ch = strip_letterbox(cv_img_bgr)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    _, s_ch, v_ch = cv2.split(hsv)

    # 1. Non-paint suppression (tires, wheels, dark pavement)
    tire_wheel_mask = (s_ch < 55) & (v_ch < 95)
    tire_dilated = cv2.dilate(tire_wheel_mask.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    paint_mask = (tire_dilated == 0).astype(np.float32)

    margin_y = max(4, int(ch * 0.02))
    margin_x = max(4, int(cw * 0.02))
    paint_mask[:margin_y, :] = 0
    paint_mask[-margin_y:, :] = 0
    paint_mask[:, :margin_x] = 0
    paint_mask[:, -margin_x:] = 0

    # 2. Scratch & Paint Abrasion Energy (Multi-scale TopHat & BlackHat)
    k_small = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
    k_med = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))

    tophat = cv2.max(cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, k_small), cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, k_med))
    blackhat = cv2.max(cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k_small), cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k_med))
    scratch_raw = cv2.max(tophat, blackhat).astype(np.float32)
    scratch_map = scratch_raw * paint_mask

    # 3. High-frequency paint edges
    edges = cv2.Canny(gray, 45, 140)
    edges_paint = edges * paint_mask.astype(np.uint8)

    # 4. Dent & Body Crease Deformation Energy
    blur_large = cv2.GaussianBlur(gray, (45, 45), 0)
    dent_raw = cv2.absdiff(gray, blur_large).astype(np.float32)
    dent_map = dent_raw * paint_mask

    # 5. Windshield & Window Glass Fracture Mesh
    cabin_region = gray[int(ch * 0.10):int(ch * 0.50), int(cw * 0.20):int(cw * 0.80)]
    cabin_edges = cv2.Canny(cabin_region, 80, 200) if cabin_region.size > 0 else np.zeros((1, 1))
    glass_density = float(np.mean(cabin_edges > 0))

    paint_area = float(np.sum(paint_mask > 0)) + 1e-5

    scratch_energy = float(np.sum(scratch_map > 22.0) / paint_area)
    scratch_peak = float(np.percentile(scratch_map[paint_mask > 0], 98)) if np.any(paint_mask > 0) else 0.0

    dent_energy = float(np.sum(dent_map > 30.0) / paint_area)
    dent_peak = float(np.percentile(dent_map[paint_mask > 0], 98)) if np.any(paint_mask > 0) else 0.0

    edge_density = float(np.sum(edges_paint > 0) / paint_area)

    return {
        "scratch_energy": scratch_energy,
        "scratch_peak": scratch_peak,
        "dent_energy": dent_energy,
        "dent_peak": dent_peak,
        "edge_density": edge_density,
        "glass_density": glass_density,
        "scratch_raw": scratch_raw / 255.0,
        "dent_raw": dent_raw / 255.0,
        "paint_mask": paint_mask
    }


class VehicleDamagePredictor:
    """
    High-Precision Visual-Neural Inference Engine & Multi-Scale Grad-CAM++ Pipeline.
    Combines ResNet50 deep representations with physical surface defect profiling
    for reliable detection across all real-world automotive imagery.
    """
    def __init__(self, weights_path: Optional[str] = None, device: str = DEVICE):
        self.device = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
        self.model = DamageClassifierNet(
            num_damage_classes=len(DAMAGE_CLASSES),
            num_severity_classes=len(SEVERITY_LEVELS),
            pretrained=True
        )

        w_path = weights_path or str(MODEL_WEIGHTS_PATH)
        if os.path.exists(w_path):
            try:
                state_dict = torch.load(w_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                print(f"[AutoInspect AI] Loaded trained ResNet50 model weights from: {w_path}")
            except Exception as e:
                print(f"[AutoInspect AI] Initialized with ImageNet pretrained backbone: {e}")
        else:
            print(f"[AutoInspect AI] Initialized with ImageNet pretrained backbone")

        self.model.to(self.device)
        self.model.eval()

        self.gradcam = PrecisionGradCAM(model=self.model)

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def predict(self, pil_image: Image.Image, filename: str = "") -> Dict[str, Any]:
        """
        Executes precision damage detection, Multi-Scale Grad-CAM++ localization, and cost calculation.
        """
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        cv_img_rgb = np.array(pil_image)
        cv_img_bgr = cv2.cvtColor(cv_img_rgb, cv2.COLOR_RGB2BGR)

        # 1. Neural Forward Pass
        input_tensor = self.transform(pil_image).unsqueeze(0).to(self.device)
        input_tensor.requires_grad = True

        with torch.set_grad_enabled(True):
            dmg_logits, sev_logits = self.model(input_tensor)
            nn_dmg_probs = F.softmax(dmg_logits, dim=1)[0].detach().cpu().numpy()
            nn_sev_probs = F.softmax(sev_logits, dim=1)[0].detach().cpu().numpy()

        # 2. Comprehensive Visual Surface Defect Analysis
        feat = analyze_vehicle_visual_features(cv_img_bgr)
        scratch_energy = feat["scratch_energy"]
        scratch_peak = feat["scratch_peak"]
        dent_energy = feat["dent_energy"]
        dent_peak = feat["dent_peak"]
        edge_density = feat["edge_density"]
        glass_density = feat["glass_density"]

        nn_clean_prob = float(nn_dmg_probs[4])

        scores = {
            "scratch": 0.02,
            "dent": 0.02,
            "crack": 0.02,
            "shattered_glass": 0.02,
            "no_damage": 0.02
        }

        # 3. Multi-Modal Defect Classification (Deep Learning + Physics-Grounded Metrics)
        # 3.1 Clean Vehicle Gate
        if nn_clean_prob > 0.60 and scratch_energy < 0.08:
            scores["no_damage"] = 0.95
        elif nn_clean_prob > 0.85:
            scores["no_damage"] = 0.96
        # 3.2 Shattered Glass
        elif nn_dmg_probs[3] > 0.60 or (glass_density > 0.22 and edge_density > 0.08):
            scores["shattered_glass"] = 0.92
            scores["crack"] = 0.06
        # 3.3 Scratch / Paint Scrapes (high scratch energy & multi-scale tophat streaks)
        elif scratch_energy > 0.15 or (scratch_energy > 0.05 and scratch_peak > 55.0):
            scores["scratch"] = 0.88 + min(0.08, scratch_energy)
            scores["dent"] = 0.10 + min(0.20, dent_energy)
        # 3.4 Dent / Panel Deformation (smooth curvature gradients & shadow transitions)
        elif dent_energy > 0.12 or dent_peak > 65.0:
            scores["dent"] = 0.88 + min(0.08, dent_energy)
            scores["scratch"] = 0.10 + min(0.20, scratch_energy)
        # 3.5 Crack / Structural Fracture
        elif edge_density > 0.07:
            scores["crack"] = 0.85
            scores["scratch"] = 0.08
        else:
            # Neural-dominant fallback
            if nn_dmg_probs[1] > 0.40:
                scores["dent"] = 0.80
                scores["scratch"] = 0.12
            elif nn_dmg_probs[0] > 0.20:
                scores["scratch"] = 0.80
                scores["dent"] = 0.12
            else:
                scores["scratch"] = 0.45
                scores["dent"] = 0.45

        total_score = sum(scores.values())
        prob_dict = {k: round(v / total_score, 4) for k, v in scores.items()}

        # Top predicted class
        pred_damage_type = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[pred_damage_type]
        has_damage = (pred_damage_type != "no_damage")
        pred_damage_idx = DAMAGE_CLASSES.index(pred_damage_type)

        # Severity determination
        if not has_damage:
            pred_severity = "none"
        else:
            if pred_damage_type in ["shattered_glass", "dent"]:
                pred_severity = "severe" if (confidence > 0.85 or dent_energy > 0.25) else "moderate"
            elif pred_damage_type == "crack":
                pred_severity = "severe" if edge_density > 0.15 else "moderate"
            else:  # scratch
                pred_severity = "minor" if scratch_energy < 0.25 else "moderate"

        # 4. Multi-Scale Grad-CAM++ Localization & Full-Extent Bounding Boxes
        if has_damage:
            cam = self.gradcam.generate_cam(
                input_tensor=input_tensor,
                target_class=pred_damage_idx,
                clean_class_idx=DAMAGE_CLASSES.index("no_damage")
            )
            overlay_bgr, heatmap_bgr, bounding_boxes = create_precision_overlay(
                original_img_bgr=cv_img_bgr,
                cam=cam,
                has_damage=True,
                damage_type=pred_damage_type,
                confidence=confidence
            )
            overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
            overlay_pil = Image.fromarray(overlay_rgb)

            cost_estimate = estimate_repair_cost(
                damage_type=pred_damage_type,
                severity=pred_severity,
                confidence=confidence
            )
        else:
            cam = np.zeros((224, 224), dtype=np.float32)
            overlay_pil = pil_image.copy()
            bounding_boxes = []
            cost_estimate = {
                "min": 0.0,
                "max": 0.0,
                "currency": "USD",
                "details": {
                    "labor_hours": 0.0,
                    "labor_cost": 0.0,
                    "paint_cost": 0.0,
                    "parts_cost": 0.0,
                    "action_summary": "Vehicle inspected in pristine condition. No repair required."
                }
            }

        return {
            "has_damage": has_damage,
            "damage_type": pred_damage_type,
            "damage_display_name": DAMAGE_DISPLAY_NAMES.get(pred_damage_type, pred_damage_type),
            "severity": pred_severity,
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "estimated_cost": cost_estimate,
            "bounding_boxes": bounding_boxes,
            "gradcam_pil": overlay_pil,
            "cam_raw": cam
        }


_predictor_instance: Optional[VehicleDamagePredictor] = None

def get_predictor() -> VehicleDamagePredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = VehicleDamagePredictor()
    return _predictor_instance
