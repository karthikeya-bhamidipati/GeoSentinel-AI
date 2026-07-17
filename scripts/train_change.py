"""
GeoSentinel AI - Siamese U-Net Training for Change Detection (OSCD 12-Channel)
"""

import sys
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import lightning as L
from torchgeo.datasets import OSCD
import torchvision.transforms.functional as F
import numpy as np
import random
from lightning.pytorch.callbacks import ModelCheckpoint, LearningRateMonitor, EarlyStopping
try:
    import segmentation_models_pytorch as smp
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.siamese import GeoSentinelSiameseUNet

class OSCD12ChannelDataset(Dataset):
    def __init__(self, root: Path, split="train", crop_size=256, multiplier=50):
        self.root = root
        self.split = split
        self.crop_size = crop_size
        self.multiplier = multiplier
        self.oscd = None
        
    def __len__(self):
        # We hardcode the length to avoid initializing the dataset just to get length.
        # OSCD train has 14 cities, test has 10.
        base_len = 14 if self.split == "train" else 10
        return base_len * self.multiplier
        
    def _extract_12_channels(self, img):
        # img is [13, H, W]
        # TorchGeo OSCD bands: B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B10, B11, B12
        blue = img[1]
        green = img[2]
        red = img[3]
        nir = img[7]
        swir1 = img[11]
        swir2 = img[12]
        
        # 6 physical bands
        bands = torch.stack([blue, green, red, nir, swir1, swir2], dim=0) # [6, H, W]
        
        # 6 indices
        epsilon = 1e-8
        ndvi = (nir - red) / (nir + red + epsilon)
        ndbi = (swir1 - nir) / (swir1 + nir + epsilon)
        ndwi = (green - nir) / (green + nir + epsilon)
        evi = 2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0 + epsilon)
        savi = (nir - red) * 1.5 / (nir + red + 0.5 + epsilon)
        bsi = ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + epsilon)
        
        indices = torch.stack([ndvi, ndbi, ndwi, evi, savi, bsi], dim=0) # [6, H, W]
        return torch.cat([bands, indices], dim=0) # [12, H, W]
        
    def __getitem__(self, idx):
        if self.oscd is None:
            self.oscd = OSCD(str(self.root), split=self.split, download=True)
            
        real_idx = idx // self.multiplier
        item = self.oscd[real_idx]
        
        images = item["image"] # [2, 13, H, W]
        t1 = images[0]
        t2 = images[1]
        mask = item["mask"].squeeze(0) # (H, W) -> 1=Change, 2=No Change
        mask = (mask == 1).long()
        
        t1 = t1.float() / 10000.0
        t2 = t2.float() / 10000.0
        
        t1 = self._extract_12_channels(t1)
        t2 = self._extract_12_channels(t2)
        
        h_img, w_img = t1.shape[1], t1.shape[2]
        if h_img <= self.crop_size or w_img <= self.crop_size:
            pad_h = max(0, self.crop_size - h_img)
            pad_w = max(0, self.crop_size - w_img)
            t1 = torch.nn.functional.pad(t1, (0, pad_w, 0, pad_h))
            t2 = torch.nn.functional.pad(t2, (0, pad_w, 0, pad_h))
            mask = torch.nn.functional.pad(mask, (0, pad_w, 0, pad_h))
            h_img, w_img = self.crop_size, self.crop_size
            
        i, j, h, w = torch.randint(0, h_img - self.crop_size + 1, (1,)), torch.randint(0, w_img - self.crop_size + 1, (1,)), self.crop_size, self.crop_size
        i, j = i.item(), j.item()
        
        t1 = F.crop(t1, i, j, h, w)
        t2 = F.crop(t2, i, j, h, w)
        mask = F.crop(mask.unsqueeze(0), i, j, h, w).squeeze(0)
        
        if random.random() > 0.5:
            t1 = F.hflip(t1)
            t2 = F.hflip(t2)
            mask = F.hflip(mask)
            
        return {
            "t1": t1, # [12, H, W]
            "t2": t2, # [12, H, W]
            "mask": mask
        }

