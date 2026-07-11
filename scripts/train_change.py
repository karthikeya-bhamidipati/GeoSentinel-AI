"""
GeoSentinel AI - Multi-Task Training: Change Detection (OSCD + S2Looking)
"""

import sys
from pathlib import Path
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, ConcatDataset
import pytorch_lightning as pl
from datasets import load_from_disk
from torchgeo.datasets import OSCD
import torchvision.transforms.functional as F
import numpy as np
import random
import argparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.train import GeoSentinelSegmentationTask

class S2LookingDataset(Dataset):
    def __init__(self, root: Path, split="train", crop_size=256):
        self.ds = load_from_disk(str(root))[split]
        self.crop_size = crop_size
        
    def __len__(self):
        return len(self.ds)

    def __getitem__(self, idx):
        item = self.ds[idx]
        
        # PIL Images
        t1 = np.array(item["t1_image"]) # (H, W, 3)
        t2 = np.array(item["t2_image"]) # (H, W, 3)
        mask = np.array(item["change_mask"]) # (H, W) -> 0 or 255
        
        # Convert to Tensor
        t1 = torch.from_numpy(t1).permute(2, 0, 1).float() / 255.0
        t2 = torch.from_numpy(t2).permute(2, 0, 1).float() / 255.0
        mask = torch.from_numpy(mask).long()
        mask = (mask > 127).long() # Binary 0/1
        
        # Random Crop
        i, j, h, w = torch.randint(0, t1.shape[1] - self.crop_size + 1, (1,)), torch.randint(0, t1.shape[2] - self.crop_size + 1, (1,)), self.crop_size, self.crop_size
        i, j = i.item(), j.item()
        
        t1 = F.crop(t1, i, j, h, w)
        t2 = F.crop(t2, i, j, h, w)
        mask = F.crop(mask.unsqueeze(0), i, j, h, w).squeeze(0)
        
        # Data Augmentation (Random Flip)
        if random.random() > 0.5:
            t1 = F.hflip(t1)
            t2 = F.hflip(t2)
            mask = F.hflip(mask)
            
        if random.random() > 0.5:
            t1 = F.vflip(t1)
            t2 = F.vflip(t2)
            mask = F.vflip(mask)
            
        return {
            "image_t1": t1,
            "image_t2": t2,
            "mask": mask
        }

class OSCDRGBDataset(Dataset):
    def __init__(self, root: Path, split="train", crop_size=256, multiplier=50):
        self.oscd = OSCD(str(root), split=split, download=False)
        self.crop_size = crop_size
        self.multiplier = multiplier # Sample multiple crops per large OSCD image
        
    def __len__(self):
        return len(self.oscd) * self.multiplier
        
    def __getitem__(self, idx):
        # Map idx to real image index
        real_idx = idx // self.multiplier
        item = self.oscd[real_idx]
        
        # OSCD is shape (2, 13, H, W). RGB are indices 3 (Red), 2 (Green), 1 (Blue)
        images = item["image"]
        
        t1 = images[0, [3, 2, 1], :, :] # (3, H, W)
        t2 = images[1, [3, 2, 1], :, :]
        mask = item["mask"].squeeze(0) # (H, W) -> 1=Change, 2=No Change
        
        # OSCD mask uses 1 for change, 2 for no change. Map to 0/1.
        mask = (mask == 1).long()
        
        # Normalize (OSCD values are unscaled Sentinel-2, approx 0-10000)
        t1 = t1.float() / 10000.0
        t2 = t2.float() / 10000.0
        
        # Crop
        h_img, w_img = t1.shape[1], t1.shape[2]
        if h_img <= self.crop_size or w_img <= self.crop_size:
            # Pad if too small
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
            "image_t1": torch.clamp(t1, 0, 1),
            "image_t2": torch.clamp(t2, 0, 1),
            "mask": mask
        }

class CombinedChangeDataModule(pl.LightningDataModule):
    def __init__(self, batch_size=8, num_workers=0):
        super().__init__()
        self.batch_size = batch_size
        self.num_workers = num_workers
        
    def setup(self, stage=None):
        s2_train = S2LookingDataset(PROJECT_ROOT / "data" / "benchmark" / "s2looking", "train")
        s2_val = S2LookingDataset(PROJECT_ROOT / "data" / "benchmark" / "s2looking", "val")
        
        oscd_train = OSCDRGBDataset(PROJECT_ROOT / "data" / "benchmark" / "oscd", "train")
        oscd_val = OSCDRGBDataset(PROJECT_ROOT / "data" / "benchmark" / "oscd", "test", multiplier=10)
        
        self.train_ds = ConcatDataset([s2_train, oscd_train])
        self.val_ds = ConcatDataset([s2_val, oscd_val])
        
    def train_dataloader(self):
        return DataLoader(self.train_ds, batch_size=self.batch_size, shuffle=True, num_workers=self.num_workers)
        
    def val_dataloader(self):
        return DataLoader(self.val_ds, batch_size=self.batch_size, shuffle=False, num_workers=self.num_workers)

def main():
    pl.seed_everything(42, workers=True)
    
    datamodule = CombinedChangeDataModule(batch_size=8)
    
    # task="change_detection" sets in_channels=6 and num_classes=2 automatically!
    model = GeoSentinelSegmentationTask(model_type="unet", task="change_detection", lr=1e-4)
    
    checkpoint_dir = PROJECT_ROOT / "data" / "weights"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    class FinalCheckpointCallback(pl.Callback):
        def on_train_end(self, trainer, pl_module):
            save_path = checkpoint_dir / "change_unet_best.pt"
            torch.save({"model_state_dict": pl_module.model.state_dict()}, save_path)
            print(f"Saved Siamese U-Net model to {save_path}")

    trainer = pl.Trainer(
        max_epochs=20,
        accelerator="auto",
        devices=1,
        precision="32-true",
        callbacks=[FinalCheckpointCallback()],
        logger=False,
        enable_checkpointing=False,
    )
    
    print("=" * 64)
    print("  Starting OSCD + S2Looking Multi-Task Change Detection Training")
    print("=" * 64)
    
    trainer.fit(model, datamodule=datamodule)

if __name__ == "__main__":
    main()
