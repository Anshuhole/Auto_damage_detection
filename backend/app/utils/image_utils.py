import os
import io
import base64
import uuid
from PIL import Image
from typing import Tuple
from app.config import UPLOAD_DIR, GRADCAM_DIR

def decode_base64_image(base64_str: str) -> Image.Image:
    """
    Decodes a base64 image string (with or without data URL header) into a PIL Image.
    """
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    
    img_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(img_data)).convert("RGB")

def encode_pil_to_base64(pil_img: Image.Image, format: str = "JPEG") -> str:
    """
    Encodes a PIL Image into a base64 data URL string.
    """
    buffered = io.BytesIO()
    pil_img.save(buffered, format=format, quality=90)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/{format.lower()};base64,{img_str}"

def save_inspection_images(original_img: Image.Image, gradcam_img: Image.Image, prefix: str = "") -> Tuple[str, str, str, str]:
    """
    Saves original and Grad-CAM images to static directories and returns file paths and URLs.
    """
    unique_id = f"{prefix}_{uuid.uuid4().hex[:10]}" if prefix else uuid.uuid4().hex[:12]
    orig_filename = f"orig_{unique_id}.jpg"
    gradcam_filename = f"gradcam_{unique_id}.jpg"

    orig_path = UPLOAD_DIR / orig_filename
    gradcam_path = GRADCAM_DIR / gradcam_filename

    # Save original image (max width 1200 for web storage efficiency)
    orig_to_save = original_img.copy()
    if orig_to_save.width > 1400:
        ratio = 1400 / orig_to_save.width
        orig_to_save = orig_to_save.resize((1400, int(orig_to_save.height * ratio)), Image.Resampling.LANCZOS)
    
    orig_to_save.save(orig_path, format="JPEG", quality=92)
    gradcam_img.save(gradcam_path, format="JPEG", quality=92)

    orig_url = f"/static/uploads/{orig_filename}"
    gradcam_url = f"/static/gradcam/{gradcam_filename}"

    return orig_filename, str(orig_path), orig_url, gradcam_url