class OSCDDataModule(L.LightningDataModule):
    def __init__(self, batch_size=16, num_workers=12):
        super().__init__()
        self.batch_size = batch_size
        self.num_workers = num_workers
        
    def setup(self, stage=None):
        self.train_ds = OSCD12ChannelDataset(PROJECT_ROOT / "data" / "benchmark" / "oscd", "train")
        self.val_ds = OSCD12ChannelDataset(PROJECT_ROOT / "data" / "benchmark" / "oscd", "test", multiplier=10)
        print(f"  Train samples: {len(self.train_ds)}")
        print(f"  Val samples:   {len(self.val_ds)}")
        
    def train_dataloader(self):
        return DataLoader(self.train_ds, batch_size=self.batch_size, shuffle=True, num_workers=self.num_workers, pin_memory=True, drop_last=True, persistent_workers=True)
        
    def val_dataloader(self):
        return DataLoader(self.val_ds, batch_size=self.batch_size, shuffle=False, num_workers=self.num_workers, pin_memory=True, persistent_workers=True)

class CombinedLoss(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.dice = smp.losses.DiceLoss(mode="multiclass")
        # 10x penalty for missing Class 1 (Change) compared to Class 0
        self.ce = torch.nn.CrossEntropyLoss(weight=torch.tensor([0.1, 0.9]))
        
    def forward(self, logits, mask):
        self.ce.weight = self.ce.weight.to(logits.device)
        return self.dice(logits, mask) + self.ce(logits, mask)

class SiameseLightningModule(L.LightningModule):
    def __init__(self, deeplab_ckpt_path):
        super().__init__()
        self.model = GeoSentinelSiameseUNet(deeplab_ckpt_path, num_classes=2)
        self.loss_fn = CombinedLoss()
        
    def forward(self, t1, t2):
        return self.model(t1, t2)
        
    def training_step(self, batch, batch_idx):
        t1, t2, mask = batch["t1"], batch["t2"], batch["mask"]
        logits = self(t1, t2)
        loss = self.loss_fn(logits, mask)
        self.log("train_loss", loss)
        return loss
        
    def validation_step(self, batch, batch_idx):
        t1, t2, mask = batch["t1"], batch["t2"], batch["mask"]
        logits = self(t1, t2)
        loss = self.loss_fn(logits, mask)
        self.log("val_loss", loss, prog_bar=True)
        return loss
        
    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, self.model.parameters()), lr=1e-4)
        return optimizer

def main():
    L.seed_everything(42, workers=True)
    
    datamodule = OSCDDataModule(batch_size=8, num_workers=4) # Scaled batch size for VRAM, scaled workers to 4 to prevent System RAM exhaustion
    
    checkpoint_dir = PROJECT_ROOT / "data" / "weights"
    deeplab_ckpt = checkpoint_dir / "deeplabv3plus_best.pt"
    if not deeplab_ckpt.exists():
        raise FileNotFoundError("DeepLabV3+ weights not found. Train it first!")
        
    task = SiameseLightningModule(str(deeplab_ckpt))
    
    class OrchestratorCheckpointCallback(L.Callback):
        def __init__(self, save_path: Path):
            self.save_path = save_path
            self.best_val_loss = float("inf")

        def on_validation_epoch_end(self, trainer, pl_module):
            val_loss = trainer.callback_metrics.get("val_loss")
            if val_loss is not None and val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                model_state = pl_module.model.state_dict()
                torch.save({"model_state_dict": model_state}, self.save_path)
                print(f"  [BEST] Saved orchestrator checkpoint: {self.save_path}")

    orch_save_path = checkpoint_dir / "change_unet_best.pt"
    
    callbacks = [
        ModelCheckpoint(
            dirpath=str(checkpoint_dir),
            filename="change_unet_best",
            monitor="val_loss",
            mode="min",
            save_top_k=1,
        ),
        LearningRateMonitor(logging_interval="epoch"),
        EarlyStopping(monitor="val_loss", patience=20, mode="min"),
        OrchestratorCheckpointCallback(orch_save_path)
    ]

    trainer = L.Trainer(
        max_epochs=50,
        accelerator="auto",
        devices=1,
        precision="32-true",
        callbacks=callbacks,
        log_every_n_steps=5,
        enable_progress_bar=True,
    )
    
    print("=" * 64)
    print("  Starting OSCD-only Siamese U-Net Change Detection Training")
    print("=" * 64)
    
    trainer.fit(task, datamodule=datamodule)

if __name__ == "__main__":
    main()
