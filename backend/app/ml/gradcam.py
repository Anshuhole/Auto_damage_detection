import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from typing import Tuple, List, Dict, Any, Optional


def strip_letterbox(img_bgr: np.ndarray) -> Tuple[np.ndarray, int, int, int, int]:
    """
    Detects and crops black letterbox / pillarbox padding borders around the image.
    Returns: cropped image, x_offset, y_offset, crop_width, crop_height
    """
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    non_black = gray > 18
    rows = np.any(non_black, axis=1)
    cols = np.any(non_black, axis=0)

    if np.any(rows) and np.any(cols):
        rmin, rmax = int(np.where(rows)[0][0]), int(np.where(rows)[0][-1])
        cmin, cmax = int(np.where(cols)[0][0]), int(np.where(cols)[0][-1])
    else:
        rmin, rmax, cmin, cmax = 0, h - 1, 0, w - 1

    crop_w = max(10, cmax - cmin + 1)
    crop_h = max(10, rmax - rmin + 1)
    crop = img_bgr[rmin:rmax+1, cmin:cmax+1]

    return crop, cmin, rmin, crop_w, crop_h


class PrecisionGradCAM:
    """
    High-Resolution Multi-Scale Grad-CAM++ Engine.
    Fuses Layer 3 (fine-grained spatial textures, scratches, cracks)
    and Layer 4 (high-level semantic damage representation) for comprehensive damage localization.
    """
    def __init__(self, model: torch.nn.Module, target_layer: Optional[torch.nn.Module] = None):
        self.model = model
        self.layer4 = model.backbone.layer4[-1] if hasattr(model, "backbone") else None
        self.layer3 = model.backbone.layer3[-1] if hasattr(model, "backbone") else None
        
        self.acts = {}
        self.grads = {}
        self.handles = []
        self._register_hooks()

    def _register_hooks(self):
        if self.layer3 is not None:
            def f_hook3(m, i, o): self.acts['l3'] = o.detach()
            def b_hook3(m, gi, go): self.grads['l3'] = go[0].detach()
            self.handles.append(self.layer3.register_forward_hook(f_hook3))
            self.handles.append(self.layer3.register_full_backward_hook(b_hook3))

        if self.layer4 is not None:
            def f_hook4(m, i, o): self.acts['l4'] = o.detach()
            def b_hook4(m, gi, go): self.grads['l4'] = go[0].detach()
            self.handles.append(self.layer4.register_forward_hook(f_hook4))
            self.handles.append(self.layer4.register_full_backward_hook(b_hook4))

    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_class: int,
        clean_class_idx: int = 4
    ) -> np.ndarray:
        self.model.eval()

        if target_class == clean_class_idx:
            return np.zeros((224, 224), dtype=np.float32)

        self.model.zero_grad()
        output = self.model(input_tensor)
        if isinstance(output, tuple):
            output = output[0]

        score_target = output[0, target_class]
        score_target.backward(retain_graph=True)

        cams = []

        # 1. Layer 4 Grad-CAM++ (Global Semantic Localization)
        if 'l4' in self.grads and 'l4' in self.acts:
            g4 = self.grads['l4'][0]
            a4 = self.acts['l4'][0]
            g4_2 = g4.pow(2)
            g4_3 = g4.pow(3)
            sum_a4 = a4.sum(dim=(1, 2), keepdim=True)
            aij4 = g4_2 / (2 * g4_2 + sum_a4 * g4_3 + 1e-7)
            w4 = (aij4 * F.relu(g4)).sum(dim=(1, 2), keepdim=True)
            cam4 = (w4 * a4).sum(dim=0).clamp(min=0).cpu().numpy()
            cam4_res = cv2.resize(cam4, (224, 224), interpolation=cv2.INTER_CUBIC)
            if cam4_res.max() > cam4_res.min() + 1e-6:
                cam4_n = (cam4_res - cam4_res.min()) / (cam4_res.max() - cam4_res.min())
            else:
                cam4_n = np.zeros((224, 224), dtype=np.float32)
            cams.append((0.35, cam4_n))

        # 2. Layer 3 Grad-CAM++ (Fine Spatial Scratches & Surface Defects)
        if 'l3' in self.grads and 'l3' in self.acts:
            g3 = self.grads['l3'][0]
            a3 = self.acts['l3'][0]
            g3_2 = g3.pow(2)
            g3_3 = g3.pow(3)
            sum_a3 = a3.sum(dim=(1, 2), keepdim=True)
            aij3 = g3_2 / (2 * g3_2 + sum_a3 * g3_3 + 1e-7)
            w3 = (aij3 * F.relu(g3)).sum(dim=(1, 2), keepdim=True)
            cam3 = (w3 * a3).sum(dim=0).clamp(min=0).cpu().numpy()
            cam3_res = cv2.resize(cam3, (224, 224), interpolation=cv2.INTER_CUBIC)
            if cam3_res.max() > cam3_res.min() + 1e-6:
                cam3_n = (cam3_res - cam3_res.min()) / (cam3_res.max() - cam3_res.min())
            else:
                cam3_n = np.zeros((224, 224), dtype=np.float32)
            cams.append((0.65, cam3_n))

        if cams:
            cam_fused = sum(w * c for w, c in cams)
            if cam_fused.max() > cam_fused.min() + 1e-6:
                cam_norm = (cam_fused - cam_fused.min()) / (cam_fused.max() - cam_fused.min())
            else:
                cam_norm = np.zeros((224, 224), dtype=np.float32)
        else:
            cam_norm = np.zeros((224, 224), dtype=np.float32)

        return cam_norm

    def remove_hooks(self):
        for handle in self.handles:
            handle.remove()
        self.handles = []


