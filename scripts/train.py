"""
===============================================================================
GeoSentinel AI

Script:
    train.py

Description:
    PyTorch Lightning & TorchGeo training pipeline.
    
    Features:
    - LightningDataModule wrapping BenchmarkDataset
    - TorchGeo SemanticSegmentationTask for distributed/mixed-precision training
    - DeepLabV3+ and U-Net support
    
Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import numpy as np

import torch
import pytorch_lightning as pl
from torch.utils.data import Dataset, DataLoader
from pytorch_lightning.callbacks import LearningRateMonitor

# ── project root on sys.path ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.model_factory import ModelFactory
from src.models.unet import NUM_CLASSES, DEFAULT_IN_CHANNELS

# =============================================================================
# Dataset & DataModule
# =============================================================================

class BenchmarkDataset(Dataset):
    """PyTorch Dataset for the real benchmark .npy patches."""
    def __init__(self, root: Path, augment: bool = False) -> None:
        super().__init__()
        self.root = Path(root)
        self.augment = augment
        self.image_files = sorted(self.root.glob("image_*.npy"))
        if len(self.image_files) == 0:
            raise FileNotFoundError(f"No image files found in {self.root}")

    def __len__(self) -> int:
        return len(self.image_files)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        img_path = self.image_files[idx]
        mask_path = self.root / img_path.name.replace("image_", "mask_")

        image = np.load(img_path)
        mask = np.load(mask_path)

        if self.augment:
            if np.random.random() > 0.5:
                image = np.flip(image, axis=2).copy()
                mask = np.flip(mask, axis=1).copy()
            if np.random.random() > 0.5:
                image = np.flip(image, axis=1).copy()
                mask = np.flip(mask, axis=0).copy()
            k = np.random.randint(0, 4)
            if k > 0:
                image = np.rot90(image, k=k, axes=(1, 2)).copy()
                mask = np.rot90(mask, k=k, axes=(0, 1)).copy()

        # Patches are already float32 and normalized/clipped by PreprocessingPipeline
        image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)

        # TorchGeo tasks expect a dict with 'image' and 'mask' keys
        return {
            "image": torch.from_numpy(image),
            "mask": torch.from_numpy(mask.copy()).long(),
        }

class GeoSentinelDataModule(pl.LightningDataModule):
    def __init__(self, data_dir: Path, batch_size: int = 8, num_workers: int = 0):
        super().__init__()
        self.data_dir = data_dir
        self.batch_size = batch_size
        self.num_workers = num_workers

    def setup(self, stage: str | None = None):
        train_dir = self.data_dir / "train"
        val_dir = self.data_dir / "val"
        if not val_dir.exists():
            val_dir = train_dir
        self.train_ds = BenchmarkDataset(train_dir, augment=True)
        self.val_ds = BenchmarkDataset(val_dir, augment=False)

    def train_dataloader(self):
        return DataLoader(self.train_ds, batch_size=self.batch_size, shuffle=True, num_workers=self.num_workers, drop_last=True)

    def val_dataloader(self):
        return DataLoader(self.val_ds, batch_size=self.batch_size, shuffle=False, num_workers=self.num_workers)

# =============================================================================
# PyTorch Lightning Module Wrapper
# =============================================================================

from src.models.losses import DiceLoss, FocalLoss

class GeoSentinelSegmentationTask(pl.LightningModule):
    def __init__(self, model_type: str, task: str = "land_cover", lr: float = 1e-4):
        super().__init__()
        self.save_hyperparameters()
        
        self.task = task
        in_channels = 6 if task == "change_detection" else DEFAULT_IN_CHANNELS
        num_classes = 2 if task == "change_detection" else NUM_CLASSES

        factory = ModelFactory()
        self.model = factory.create_model(
            model_type=model_type,
            in_channels=in_channels,
            num_classes=num_classes,
            encoder_weights="imagenet"
        )
        self.lr = lr
        
        # Losses
        self.dice = DiceLoss()
        self.focal = FocalLoss(gamma=2.0)
        
        from torchmetrics.classification import MulticlassJaccardIndex
        self.miou = MulticlassJaccardIndex(num_classes=num_classes, ignore_index=0)
        
    def forward(self, x):
        return self.model(x)

    def _shared_step(self, batch, batch_idx):
        if self.task == "change_detection":
            # Stack T1 and T2 to form a 24-channel input
            images = torch.cat([batch["image_t1"], batch["image_t2"]], dim=1)
        else:
            images = batch["image"]
            
        masks = batch["mask"]
        logits = self(images)
        loss = 0.5 * self.dice(logits, masks) + 0.5 * self.focal(logits, masks)
        return loss, logits, masks

    def training_step(self, batch, batch_idx):
        loss, logits, masks = self._shared_step(batch, batch_idx)
        
        preds = torch.argmax(logits, dim=1)
        miou = self.miou(preds, masks)
        
        self.log("train_loss", loss, prog_bar=True, on_step=False, on_epoch=True)
        self.log("train_miou", miou, prog_bar=True, on_step=False, on_epoch=True)
        return loss

    def validation_step(self, batch, batch_idx):
        loss, logits, masks = self._shared_step(batch, batch_idx)
        
        preds = torch.argmax(logits, dim=1)
        
        correct = (preds == masks).sum().float()
        acc = correct / (masks.numel() + 1e-6)
        miou = self.miou(preds, masks)
        
        self.log("val_loss", loss, prog_bar=True, sync_dist=True)
        self.log("val_acc", acc, prog_bar=True, sync_dist=True)
        self.log("val_miou", miou, prog_bar=True, sync_dist=True)
        return loss
        
    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(self.parameters(), lr=self.lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.trainer.max_epochs)
        return {"optimizer": optimizer, "lr_scheduler": scheduler}


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Train GeoSentinel Models (TorchGeo/Lightning)")
    parser.add_argument("--model", type=str, default="unet", choices=["unet", "deeplabv3plus"])
    parser.add_argument("--task", type=str, default="land_cover", choices=["land_cover", "change_detection"])
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data" / "benchmark" / "real")
    parser.add_argument("--epochs", type=int, default=55)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()

    pl.seed_everything(42, workers=True)

    datamodule = GeoSentinelDataModule(args.data_dir, batch_size=args.batch_size)
    task = GeoSentinelSegmentationTask(model_type=args.model, task=args.task, lr=args.lr)

    checkpoint_dir = PROJECT_ROOT / "data" / "weights"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Custom callback to save as {model}_best.pt so orchestrator.py finds it
    class FinalCheckpointCallback(pl.Callback):
        def on_train_end(self, trainer, pl_module):
            save_path = checkpoint_dir / f"{args.model}_best.pt"
            torch.save({"model_state_dict": pl_module.model.state_dict()}, save_path)
            print(f"Saved best model to {save_path}")

    trainer = pl.Trainer(
        max_epochs=args.epochs,
        accelerator="auto",
        devices=1,
        precision="32-true", # Forced FP32 to prevent Sentinel-2 overflows
        callbacks=[FinalCheckpointCallback()],
        logger=False, # Disable wandb/tensorboard for clean stdout
        enable_checkpointing=False, # We use custom callback
    )

    print("=" * 64)
    print(f"  TorchGeo Lightning Pipeline: {args.model.upper()}")
    print("=" * 64)

    trainer.fit(model=task, datamodule=datamodule)

if __name__ == "__main__":
    main()
