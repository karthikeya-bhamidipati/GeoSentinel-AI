"""
GeoSentinel AI - Siamese U-Net Evaluation Script
Evaluates the trained Siamese U-Net model on the OSCD validation dataset.
Generates metrics and visualization plots.
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import torch
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
import matplotlib.colors as mcolors

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.siamese import GeoSentinelSiameseUNet
from scripts.train_change import OSCDDataModule

# Sentinel-2 visualization bands
RGB_BANDS = [2, 1, 0] # B04, B03, B02

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=str, default="data/weights/change_unet_best.pt")
    parser.add_argument("--deeplab-weights", type=str, default="data/weights/deeplabv3plus_best.pt")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--num-visualizations", type=int, default=5)
    args = parser.parse_args()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating on device: {device}")
    
    # Load model
    weights_path = PROJECT_ROOT / args.weights
    deeplab_path = PROJECT_ROOT / args.deeplab_weights
    
    if not weights_path.exists():
        print(f"Error: Weights file not found at {weights_path}")
        return
        
    model = GeoSentinelSiameseUNet(deeplab_ckpt_path=str(deeplab_path), num_classes=2)
    
    print(f"Loading weights from {weights_path}")
    checkpoint = torch.load(weights_path, map_location=device, weights_only=True)
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    
    new_sd = {}
    for k, v in state_dict.items():
        if k.startswith("model."):
            new_sd[k[6:]] = v
        else:
            new_sd[k] = v
            
    model.load_state_dict(new_sd, strict=False)
    model = model.to(device)
    model.eval()
    
    # Load data
    datamodule = OSCDDataModule(batch_size=args.batch_size, num_workers=4)
    datamodule.setup()
    
    val_loader = datamodule.val_dataloader()
    print(f"Starting evaluation on validation patches...")
    
    all_preds = []
    all_masks = []
    vis_t1 = []
    vis_t2 = []
    vis_masks = []
    vis_preds = []
    
    with torch.no_grad():
        for i, batch in enumerate(val_loader):
            t1 = batch["t1"].to(device)
            t2 = batch["t2"].to(device)
            masks = batch["mask"].cpu().numpy()
            
            logits = model(t1, t2)
            # Require 75% confidence to declare a change, reducing false positives
            probs = torch.softmax(logits, dim=1)[:, 1]
            preds = (probs > 0.75).cpu().numpy().astype(np.int32)
            
            all_preds.append(preds.flatten())
            all_masks.append(masks.flatten())
            
            # Save some for visualization
            if len(vis_t1) < args.num_visualizations:
                for j in range(t1.shape[0]):
                    if len(vis_t1) >= args.num_visualizations:
                        break
                    vis_t1.append(t1[j].cpu().numpy())
                    vis_t2.append(t2[j].cpu().numpy())
                    vis_masks.append(masks[j])
                    vis_preds.append(preds[j])
                    
    all_preds = np.concatenate(all_preds)
    all_masks = np.concatenate(all_masks)
    
    acc = accuracy_score(all_masks, all_preds)
    precision = precision_score(all_masks, all_preds, zero_division=0)
    recall = recall_score(all_masks, all_preds, zero_division=0)
    f1 = f1_score(all_masks, all_preds, zero_division=0)
    
    print("\n" + "="*50)
    print("EVALUATION RESULTS (CHANGE DETECTION)")
    print("="*50)
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("="*50)
    
    # Visualizations
    if args.num_visualizations > 0:
        print("\nGenerating visualizations...")
        out_dir = PROJECT_ROOT / "data" / "benchmark" / "real" / "visualizations_unet_retrained"
        out_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(len(vis_t1)):
            fig, axs = plt.subplots(1, 4, figsize=(20, 5))
            
            img_rgb_t1 = vis_t1[i][RGB_BANDS].transpose(1, 2, 0)
            img_rgb_t1 = np.clip(img_rgb_t1 * 3.0, 0, 1)
            
            img_rgb_t2 = vis_t2[i][RGB_BANDS].transpose(1, 2, 0)
            img_rgb_t2 = np.clip(img_rgb_t2 * 3.0, 0, 1)
            
            axs[0].imshow(img_rgb_t1)
            axs[0].set_title("T1 RGB")
            axs[0].axis("off")
            
            axs[1].imshow(img_rgb_t2)
            axs[1].set_title("T2 RGB")
            axs[1].axis("off")
            
            axs[2].imshow(vis_masks[i], cmap='gray', vmin=0, vmax=1)
            axs[2].set_title("Ground Truth Change")
            axs[2].axis("off")
            
            axs[3].imshow(vis_preds[i], cmap='gray', vmin=0, vmax=1)
            axs[3].set_title("Siamese Predicted Change")
            axs[3].axis("off")
            
            plt.tight_layout()
            save_path = out_dir / f"change_patch_{i}.png"
            plt.savefig(save_path)
            plt.close()
            
        print(f"Saved {len(vis_t1)} visualizations to {out_dir}")

if __name__ == "__main__":
    main()