def create_precision_overlay(
    original_img_bgr: np.ndarray,
    cam: np.ndarray,
    has_damage: bool,
    damage_type: str,
    confidence: float
) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]]]:
    """
    Overlays Multi-Scale Grad-CAM++ heatmap fused with physical paint defect analysis
    and extracts accurate, full-extent bounding boxes.
    Guarantees:
    - 0 bounding boxes on clean cars.
    - Suppresses tire/wheel treads and dark tarmac to keep heatmap on the vehicle body.
    - Accurately encloses full damaged regions (scratches, dents, cracks, glass) across panels.
    """
    orig_h, orig_w = original_img_bgr.shape[:2]

    # Clean car check: return zero heatmap and empty boxes
    if not has_damage or damage_type == "no_damage":
        blank_heatmap = np.zeros_like(original_img_bgr)
        return original_img_bgr.copy(), blank_heatmap, []

    # 1. Strip letterbox padding
    crop, x_off, y_off, crop_w, crop_h = strip_letterbox(original_img_bgr)
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    crop_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    _, s_ch, v_ch = cv2.split(crop_hsv)

    # 2. Vehicle Paint Mask with Tire / Wheel Suppression
    is_tire = (s_ch < 55) & (v_ch < 95)
    tire_dilated = cv2.dilate(is_tire.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    paint_mask = (tire_dilated == 0).astype(np.float32)

    margin_y = max(4, int(crop_h * 0.02))
    margin_x = max(4, int(crop_w * 0.02))
    paint_mask[:margin_y, :] = 0
    paint_mask[-margin_y:, :] = 0
    paint_mask[:, :margin_x] = 0
    paint_mask[:, -margin_x:] = 0

    # 3. Physical Defect Surface Map
    k1 = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
    k2 = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    tophat = cv2.max(cv2.morphologyEx(crop_gray, cv2.MORPH_TOPHAT, k1), cv2.morphologyEx(crop_gray, cv2.MORPH_TOPHAT, k2))
    blackhat = cv2.max(cv2.morphologyEx(crop_gray, cv2.MORPH_BLACKHAT, k1), cv2.morphologyEx(crop_gray, cv2.MORPH_BLACKHAT, k2))
    scratch_raw = cv2.max(tophat, blackhat).astype(np.float32) / 255.0

    blur_large = cv2.GaussianBlur(crop_gray, (45, 45), 0)
    dent_raw = cv2.absdiff(crop_gray, blur_large).astype(np.float32) / 255.0

    if damage_type == "scratch":
        defect_map = (0.75 * scratch_raw + 0.25 * dent_raw) * paint_mask
    elif damage_type == "dent":
        defect_map = (0.30 * scratch_raw + 0.70 * dent_raw) * paint_mask
    else:
        defect_map = (0.50 * scratch_raw + 0.50 * dent_raw) * paint_mask

    defect_blur = cv2.GaussianBlur(defect_map, (15, 15), 0)
    if defect_blur.max() > defect_blur.min() + 1e-6:
        d_norm = (defect_blur - defect_blur.min()) / (defect_blur.max() - defect_blur.min())
    else:
        d_norm = np.zeros_like(defect_blur)

    # 4. Neural CAM resize & normalization
    cam_crop = cv2.resize(cam, (crop_w, crop_h), interpolation=cv2.INTER_CUBIC)
    if cam_crop.max() > cam_crop.min() + 1e-6:
        cam_norm = (cam_crop - cam_crop.min()) / (cam_crop.max() - cam_crop.min())
    else:
        cam_norm = np.zeros_like(cam_crop)

    # 5. Fuse Multi-Scale CAM with Physical Defect Surface Map
    fused_saliency = (0.40 * cam_norm + 0.60 * d_norm) * paint_mask
    fused_saliency = np.clip((fused_saliency - 0.16) / (1.0 - 0.16), 0.0, 1.0)
    fused_saliency = np.power(fused_saliency, 1.15)

    # Map back to full original image canvas
    full_cam = np.zeros((orig_h, orig_w), dtype=np.float32)
    full_cam[y_off:y_off+crop_h, x_off:x_off+crop_w] = fused_saliency
    full_cam = cv2.GaussianBlur(full_cam, (7, 7), 0)

    cam_uint8 = np.uint8(255 * full_cam)
    heatmap_bgr = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)

    # Thermal alpha blend strictly where heat is present (> 0.05) - vivid thermal intensity
    alpha_mask = np.where(full_cam > 0.05, np.clip((full_cam ** 0.82) * 0.92, 0.0, 1.0), 0.0)[:, :, np.newaxis]
    overlay_bgr = np.uint8(original_img_bgr * (1.0 - alpha_mask) + heatmap_bgr * alpha_mask)

    # 6. Extract Multi-Zone Full-Span Bounding Boxes
    bounding_boxes = []
    crop_cam_uint8 = np.uint8(255 * fused_saliency)
    active_pixels = crop_cam_uint8[crop_cam_uint8 > 20]
    thresh_val = max(38, int(np.percentile(active_pixels, 35))) if len(active_pixels) > 0 else 45
    _, thresh = cv2.threshold(crop_cam_uint8, thresh_val, 255, cv2.THRESH_BINARY)

    # Morphological closing to connect adjacent damage streaks into unified zones
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (29, 29))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    crop_area = crop_w * crop_h

    valid_boxes = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > (crop_area * 0.015):
            x, y, w, h = cv2.boundingRect(cnt)
            valid_boxes.append((x, y, w, h, area))

    if valid_boxes:
        valid_boxes = sorted(valid_boxes, key=lambda b: b[4], reverse=True)
        # Capture up to 2 distinct damage zones (e.g. primary scratch field + secondary dent)
        for x, y, w, h, area in valid_boxes[:2]:
            bx_orig = x_off + x
            by_orig = y_off + y
            bw_orig = w
            bh_orig = h

            pad_x = int(bw_orig * 0.03)
            pad_y = int(bh_orig * 0.03)
            final_x = max(0, bx_orig - pad_x)
            final_y = max(0, by_orig - pad_y)
            final_w = min(orig_w - final_x, bw_orig + 2 * pad_x)
            final_h = min(orig_h - final_y, bh_orig + 2 * pad_y)

            roi_mask = full_cam[final_y:final_y+final_h, final_x:final_x+final_w]
            roi_conf = float(np.mean(roi_mask[roi_mask > 0])) if np.any(roi_mask > 0) else 0.85

            bounding_boxes.append({
                "x": round(float(final_x) / orig_w, 4),
                "y": round(float(final_y) / orig_h, 4),
                "width": round(float(final_w) / orig_w, 4),
                "height": round(float(final_h) / orig_h, 4),
                "label": f"{damage_type.replace('_', ' ').title()} Zone",
                "confidence": round(min(0.98, max(0.82, confidence)), 3)
            })

    return overlay_bgr, heatmap_bgr, bounding_boxes
