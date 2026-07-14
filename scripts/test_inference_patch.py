import os
import numpy as np
import torch
import cv2
from PIL import Image

from src.models.model_factory import ModelFactory
from src.models.unet import LAND_COVER_COLORS, LandCoverClass

def colorize_mask(mask: np.ndarray) -> np.ndarray:
    """Convert a 2D mask of class indices into an RGB image."""
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_idx in np.unique(mask):
        try:
            lc_enum = LandCoverClass(class_idx)
            r, g, b = LAND_COVER_COLORS[lc_enum]
            rgb[mask == class_idx] = [r, g, b]
        except ValueError:
            pass # ignore unknown classes
    return rgb

def main():
    patch_path = "data/benchmark/real/train/image_0000.npy"
    if not os.path.exists(patch_path):
        print("Patch not found.")
        return
        
    img = np.load(patch_path) # (12, H, W)
    print(f"Loaded patch shape: {img.shape}")
    
    factory = ModelFactory()
    model = factory.create_model('unet', in_channels=12, num_classes=6)
    ckpt = torch.load("data/weights/unet_best.pt", map_location='cpu', weights_only=True)
    
    # Extract state dict if nested
    if "model_state_dict" in ckpt:
        state_dict = ckpt["model_state_dict"]
    else:
        state_dict = ckpt
        
    model.load_state_dict(state_dict)
    model.eval()
    
    with torch.no_grad():
        tensor = torch.tensor(img, dtype=torch.float32).unsqueeze(0)
        out = model(tensor)
        pred = torch.argmax(out, dim=1).squeeze(0).numpy() # (H, W)
        
    print(f"Prediction unique classes: {np.unique(pred)}")
    
    color_mask = colorize_mask(pred)
    
    # Save the raw image (B04=idx 2, B03=idx 1, B02=idx 0)
    # Actually let's just make it a bit brighter
    rgb_img = img[[2, 1, 0], :, :]
    rgb_img = np.transpose(rgb_img, (1, 2, 0))
    rgb_img = np.clip(rgb_img * 255 * 2.5, 0, 255).astype(np.uint8)
    
    # Concatenate side by side
    combined = np.hstack((rgb_img, color_mask))
    
    # Save to artifacts directory
    # Get the conversation ID from environment or just hardcode the path
    # C:\Users\karth\.gemini\antigravity\brain\6d03cec9-78f8-4763-8ee0-3e1ffe5599bc
    out_dir = r"C:\Users\karth\.gemini\antigravity\brain\6d03cec9-78f8-4763-8ee0-3e1ffe5599bc"
    os.makedirs(out_dir, exist_ok=True)
    
    out_path = os.path.join(out_dir, "segmentation_preview.png")
    Image.fromarray(combined).save(out_path)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
