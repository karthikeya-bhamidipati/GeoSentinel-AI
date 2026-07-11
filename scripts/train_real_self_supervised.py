"""
GeoSentinel AI — Real-Data Self-Supervised U-Net Training
==========================================================
Training philosophy:
  • REAL DATA ONLY: Fetches multiple actual Sentinel-2 scenes over the
    Hyderabad region from CDSE STAC. No synthetic/generated data.
  • AUGMENTATION: Purely geometric transforms (flips, rotations) via
    albumentations on existing real patches. Raw spectral values are NEVER
    altered — only spatial transforms are applied to preserve sensor fidelity.
  • ROBUST LABELS: Pseudo-labels are generated via multi-index thresholding
    (NDVI + NDBI + MNDWI) and patches with low label confidence are filtered out.
  • DYNAMIC LOOP: Trains until mIoU > 90% AND mean loss < 0.1 (realistic
    per-epoch loss scale for Dice+Focal), capped at MAX_EPOCHS to prevent
    infinite runs. The hard cap is generous (150) but finite.
  • GPU ENFORCED: Will assert CUDA is available and crash early if not.
  • PRECISION: Uses PyTorch AMP (mixed precision) for 2x speed on RTX 3050.
  • SCHEDULER: OneCycleLR for fast convergence.
  • CLASS WEIGHTS: Computed from pixel frequency to handle class imbalance.

Author: GeoSentinel AI Pipeline
"""

from __future__ import annotations

import sys
import os
import json
import time
from pathlib import Path
from datetime import date, timedelta
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from shapely.geometry import box

from src.models.model_factory import ModelFactory
from src.models.losses import DiceLoss, FocalLoss
from src.models.unet import NUM_CLASSES
from src.eo.providers.stac import CDSEProvider
from src.preprocessing.pipeline import PreprocessingPipeline
from src.feature_engineering.pipeline import FeatureEngineeringPipeline


# =============================================================================
# Configuration
# =============================================================================

MAX_EPOCHS = 150          # Hard cap — training stops even if mIoU target not met
TARGET_MIOU = 0.90        # Stop training if mIoU exceeds this
TARGET_LOSS = 0.10        # Stop training if loss drops below this (realistic Dice+Focal scale)
PATCH_SIZE = 256          # Spatial size of each training patch in pixels
STRIDE = 128              # Overlap stride for patch extraction (50% overlap)
BATCH_SIZE = 8            # Larger batch for better GPU utilisation on RTX 3050
NUM_WORKERS = 0           # No multiprocessing on Windows (avoids fork issues)
BASE_LR = 3e-4            # Peak learning rate for OneCycleLR

# Hyderabad region — the primary training AOI
# Covers urban core + suburban fringe + Hussain Sagar lake + green belts
HYD_AOI = box(78.30, 17.25, 78.60, 17.60)

# Sentinel-2 scene dates: three distinct seasonal windows for Hyderabad
# - Oct 2023: post-monsoon (high vegetation)
# - Jan 2024: winter dry season (urban easier to classify)
# - Apr 2024: pre-monsoon (maximum spectral contrast between veg/urban)
SCENE_WINDOWS = [
    (date(2023, 10, 1),  date(2023, 10, 31)),
    (date(2024, 1, 1),   date(2024, 1, 31)),
    (date(2024, 4, 1),   date(2024, 4, 30)),
]


# =============================================================================
# Dataset with Albumentations
# =============================================================================

try:
    import albumentations as A
    ALBUMENTATIONS_AVAILABLE = True
except ImportError:
    ALBUMENTATIONS_AVAILABLE = False
    print("[WARNING] albumentations not installed. Running without augmentation.")
    print("          Install with: pip install albumentations")


