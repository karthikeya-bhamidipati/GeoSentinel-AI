"""
GeoSentinel AI - Siamese U-Net Training for Change Detection (OSCD, 12 channels)

Protocol
--------
* Input stack: the same 12 channels, in the same order and with the same
  clipping, as the land-cover anchor was trained on (src/feature_engineering/
  stack.py): B02, B03, B04, B08, B11, NDVI, NDBI, NDWI, SAVI, EVI, MNDWI, BSI.
  Reflectance = DN / 10 000 clipped to [0, 1]; indices clipped to [-1, 1].
* Validation: three OSCD *training* cities are held out (VAL_CITIES) and tiled
  deterministically. The ten OSCD test cities are never used during training;
  they are scored once afterwards by scripts/evaluate_change_fullscene.py.
"""

import argparse
import random
import sys
from pathlib import Path

import lightning as L
import numpy as np
import rasterio
import torch
import torchvision.transforms.functional as TF
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor
from lightning.pytorch.loggers import CSVLogger
from torch.utils.data import DataLoader, Dataset

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torchgeo.datasets.oscd as oscd_module  # noqa: E402
from torchgeo.datasets import OSCD  # noqa: E402

# Pillow sometimes fails on OSCD TIFFs ("buffer is not large enough"); read them with rasterio.
def _load_image_rasterio(self, paths):
    bands = []
    for path in paths:
        with rasterio.open(path) as src:
            bands.append(src.read(1))
    return torch.from_numpy(np.stack(bands, axis=0))


oscd_module.OSCD._load_image = _load_image_rasterio

from src.models.losses import FocalTverskyLoss  # noqa: E402
from src.models.siamese import GeoSentinelSiameseUNet  # noqa: E402

# Order used by the land-cover anchor (src/feature_engineering/stack.py, EXPECTED_CHANNELS)
CHANNELS = ["B02", "B03", "B04", "B08", "B11", "NDVI", "NDBI", "NDWI", "SAVI", "EVI", "MNDWI", "BSI"]
# OSCD training cities held out for validation (Middle East, Europe, North America)
VAL_CITIES = ("beirut", "bordeaux", "cupertino")
DEFAULT_OSCD_ROOT = PROJECT_ROOT / "data" / "benchmark" / "oscd"
EPS = 1e-10


