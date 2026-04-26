import os
import io
from PIL import Image

def process_image(file_bytes: bytes) -> str:
    """
    Processes the uploaded image bytes, saves it temporarily, 
    and returns the file path. Real-world scenarios should use S3/CDN.
    """
    image = Image.open(io.BytesIO(file_bytes))
    
    # Ensure RGB
    if image.mode != "RGB":
        image = image.convert("RGB")
        
    # Resize keeping aspect ratio, optimized for 768x1024 or 512x768 (standard V-TON)
    # We will just save it as is for the HF client or limit max dimension.
    max_size = 1024
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Save to system temp area
    import tempfile
    import uuid
    filename = os.path.join(tempfile.gettempdir(), f"viton_{uuid.uuid4().hex}.jpg")
    image.save(filename, format="JPEG", quality=95)
    return filename

def cleanup_files(*filepaths):
    """
    Utility to remove temporary files after processing.
    """
    for fp in filepaths:
        if fp and os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception as e:
                print(f"Error removing {fp}: {e}")

def generate_fullbody_mask(human_img_path: str, bottom_ratio: float = 0.85) -> str:
    """
    Generates a white mask that covers the full body clothing area 
    (from neck to ankles, roughly 15%-85% of the image height).
    The mask tells IDM-VTON to replace that area instead of just the upper body.
    White = area to replace, Black = area to keep.
    """
    img = Image.open(human_img_path)
    w, h = img.size
    
    # Create a black image (keep everything by default)
    mask = Image.new("RGB", (w, h), (0, 0, 0))
    
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    
    # ENHANCED: Move top margin down to ensure the face is NOT masked.
    # bottom_ratio allows controlling garment length (e.g. 0.65 for knee-length kurti)
    top = int(h * 0.22) 
    bottom = int(h * bottom_ratio)
    left = int(w * 0.10)
    right = int(w * 0.90)
    
    # Use a trapezoidal / tapered top to better follow shoulder lines
    # AND narrower at the bottom to avoid masking hands at the sides
    shoulder_top = top
    shoulder_width_offset = int(w * 0.15)
    bottom_width_offset = int(w * 0.20)  # Narrower at bottom to protect hands
    
    points = [
        (left + shoulder_width_offset, shoulder_top),
        (right - shoulder_width_offset, shoulder_top),
        (right - bottom_width_offset, bottom),
        (left + bottom_width_offset, bottom)
    ]
    
    draw.polygon(points, fill=(255, 255, 255))
    
    # Save mask
    import tempfile
    import uuid as _uuid
    mask_path = os.path.join(tempfile.gettempdir(), f"viton_mask_{_uuid.uuid4().hex}.png")
    mask.save(mask_path)
    return mask_path

def generate_lowerbody_mask(human_img_path: str, top_ratio: float = 0.40, bottom_ratio: float = 0.98) -> str:
    """
    Generates a white mask that covers only the lower body area (waist to ankles).
    This forces the model to replace the pants/skirt instead of the upper body.
    """
    img = Image.open(human_img_path)
    w, h = img.size
    
    # Create black image
    mask = Image.new("RGB", (w, h), (0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(mask)
    
    # ULTRA-PROTECTIVE: Start lower and keep waist very narrow to avoid arms/torso distortions
    # top_ratio=0.48 starts the pants mask below the natural waistline
    top = int(h * 0.48) 
    bottom = int(h * bottom_ratio)
    
    # Very narrow waist column (approx 20% width)
    left = int(w * 0.40)
    right = int(w * 0.60)
    
    # Widen aggressively at the bottom for flared/wide pants
    bottom_width_offset = int(w * 0.15)
    
    points = [
        (left, top),
        (right, top),
        (right + bottom_width_offset, bottom),
        (left - bottom_width_offset, bottom)
    ]
    
    draw.polygon(points, fill=(255, 255, 255))
    
    import tempfile
    import uuid as _uuid
    mask_path = os.path.join(tempfile.gettempdir(), f"viton_mask_lower_{_uuid.uuid4().hex}.png")
    mask.save(mask_path)
    return mask_path

def preserve_face_and_pose(original_human_path: str, generated_result_path: str) -> str:
    """
    Stitches the original face and head area back onto the generated result 
    to ensure 100% identity preservation.
    """
    orig = Image.open(original_human_path).convert("RGBA")
    gen = Image.open(generated_result_path).convert("RGBA")
    
    # Ensure they are the same size
    if orig.size != gen.size:
        orig = orig.resize(gen.size, Image.Resampling.LANCZOS)
    
    w, h = gen.size
    
    # Create a feather mask for the top ~25% (head/neck area)
    # White = original, Black = generated
    face_mask = Image.new("L", (w, h), 0)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(face_mask)
    
    # Gradient/Feathered transition around 25% height
    transition_start = int(h * 0.15)
    transition_end = int(h * 0.30)
    
    # Fill top area solidly
    draw.rectangle([0, 0, w, transition_start], fill=255)
    
    # Gradient for smooth blending
    for y in range(transition_start, transition_end):
        # Quadratic-like ease-in-out for smoother transition
        t = (y - transition_start) / (transition_end - transition_start)
        alpha = int(255 * (1 - (3*t**2 - 2*t**3))) 
        draw.line([(0, y), (w, y)], fill=alpha)
        
    # ENHANCED: Apply slight Gaussian blur to the mask to avoid sharp seams
    from PIL import ImageFilter
    face_mask = face_mask.filter(ImageFilter.GaussianBlur(radius=5))
    
    # Composite: orig (top) over gen (bottom)
    final_img = Image.composite(orig, gen, face_mask)
    
    # Save result back to a new path
    import tempfile
    import uuid
    output_path = os.path.join(tempfile.gettempdir(), f"viton_stitched_{uuid.uuid4().hex}.png")
    final_img.convert("RGB").save(output_path, quality=95)
    return output_path

def preserve_identity_via_mask(original_human_path: str, generated_result_path: str, mask_path: str) -> str:
    """
    Uses the generation mask to stitch original content (hands, arms, face) 
    back onto the generated result. 
    White in mask = keep generated (pants).
    Black in mask = keep original (identity).
    """
    orig = Image.open(original_human_path).convert("RGBA")
    gen = Image.open(generated_result_path).convert("RGBA")
    mask = Image.open(mask_path).convert("L") # Mask is grayscale (L)
    
    # Ensure they are the same size
    if orig.size != gen.size:
        orig = orig.resize(gen.size, Image.Resampling.LANCZOS)
    if mask.size != gen.size:
        mask = mask.resize(gen.size, Image.Resampling.LANCZOS)
        
    # Feather the mask slightly to prevent sharp seams
    from PIL import ImageFilter
    mask = mask.filter(ImageFilter.GaussianBlur(radius=3))
    
    # Composite: gen (where mask is white) over orig (where mask is black)
    # Image.composite uses the mask to blend: res = gen * mask + orig * (1-mask)
    final_img = Image.composite(gen, orig, mask)
    
    import tempfile
    import uuid
    output_path = os.path.join(tempfile.gettempdir(), f"viton_final_{uuid.uuid4().hex}.png")
    final_img.convert("RGB").save(output_path, quality=95)
    return output_path