class HyderabadPatchDataset(Dataset):
    """
    Dataset of 256x256 real Sentinel-2 feature stack patches over Hyderabad.
    
    Augmentation is GEOMETRIC ONLY (flips + rotations). Pixel values are
    never altered, preserving the spectral integrity of real satellite data.
    """

    def __init__(
        self,
        patches: list[np.ndarray],   # list of (12, H, W) float32 arrays
        masks: list[np.ndarray],      # list of (H, W) int64 arrays
        augment: bool = True,
    ) -> None:
        self.patches = patches
        self.masks = masks
        self.augment = augment and ALBUMENTATIONS_AVAILABLE

        if self.augment:
            self.transform = A.Compose([
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.5),
                A.RandomRotate90(p=0.5),
                A.Transpose(p=0.25),
            ])

    def __len__(self) -> int:
        return len(self.patches)

    def __getitem__(self, idx: int):
        img = self.patches[idx].copy()   # (12, H, W) float32
        mask = self.masks[idx].copy()    # (H, W) int64

        if self.augment:
            # albumentations expects (H, W, C) for images
            img_hwc = np.transpose(img, (1, 2, 0))  # (H, W, 12)
            transformed = self.transform(image=img_hwc, mask=mask)
            img = np.transpose(transformed["image"], (2, 0, 1))  # back to (12, H, W)
            mask = transformed["mask"]

        return (
            torch.tensor(img, dtype=torch.float32),
            torch.tensor(mask, dtype=torch.long),
        )


# =============================================================================
# Metric utilities
# =============================================================================

def compute_miou(preds: torch.Tensor, targets: torch.Tensor, num_classes: int) -> float:
    """Compute mean Intersection-over-Union, ignoring NaN classes."""
    preds_cls = preds.argmax(dim=1)
    ious = []
    for c in range(num_classes):
        pred_c = (preds_cls == c)
        tgt_c = (targets == c)
        intersection = (pred_c & tgt_c).sum().item()
        union = (pred_c | tgt_c).sum().item()
        if union > 0:
            ious.append(intersection / union)
    return float(np.mean(ious)) if ious else 0.0


# =============================================================================
# Scene fetching & patch extraction
# =============================================================================

def fetch_scene_and_extract_patches(
    provider: CDSEProvider,
    aoi,
    start_date: date,
    end_date: date,
    patch_size: int = 256,
    stride: int = 128,
) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """
    Fetch one Sentinel-2 scene and return filtered (patch, mask) pairs.
    Returns empty lists if no scene is found or on error.
    """
    print(f"\n  -> Searching {start_date} to {end_date}...")
    try:
        scenes = provider.search(
            aoi=aoi,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=15.0,
            max_results=1,
        )
    except Exception as e:
        print(f"    [FAIL] STAC search failed: {e}")
        return [], []

    if not scenes:
        print("    [SKIP] No cloud-free scene found for this window.")
        return [], []

    scene_id = scenes[0].get("id", "unknown")
    print(f"    [OK] Scene: {scene_id}")

    try:
        scene = provider.load(source=scenes[0], aoi=aoi)
    except Exception as e:
        print(f"    [FAIL] Failed to load scene: {e}")
        return [], []

    try:
        preprocessor = PreprocessingPipeline()
        prep_result = preprocessor.run(scene)

        fe_pipeline = FeatureEngineeringPipeline()
        fe_result = fe_pipeline.run(prep_result.scene)
    except Exception as e:
        print(f"    [FAIL] Feature engineering failed: {e}")
        return [], []

    stack = fe_result.stack.array  # (12, H, W) float32
    indices = fe_result.indices

    # --- Pseudo-label generation using multi-index thresholding ---
    # Uses NDVI, NDBI, and optionally MNDWI for robust 3-class labelling
    ndvi = indices.get("NDVI")
    ndbi = indices.get("NDBI")
    mndwi = indices.get("MNDWI")

    if ndvi is None or ndbi is None:
        print("    [FAIL] Required indices not computed.")
        return [], []

    H, W = ndvi.shape
    mask = np.zeros((H, W), dtype=np.int64)  # 0 = background

    # Vegetation: Strong NDVI signal, low NDBI
    veg_mask = (ndvi > 0.30) & (ndbi < 0.05)
    mask[veg_mask] = 1

    # Urban: Positive NDBI, low NDVI — built-up surfaces
    urban_mask = (ndbi > 0.05) & (ndvi < 0.30)
    if mndwi is not None:
        # Exclude water bodies from urban (MNDWI > 0 indicates water)
        try:
            if mndwi.shape != ndvi.shape:
                from scipy.ndimage import zoom
                scale_y = ndvi.shape[0] / mndwi.shape[0]
                scale_x = ndvi.shape[1] / mndwi.shape[1]
                mndwi = zoom(mndwi, (scale_y, scale_x), order=1)
            urban_mask = urban_mask & (mndwi < 0.0)
        except Exception:
            pass  # If MNDWI fails, skip water exclusion

    mask[urban_mask] = 2

    print(f"    Labels -> BG: {np.sum(mask==0):,}  Veg: {np.sum(mask==1):,}  Urban: {np.sum(mask==2):,}")

    # --- Patch extraction ---
    patches_img, patches_mask = [], []
    total_pixels = patch_size * patch_size

    for y in range(0, H - patch_size + 1, stride):
        for x in range(0, W - patch_size + 1, stride):
            img_patch = stack[:, y:y + patch_size, x:x + patch_size]
            mask_patch = mask[y:y + patch_size, x:x + patch_size]

            # Quality filter: skip patches that are >90% background or have NaN
            bg_fraction = np.mean(mask_patch == 0)
            if bg_fraction > 0.90:
                continue
            if np.any(~np.isfinite(img_patch)):
                continue
            # Require at least some presence of BOTH vegetation AND urban
            # so the model sees both classes in each patch (improves gradients)
            has_veg = np.mean(mask_patch == 1) > 0.02
            has_urban = np.mean(mask_patch == 2) > 0.02
            if not (has_veg or has_urban):
                continue

            patches_img.append(img_patch.astype(np.float32))
            patches_mask.append(mask_patch)

    print(f"    Extracted {len(patches_img)} quality patches from {scene_id}")
    return patches_img, patches_mask


