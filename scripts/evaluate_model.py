"""
GeoSentinel AI - Evaluation Script
Evaluates the trained DeepLabV3+ model on the real Sentinel-2 validation patches.
Generates metrics and visualization plots.
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import torch
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix
import matplotlib.colors as mcolors

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.model_factory import ModelFactory
from src.models.unet import NUM_CLASSES, DEFAULT_IN_CHANNELS, LAND_COVER_NAMES
from scripts.train import GeoSentinelDataModule

# Sentinel-2 visualization bands
RGB_BANDS = [2, 1, 0] # B04, B03, B02 are at indices 2, 1, 0 in the stack

# Colors for the 6 classes
COLORS = [
    '#000000', # 0: Background
    '#FF0000', # 1: Urban (Red)
    '#00FF00', # 2: Vegetation (Green)
    '#0000FF', # 3: Water (Blue)
    '#FFFF00', # 4: Barren (Yellow)
    '#FFA500'  # 5: Agriculture (Orange)
]
CMAP = mcolors.ListedColormap(COLORS)
NORM = mcolors.BoundaryNorm(boundaries=np.arange(NUM_CLASSES + 1) - 0.5, ncolors=NUM_CLASSES)

def compute_metrics(y_true, y_pred, num_classes):
    cm = confusion_matrix(y_true.flatten(), y_pred.flatten(), labels=range(num_classes))
    
    intersection = np.diag(cm)
    ground_truth_set = cm.sum(axis=1)
    predicted_set = cm.sum(axis=0)
    union = ground_truth_set + predicted_set - intersection
    
    iou = intersection / (union + 1e-10)
    miou = np.nanmean(iou)
    
    precision = intersection / (predicted_set + 1e-10)
    recall = intersection / (ground_truth_set + 1e-10)
    
    # F1 Score
    f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
    
    # Overall Accuracy
    total_pixels = cm.sum()
    oa = intersection.sum() / (total_pixels + 1e-10)
    
    # Kappa
    pe = (ground_truth_set * predicted_set).sum() / (total_pixels * total_pixels + 1e-10)
    kappa = (oa - pe) / (1 - pe + 1e-10)
    
    return miou, iou, precision, recall, f1, oa, kappa

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="deeplabv3plus")
    parser.add_argument("--weights", type=str, default="data/weights/deeplabv3plus_best.pt")
    parser.add_argument("--data-dir", type=str, default="data/benchmark/real")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-visualizations", type=int, default=5)
    args = parser.parse_args()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating on device: {device}")
    
    # Load model
    weights_path = PROJECT_ROOT / args.weights
    if not weights_path.exists():
        print(f"Error: Weights file not found at {weights_path}")
        return
        
    factory = ModelFactory()
    model = factory.create_model(
        model_type=args.model,
        in_channels=DEFAULT_IN_CHANNELS,
        num_classes=NUM_CLASSES,
        encoder_name="resnet50",
        encoder_weights=None
    )
    
    print(f"Loading weights from {weights_path}")
    checkpoint = torch.load(weights_path, map_location=device, weights_only=True)
    
    # Extract state_dict
    state_dict = None
    if "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    elif "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
    else:
        state_dict = checkpoint
        
    # GeoSentinelDeepLabV3Plus and UNet wrap the smp model in 'self.model'
    # So the model expects keys starting with 'model.'
    # If the checkpoint keys don't have 'model.', add it.
    # If the checkpoint keys have 'model.' but the model doesn't expect it, remove it.
    model_keys = list(model.state_dict().keys())
    needs_model_prefix = any(k.startswith("model.") for k in model_keys)
    has_model_prefix = any(k.startswith("model.") for k in state_dict.keys())
    
    new_state_dict = {}
    for k, v in state_dict.items():
        if needs_model_prefix and not has_model_prefix:
            new_state_dict[f"model.{k}"] = v
        elif not needs_model_prefix and has_model_prefix:
            new_state_dict[k.replace("model.", "", 1)] = v
        else:
            new_state_dict[k] = v
            
    model.load_state_dict(new_state_dict, strict=False)
        
    model = model.to(device)
    model.eval()
    
    # Load data
    data_dir = PROJECT_ROOT / args.data_dir
    datamodule = GeoSentinelDataModule(data_dir=data_dir, batch_size=args.batch_size, num_workers=4)
    datamodule.setup()
    
    val_loader = datamodule.val_dataloader()
    
    print(f"Starting evaluation on {len(val_loader.dataset)} validation patches...")
    
    all_preds = []
    all_masks = []
    vis_images = []
    vis_masks = []
    vis_preds = []
    
    with torch.no_grad():
        for i, batch in enumerate(val_loader):
            images = batch["image"].to(device)
            masks = batch["mask"].cpu().numpy()
            
            logits = model(images)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            
            all_preds.append(preds)
            all_masks.append(masks)
            
            # Save some for visualization
            if len(vis_images) < args.num_visualizations:
                for j in range(images.shape[0]):
                    if len(vis_images) >= args.num_visualizations:
                        break
                    img_np = images[j].cpu().numpy()
                    vis_images.append(img_np)
                    vis_masks.append(masks[j])
                    vis_preds.append(preds[j])
                    
    all_preds = np.concatenate(all_preds, axis=0)
    all_masks = np.concatenate(all_masks, axis=0)
    
    miou, iou, precision, recall, f1, oa, kappa = compute_metrics(all_masks, all_preds, NUM_CLASSES)
    
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    print(f"Overall Accuracy (OA): {oa:.4f}")
    print(f"Kappa Coefficient:     {kappa:.4f}")
    print(f"Mean IoU:              {miou:.4f}")
    print("-" * 50)
    for class_id, class_name in LAND_COVER_NAMES.items():
        print(f"Class {class_id} ({class_name}):")
        print(f"  IoU:       {iou[class_id]:.4f}")
        print(f"  F1-Score:  {f1[class_id]:.4f}")
        print(f"  Precision: {precision[class_id]:.4f}")
        print(f"  Recall:    {recall[class_id]:.4f}")
    
    # Visualizations
    if args.num_visualizations > 0:
        print("\nGenerating visualizations...")
        out_dir = PROJECT_ROOT / "data" / "benchmark" / "real" / "visualizations_100_epochs"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(len(vis_images)):
            fig, axs = plt.subplots(1, 3, figsize=(15, 5))
            
            # RGB Image
            # Normalize to 0-1 for plotting based on Sentinel-2 typical reflectance
            img_rgb = vis_images[i][RGB_BANDS].transpose(1, 2, 0)
            img_rgb = np.clip(img_rgb * 3.0, 0, 1) # Brighten slightly
            
            axs[0].imshow(img_rgb)
            axs[0].set_title("Sentinel-2 RGB (T1)")
            axs[0].axis("off")
            
            # Ground Truth
            im1 = axs[1].imshow(vis_masks[i], cmap=CMAP, norm=NORM)
            axs[1].set_title("ESA WorldCover (Ground Truth)")
            axs[1].axis("off")
            
            # Prediction
            im2 = axs[2].imshow(vis_preds[i], cmap=CMAP, norm=NORM)
            axs[2].set_title(f"Prediction ({args.model})")
            axs[2].axis("off")
            
            plt.tight_layout()
            save_path = out_dir / f"eval_patch_{i}.png"
            plt.savefig(save_path)
            plt.close()
            
        print(f"Saved {len(vis_images)} visualizations to {out_dir}")

if __name__ == "__main__":
    main()
