"""
GeoSentinel AI - Siamese U-Net Evaluation Script
Evaluates the trained Siamese U-Net model on the OSCD dataset.
Generates metrics (OA, Kappa, mIoU, F1, Precision, Recall) for Change Detection.
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix
import lightning as L

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.siamese import GeoSentinelSiameseUNet
from scripts.train_change import OSCDDataModule

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
    parser.add_argument("--weights", type=str, default="data/weights/change_unet_best.pt")
    parser.add_argument("--deeplab-weights", type=str, default="data/weights/deeplabv3plus_best.pt")
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating on device: {device}")
    
    deeplab_path = PROJECT_ROOT / args.deeplab_weights
    if not deeplab_path.exists():
        print(f"Error: DeepLab weights not found at {deeplab_path}")
        return
        
    weights_path = PROJECT_ROOT / args.weights
    if not weights_path.exists():
        print(f"Error: Siamese weights not found at {weights_path}")
        return
        
    model = GeoSentinelSiameseUNet(str(deeplab_path), num_classes=2)
    
    print(f"Loading weights from {weights_path}")
    checkpoint = torch.load(weights_path, map_location=device, weights_only=True)
    
    state_dict = None
    if "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    elif "model_state_dict" in checkpoint:
        state_dict = checkpoint["model_state_dict"]
    else:
        state_dict = checkpoint
        
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
    
    datamodule = OSCDDataModule(batch_size=args.batch_size, num_workers=4)
    datamodule.setup()
    
    val_loader = datamodule.val_dataloader()
    
    print(f"Starting evaluation on {len(val_loader.dataset)} validation patches...")
    
    all_preds = []
    all_masks = []
    
    with torch.no_grad():
        for i, batch in enumerate(val_loader):
            t1 = batch["t1"].to(device)
            t2 = batch["t2"].to(device)
            masks = batch["mask"].cpu().numpy()
            
            logits = model(t1, t2)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            
            all_preds.append(preds)
            all_masks.append(masks)
            
    all_preds = np.concatenate(all_preds, axis=0)
    all_masks = np.concatenate(all_masks, axis=0)
    
    miou, iou, precision, recall, f1, oa, kappa = compute_metrics(all_masks, all_preds, 2)
    
    print("\n" + "="*50)
    print("SIAMESE U-NET EVALUATION RESULTS")
    print("="*50)
    print(f"Overall Accuracy (OA): {oa:.4f}")
    print(f"Kappa Coefficient:     {kappa:.4f}")
    print(f"Mean IoU:              {miou:.4f}")
    print("-" * 50)
    
    class_names = {0: "Unchanged", 1: "Changed"}
    for class_id, class_name in class_names.items():
        print(f"Class {class_id} ({class_name}):")
        print(f"  IoU:       {iou[class_id]:.4f}")
        print(f"  F1-Score:  {f1[class_id]:.4f}")
        print(f"  Precision: {precision[class_id]:.4f}")
        print(f"  Recall:    {recall[class_id]:.4f}")

if __name__ == "__main__":
    main()