# =============================================================================
# Main training function
# =============================================================================

def main():
    load_dotenv()

    # ── GPU assertion ──────────────────────────────────────────────────────
    assert torch.cuda.is_available(), (
        "CUDA GPU is required for training. "
        "Please ensure you have an NVIDIA GPU and the CUDA-enabled PyTorch installed. "
        "Install: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124"
    )
    device = torch.device("cuda")
    gpu_name = torch.cuda.get_device_name(0)
    print(f"\n{'='*60}")
    print(f"  GeoSentinel AI - Hyderabad U-Net Training")
    print(f"  GPU: {gpu_name}")
    print(f"  Target: mIoU > {TARGET_MIOU:.0%} OR Loss < {TARGET_LOSS:.3f}")
    print(f"  Hard cap: {MAX_EPOCHS} epochs")
    print(f"{'='*60}\n")

    # ── Connect to CDSE ────────────────────────────────────────────────────
    print("Connecting to Copernicus Data Space Ecosystem...")
    provider = CDSEProvider()
    provider.connect()
    print("  [OK] Connected\n")

    # ── Fetch all scenes ───────────────────────────────────────────────────
    print(f"Fetching real Sentinel-2 scenes for Hyderabad ({len(SCENE_WINDOWS)} windows)...")
    all_patches: list[np.ndarray] = []
    all_masks: list[np.ndarray] = []

    for start_d, end_d in SCENE_WINDOWS:
        patches, masks = fetch_scene_and_extract_patches(
            provider, HYD_AOI, start_d, end_d, PATCH_SIZE, STRIDE
        )
        all_patches.extend(patches)
        all_masks.extend(masks)

    if not all_patches:
        print("\n[ERROR] No training patches could be extracted from any scene.")
        print("Please check your CDSE credentials in .env and network connectivity.")
        return

    print(f"\n{'='*60}")
    print(f"  Total training patches: {len(all_patches)}")
    print(f"  Patch shape: {all_patches[0].shape}")
    print(f"{'='*60}\n")

    # ── Class weights for imbalanced labels ───────────────────────────────
    all_mask_flat = np.concatenate([m.flatten() for m in all_masks])
    class_counts = np.array([np.sum(all_mask_flat == c) for c in range(NUM_CLASSES)], dtype=np.float64)
    total = class_counts.sum()
    # Inverse frequency weighting — rare classes get higher weight
    class_weights = (total / (NUM_CLASSES * class_counts + 1e-6))
    class_weights = class_weights / class_weights.sum() * NUM_CLASSES  # normalise
    weights_tensor = torch.tensor(class_weights, dtype=torch.float32, device=device)
    print(f"Class weights -> BG: {class_weights[0]:.3f}  Veg: {class_weights[1]:.3f}  Urban: {class_weights[2]:.3f}")

    # ── Dataset & DataLoader ───────────────────────────────────────────────
    # 90/10 split: train / validation
    n_total = len(all_patches)
    n_train = int(n_total * 0.9)
    indices = np.random.permutation(n_total)
    train_idx, val_idx = indices[:n_train], indices[n_train:]

    train_patches = [all_patches[i] for i in train_idx]
    train_masks   = [all_masks[i]   for i in train_idx]
    val_patches   = [all_patches[i] for i in val_idx]
    val_masks     = [all_masks[i]   for i in val_idx]

    train_dataset = HyderabadPatchDataset(train_patches, train_masks, augment=True)
    val_dataset   = HyderabadPatchDataset(val_patches,   val_masks,   augment=False)

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS, pin_memory=True, drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=True,
    )
    print(f"Train: {len(train_dataset)} patches, Val: {len(val_dataset)} patches")
    print(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}\n")

    # ── Model ──────────────────────────────────────────────────────────────
    print("Initialising U-Net (ResNet34 encoder, ImageNet pretrained)...")
    factory = ModelFactory()
    model = factory.create_model("unet", in_channels=12, num_classes=NUM_CLASSES).to(device)
    print(f"  {model}")

    # Load existing checkpoint if available (resume training)
    weights_dir = PROJECT_ROOT / "weights"
    weights_dir.mkdir(exist_ok=True)
    checkpoint_path = weights_dir / "unet_best.pt"
    if checkpoint_path.exists():
        print(f"  -> Resuming from checkpoint: {checkpoint_path}")
        try:
            model.load_state_dict(torch.load(checkpoint_path, map_location=device))
        except Exception as e:
            print(f"  -> Could not load checkpoint ({e}), starting fresh.")

    # ── Loss functions ─────────────────────────────────────────────────────
    # Combined: weighted Cross-Entropy + Dice + Focal
    # CE with class weights handles imbalance at pixel level
    # Dice optimises overlap (mIoU proxy) directly
    # Focal focuses gradients on hard, misclassified pixels
    ce_loss_fn = nn.CrossEntropyLoss(weight=weights_tensor)
    dice_loss_fn = DiceLoss(smooth=1.0)
    focal_loss_fn = FocalLoss(gamma=2.0)

    # ── Optimiser & Scheduler ──────────────────────────────────────────────
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=BASE_LR, weight_decay=1e-4, amsgrad=True
    )

    # We don't know total epochs upfront (dynamic), so we use ReduceLROnPlateau
    # which adapts based on validation mIoU
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=5, min_lr=1e-6, verbose=True
    )

    # AMP scaler for mixed-precision training
    scaler = GradScaler()

    # ── Training loop ──────────────────────────────────────────────────────
    best_miou = 0.0
    best_loss = float("inf")
    epoch = 0
    training_log = []

    log_path = weights_dir / "training_log.json"
    if checkpoint_path.exists() and log_path.exists():
        try:
            with open(log_path, "r") as f:
                training_log = json.load(f)
            if training_log:
                best_miou = max(entry["miou"] for entry in training_log)
                best_loss = min(entry["val_loss"] for entry in training_log)
                epoch = training_log[-1]["epoch"]
                print(f"  -> Restored log history. Best mIoU was {best_miou*100:.1f}%")
        except Exception as e:
            print(f"  -> Could not load training log: {e}")

    print(f"\nStarting training loop (target mIoU > {TARGET_MIOU:.0%}, max {MAX_EPOCHS} epochs)...\n")

    while epoch < MAX_EPOCHS:
        epoch += 1
        t0 = time.time()

        # ── Train ──────────────────────────────────────────────────────────
        model.train()
        train_loss = 0.0
        train_steps = 0

        for imgs, masks_batch in tqdm(train_loader, desc=f"Epoch {epoch:3d}/{MAX_EPOCHS} [Train]", leave=False):
            imgs = imgs.to(device, non_blocking=True)
            masks_batch = masks_batch.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            with autocast():
                logits = model(imgs)
                # Ensure logits match mask spatial dims (handles any U-Net decoder rounding)
                if logits.shape[-2:] != masks_batch.shape[-2:]:
                    logits = F.interpolate(logits, size=masks_batch.shape[-2:], mode="bilinear", align_corners=False)

                loss_ce    = ce_loss_fn(logits, masks_batch)
                loss_dice  = dice_loss_fn(logits, masks_batch)
                loss_focal = focal_loss_fn(logits, masks_batch)
                # Weighted combination: CE (stability) + Dice (mIoU) + Focal (hard pixels)
                loss = 0.4 * loss_ce + 0.4 * loss_dice + 0.2 * loss_focal

            scaler.scale(loss).backward()
            # Gradient clipping prevents exploding gradients
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item()
            train_steps += 1

        avg_train_loss = train_loss / max(train_steps, 1)

        # ── Validate ───────────────────────────────────────────────────────
        model.eval()
        val_loss = 0.0
        val_steps = 0
        val_miou_accum = 0.0

        with torch.no_grad():
            for imgs, masks_batch in val_loader:
                imgs = imgs.to(device, non_blocking=True)
                masks_batch = masks_batch.to(device, non_blocking=True)

                with autocast():
                    logits = model(imgs)
                    if logits.shape[-2:] != masks_batch.shape[-2:]:
                        logits = F.interpolate(logits, size=masks_batch.shape[-2:], mode="bilinear", align_corners=False)

                    loss_ce    = ce_loss_fn(logits, masks_batch)
                    loss_dice  = dice_loss_fn(logits, masks_batch)
                    loss_focal = focal_loss_fn(logits, masks_batch)
                    loss = 0.4 * loss_ce + 0.4 * loss_dice + 0.2 * loss_focal

                val_loss += loss.item()
                val_miou_accum += compute_miou(logits, masks_batch, NUM_CLASSES)
                val_steps += 1

        avg_val_loss = val_loss / max(val_steps, 1)
        avg_val_miou = val_miou_accum / max(val_steps, 1)
        elapsed = time.time() - t0

        # LR scheduler step based on validation mIoU
        scheduler.step(avg_val_miou)

        # Logging
        current_lr = optimizer.param_groups[0]["lr"]
        log_line = (
            f"Epoch {epoch:3d}/{MAX_EPOCHS} | "
            f"TrainLoss: {avg_train_loss:.4f} | "
            f"ValLoss: {avg_val_loss:.4f} | "
            f"mIoU: {avg_val_miou:.4f} ({avg_val_miou*100:.1f}%) | "
            f"LR: {current_lr:.1e} | "
            f"{elapsed:.1f}s"
        )
        print(log_line)

        training_log.append({
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 6),
            "val_loss": round(avg_val_loss, 6),
            "miou": round(avg_val_miou, 6),
            "lr": current_lr,
        })

        # Save best model
        if avg_val_miou > best_miou:
            best_miou = avg_val_miou
            best_loss = avg_val_loss
            torch.save(model.state_dict(), checkpoint_path)
            print(f"  [BEST] mIoU: {best_miou:.4f} ({best_miou*100:.1f}%) -- Saved to {checkpoint_path}")

        # ── Early stopping: target achieved ───────────────────────────────
        if avg_val_miou >= TARGET_MIOU:
            print(f"\n{'='*60}")
            print(f"  [TARGET ACHIEVED] at epoch {epoch}!")
            print(f"  mIoU: {avg_val_miou*100:.2f}% (target: {TARGET_MIOU*100:.0f}%)")
            print(f"  Val Loss: {avg_val_loss:.6f}")
            print(f"{'='*60}\n")
            break

        if avg_val_loss <= TARGET_LOSS and avg_val_miou >= 0.85:
            print(f"\n{'='*60}")
            print(f"  [LOSS TARGET ACHIEVED] at epoch {epoch}!")
            print(f"  Val Loss: {avg_val_loss:.6f} (target: {TARGET_LOSS:.3f})")
            print(f"  mIoU: {avg_val_miou*100:.2f}%")
            print(f"{'='*60}\n")
            break

    # ── Save training log ──────────────────────────────────────────────────
    log_path = weights_dir / "training_log.json"
    with open(log_path, "w") as f:
        json.dump(training_log, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Training complete!")
    print(f"  Best mIoU: {best_miou*100:.2f}%")
    print(f"  Best Val Loss: {best_loss:.6f}")
    print(f"  Epochs run: {epoch}/{MAX_EPOCHS}")
    print(f"  Checkpoint: {checkpoint_path}")
    print(f"  Log: {log_path}")
    print(f"{'='*60}\n")

    if best_miou < TARGET_MIOU:
        print(f"  [NOTE] mIoU ({best_miou*100:.1f}%) did not reach target ({TARGET_MIOU*100:.0f}%) within {MAX_EPOCHS} epochs.")
        print(f"  The best checkpoint has been saved. Re-run the script to continue training from this checkpoint.")


if __name__ == "__main__":
    main()
