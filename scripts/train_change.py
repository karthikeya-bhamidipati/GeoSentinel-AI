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
            
        if random.random() > 0.5:
            t1 = F.vflip(t1)
            t2 = F.vflip(t2)
            mask = F.vflip(mask)
            
        # Random Rotation (0, 90, 180, 270)
        rot_angle = random.choice([0, 90, 180, 270])
        if rot_angle > 0:
            t1 = F.rotate(t1, rot_angle)
            t2 = F.rotate(t2, rot_angle)
            # mask has shape [H, W], rotate expects [1, H, W] or [C, H, W]
            mask = F.rotate(mask.unsqueeze(0), rot_angle).squeeze(0)
            
        # Random Brightness/Contrast Jitter on optical bands (first 6 bands)
        if random.random() > 0.5:
            # We apply color jitter individually per image to simulate different lighting conditions
            brightness_factor = random.uniform(0.8, 1.2)
            contrast_factor = random.uniform(0.8, 1.2)
            
            t1[:6] = F.adjust_brightness(t1[:6], brightness_factor)
            t1[:6] = F.adjust_contrast(t1[:6], contrast_factor)
            
            brightness_factor2 = random.uniform(0.8, 1.2)
            contrast_factor2 = random.uniform(0.8, 1.2)
            
            t2[:6] = F.adjust_brightness(t2[:6], brightness_factor2)
            t2[:6] = F.adjust_contrast(t2[:6], contrast_factor2)
            
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

from src.models.losses import FocalTverskyLoss
import argparse

class SiameseLightningModule(L.LightningModule):
    def __init__(self, deeplab_ckpt_path, lr=1e-4, ablation_mode=False):
        super().__init__()
        self.model = GeoSentinelSiameseUNet(deeplab_ckpt_path, num_classes=2, ablation_mode=ablation_mode)
        self.loss_fn = FocalTverskyLoss(class_weights=[0.15, 0.85])
        self.lr = lr
        
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
        # Differential learning rates
        encoder_params = []
        decoder_params = []
        
        # DeepLab is not frozen now
        if hasattr(self.model, "deeplab"):
            encoder_params = list(self.model.deeplab.parameters())
        
        # Unet encoder also
        if hasattr(self.model, "unet"):
            encoder_params += list(self.model.unet.encoder.parameters())
            decoder_params += list(self.model.unet.decoder.parameters()) + list(self.model.unet.segmentation_head.parameters())
            
        # Cross Attention and other fusions
        for name, param in self.model.named_parameters():
            if "cross_attentions" in name or "reducers" in name or "bottleneck" in name:
                decoder_params.append(param)
                
        # Remove duplicates
        encoder_params = list(set(encoder_params))
        decoder_params = list(set(decoder_params))
        
        optimizer = torch.optim.AdamW([
            {"params": encoder_params, "lr": self.lr * 0.1},
            {"params": decoder_params, "lr": self.lr}
        ], weight_decay=1e-4)
        
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=5
        )
        return {"optimizer": optimizer, "lr_scheduler": {"scheduler": scheduler, "monitor": "val_loss"}}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--ablation", action="store_true", help="Run in ablation mode (ImageNet ResNet50 baseline)")
    args = parser.parse_args()

    L.seed_everything(42, workers=True)
    
    datamodule = OSCDDataModule(batch_size=args.batch_size, num_workers=args.num_workers)
    
    checkpoint_dir = PROJECT_ROOT / "data" / "weights"
    deeplab_ckpt = checkpoint_dir / "deeplabv3plus_best.pt"
    if not deeplab_ckpt.exists() and not args.ablation:
        raise FileNotFoundError("DeepLabV3+ weights not found. Train it first!")
        
    task = SiameseLightningModule(str(deeplab_ckpt), ablation_mode=args.ablation)
    
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

    # Determine checkpoint filenames based on ablation mode
    ckpt_filename = "change_unet_baseline_best" if args.ablation else "change_unet_best"
    orch_save_path = checkpoint_dir / f"{ckpt_filename}.pt"
    
    callbacks = [
        ModelCheckpoint(
            dirpath=str(checkpoint_dir),
            filename=ckpt_filename,
            monitor="val_loss",
            mode="min",
            save_top_k=1,
        ),
        LearningRateMonitor(logging_interval="epoch"),
        EarlyStopping(monitor="val_loss", patience=20, mode="min"),
        OrchestratorCheckpointCallback(orch_save_path)
    ]

    trainer = L.Trainer(
        max_epochs=args.epochs,
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