def oscd_stack(img: torch.Tensor) -> torch.Tensor:
    """13-band OSCD image [13, H, W] (DN, TorchGeo band order B01..B12) -> 12-channel stack."""
    r = (img.float() / 10000.0).clamp(0.0, 1.0)
    blue, green, red, nir, swir1 = r[1], r[2], r[3], r[7], r[11]

    def nd(a, b):
        return ((a - b) / (a + b + EPS)).clamp(-1.0, 1.0)

    ndvi = nd(nir, red)
    ndbi = nd(swir1, nir)
    ndwi = nd(green, nir)
    savi = (1.5 * (nir - red) / (nir + red + 0.5 + EPS)).clamp(-1.0, 1.0)
    evi = (2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0 + EPS)).clamp(-1.0, 1.0)
    mndwi = nd(green, swir1)
    bsi = (((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + EPS)).clamp(-1.0, 1.0)
    out = torch.stack([blue, green, red, nir, swir1, ndvi, ndbi, ndwi, savi, evi, mndwi, bsi])
    return torch.nan_to_num(out, nan=0.0)


def city_name(files_entry) -> str:
    return Path(files_entry["images1"][0]).parent.parent.name


def load_scenes(root: Path, split: str, cities=None, exclude=()):
    """Load OSCD scenes of a split into memory as (name, t1, t2, mask) tuples."""
    ds = OSCD(str(root), split=split, download=False)
    scenes = []
    for i, entry in enumerate(ds.files):
        name = city_name(entry)
        if (cities is not None and name not in cities) or name in exclude:
            continue
        s = ds[i]
        if "image" in s:
            img1, img2 = s["image"][0], s["image"][1]
        else:  # TorchGeo >= 0.7 returns image1 / image2
            img1, img2 = s["image1"], s["image2"]
        mask = (s["mask"].squeeze() == 1).long()
        scenes.append((name, oscd_stack(img1), oscd_stack(img2), mask))
    return scenes


def _pad_to(t, size, value=0):
    h, w = t.shape[-2:]
    ph, pw = max(0, size - h), max(0, size - w)
    if ph or pw:
        t = torch.nn.functional.pad(t, (0, pw, 0, ph), value=value)
    return t


class OSCD12ChannelDataset(Dataset):
    """Random 256-px crops with flip/rot90 augmentation (training) or plain random crops.

    Kept compatible with the evaluation scripts: OSCD12ChannelDataset(root, split, multiplier=...)
    and ._extract_12_channels(img13).
    """

    def __init__(self, root: Path, split="train", crop_size=256, multiplier=50, cities=None,
                 exclude=(), augment=None):
        self.root, self.split, self.crop_size, self.multiplier = Path(root), split, crop_size, multiplier
        self.augment = (split == "train") if augment is None else augment
        self.scenes = load_scenes(self.root, split, cities, exclude)

    @staticmethod
    def _extract_12_channels(img):
        return oscd_stack(img)

    def __len__(self):
        return len(self.scenes) * self.multiplier

    def __getitem__(self, idx):
        _, t1, t2, mask = self.scenes[idx // self.multiplier]
        c = self.crop_size
        t1, t2, mask = _pad_to(t1, c), _pad_to(t2, c), _pad_to(mask, c, value=-1)  # -1 = padding, ignored by the loss
        h, w = mask.shape
        i = int(torch.randint(0, h - c + 1, (1,)))
        j = int(torch.randint(0, w - c + 1, (1,)))
        t1, t2, mask = t1[:, i:i + c, j:j + c], t2[:, i:i + c, j:j + c], mask[i:i + c, j:j + c]
        if self.augment:
            if random.random() > 0.5:
                t1, t2, mask = TF.hflip(t1), TF.hflip(t2), TF.hflip(mask)
            if random.random() > 0.5:
                t1, t2, mask = TF.vflip(t1), TF.vflip(t2), TF.vflip(mask)
            k = random.randint(0, 3)
            if k:
                t1, t2, mask = (torch.rot90(t1, k, (1, 2)), torch.rot90(t2, k, (1, 2)),
                                torch.rot90(mask, k, (0, 1)))
        return {"t1": t1.contiguous(), "t2": t2.contiguous(), "mask": mask.contiguous()}


class TiledDataset(Dataset):
    """Deterministic non-overlapping 256-px tiles covering each scene (validation)."""

    def __init__(self, scenes, tile=256):
        self.items = []
        for _, t1, t2, mask in scenes:
            h, w = mask.shape
            H, W = -(-h // tile) * tile, -(-w // tile) * tile
            t1p = torch.nn.functional.pad(t1, (0, W - w, 0, H - h))
            t2p = torch.nn.functional.pad(t2, (0, W - w, 0, H - h))
            mp = torch.nn.functional.pad(mask, (0, W - w, 0, H - h), value=-1)  # -1 = padding
            for y in range(0, H, tile):
                for x in range(0, W, tile):
                    self.items.append((t1p[:, y:y + tile, x:x + tile].contiguous(),
                                       t2p[:, y:y + tile, x:x + tile].contiguous(),
                                       mp[y:y + tile, x:x + tile].contiguous()))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        t1, t2, m = self.items[i]
        return {"t1": t1, "t2": t2, "mask": m}


class OSCDDataModule(L.LightningDataModule):
    def __init__(self, root=DEFAULT_OSCD_ROOT, batch_size=4, num_workers=4):
        super().__init__()
        self.root, self.batch_size, self.num_workers = Path(root), batch_size, num_workers

    def setup(self, stage=None):
        if getattr(self, "train_ds", None) is not None:
            return
        self.train_ds = OSCD12ChannelDataset(self.root, "train", exclude=VAL_CITIES)
        self.val_ds = TiledDataset(load_scenes(self.root, "train", cities=VAL_CITIES))
        names = sorted({s[0] for s in self.train_ds.scenes})
        print(f"  Train cities ({len(names)}): {', '.join(names)}")
        print(f"  Validation cities: {', '.join(VAL_CITIES)}  ({len(self.val_ds)} tiles)")

    def train_dataloader(self):
        return DataLoader(self.train_ds, batch_size=self.batch_size, shuffle=True, drop_last=True,
                          num_workers=self.num_workers, pin_memory=True,
                          persistent_workers=self.num_workers > 0)

    def val_dataloader(self):
        return DataLoader(self.val_ds, batch_size=self.batch_size, shuffle=False,
                          num_workers=self.num_workers, pin_memory=True,
                          persistent_workers=self.num_workers > 0)


class SiameseLightningModule(L.LightningModule):
    def __init__(self, deeplab_ckpt_path, lr=1e-4, ablation_mode=False):
        super().__init__()
        self.model = GeoSentinelSiameseUNet(deeplab_ckpt_path, num_classes=2, ablation_mode=ablation_mode)
        # ignore_index=-1 excludes padded validation pixels from the loss
        self.loss_fn = FocalTverskyLoss(class_weights=[0.15, 0.85], ignore_index=-1)
        self.lr = lr
        self._val = torch.zeros(3)

    def forward(self, t1, t2):
        return self.model(t1, t2)

    def training_step(self, batch, batch_idx):
        loss = self.loss_fn(self(batch["t1"], batch["t2"]), batch["mask"])
        self.log("train_loss", loss, on_step=False, on_epoch=True)
        return loss

    def on_validation_epoch_start(self):
        self._val = torch.zeros(3, device=self.device)

    def validation_step(self, batch, batch_idx):
        mask = batch["mask"]
        logits = self(batch["t1"], batch["t2"])
        loss = self.loss_fn(logits, mask)
        self.log("val_loss", loss, on_step=False, on_epoch=True, prog_bar=True)
        pred, valid = logits.argmax(1), mask >= 0
        tp = ((pred == 1) & (mask == 1) & valid).sum()
        fp = ((pred == 1) & (mask == 0) & valid).sum()
        fn = ((pred == 0) & (mask == 1) & valid).sum()
        self._val += torch.stack([tp, fp, fn]).float()
        return loss

    def on_validation_epoch_end(self):
        tp, fp, fn = self._val
        self.log("val_f1", 2 * tp / (2 * tp + fp + fn + 1e-9), prog_bar=True)

    def configure_optimizers(self):
        encoder_params = list(self.model.deeplab.parameters()) + list(self.model.unet.encoder.parameters())
        enc_ids = {id(p) for p in encoder_params}
        other_params = [p for p in self.model.parameters() if id(p) not in enc_ids]
        optimizer = torch.optim.AdamW([
            {"params": encoder_params, "lr": self.lr * 0.1},
            {"params": other_params, "lr": self.lr},
        ], weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=5)
        return {"optimizer": optimizer, "lr_scheduler": {"scheduler": scheduler, "monitor": "val_loss"}}


class StateDictCheckpoint(L.Callback):
    """Saves the bare model state_dict (orchestrator / evaluation format) at the best val_loss."""

    def __init__(self, path: Path):
        self.path, self.best = path, float("inf")

    def on_validation_end(self, trainer, pl_module):
        # runs after LightningModule.on_validation_epoch_end, so val_f1 is available
        if trainer.sanity_checking:
            return
        v = trainer.callback_metrics.get("val_loss")
        f1 = trainer.callback_metrics.get("val_f1")
        tl = trainer.callback_metrics.get("train_loss")
        line = f"Epoch {trainer.current_epoch:03d} | val_loss {float(v):.4f} | val_f1 {float(f1):.4f}"
        if tl is not None:
            line += f" | train_loss {float(tl):.4f}"
        if v is not None and float(v) < self.best:
            self.best = float(v)
            torch.save({"model_state_dict": pl_module.model.state_dict(),
                        "epoch": trainer.current_epoch, "val_loss": self.best, "val_f1": float(f1)}, self.path)
            line += "  [saved]"
        print(line, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oscd-root", default=str(DEFAULT_OSCD_ROOT))
    ap.add_argument("--deeplab-ckpt", default=str(PROJECT_ROOT / "data" / "weights" / "deeplabv3plus_best.pt"))
    ap.add_argument("--out-dir", default=str(PROJECT_ROOT / "data" / "weights"))
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--ablation", action="store_true", help="ImageNet-initialised ResNet-50 branch (baseline)")
    args = ap.parse_args()

    L.seed_everything(args.seed, workers=True)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"change_{'baseline' if args.ablation else 'anchor'}_seed{args.seed}"

    if not args.ablation and not Path(args.deeplab_ckpt).exists():
        raise FileNotFoundError(f"Anchor weights not found: {args.deeplab_ckpt}")

    dm = OSCDDataModule(args.oscd_root, args.batch_size, args.num_workers)
    task = SiameseLightningModule(args.deeplab_ckpt, lr=args.lr, ablation_mode=args.ablation)

    trainer = L.Trainer(
        max_epochs=args.epochs,
        accelerator="gpu" if torch.cuda.is_available() else "cpu",
        devices=[args.gpu] if torch.cuda.is_available() else 1,
        precision="32-true",
        callbacks=[
            EarlyStopping(monitor="val_loss", patience=20, mode="min"),
            LearningRateMonitor(logging_interval="epoch"),
            StateDictCheckpoint(out_dir / f"{name}.pt"),
        ],
        logger=CSVLogger(str(out_dir / "logs"), name=name),
        enable_checkpointing=False,
        enable_progress_bar=False,
        log_every_n_steps=10,
    )
    print("=" * 64)
    print(f"  {name}: OSCD change detection training")
    print("=" * 64)
    trainer.fit(task, datamodule=dm)
    print(f"  Best checkpoint: {out_dir / (name + '.pt')}")


if __name__ == "__main__":
    main()
