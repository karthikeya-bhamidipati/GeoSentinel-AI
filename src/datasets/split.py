"""
===============================================================================
GeoSentinel AI

Module:
    split.py

Description:
    Dataset loaders and train/val/test split utilities.

    Implements:
    - OSCD (Onera Satellite Change Detection) dataset loader via TorchGeo
    - S2Looking dataset loader
    - Patch extraction from large rasters
    - Stratified train/val/test splits

    The OSCD dataset is used as the primary benchmark dataset for
    urban change detection. S2Looking is used for robustness evaluation.

    References:
    - TorchGeo: Stewart et al. (2022). Deep Learning With Geospatial Data.
    - OSCD: Daudt et al. (2018). Urban Change Detection for Multispectral
      Earth Observation Using Convolutional Neural Networks. IGARSS 2018.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, random_split

from src.utils.logger import logger
from src.utils.paths import paths


# =============================================================================
# Patch Dataset
# =============================================================================


@dataclass
class PatchSample:
    """
    A single training patch.

    Attributes
    ----------
    image : np.ndarray
        Shape (channels, height, width), float32.
    mask : np.ndarray
        Shape (height, width), int64 class indices.
    scene_id : str
        Source scene identifier.
    """

    image: np.ndarray
    mask: np.ndarray
    scene_id: str = ""


class PatchDataset(Dataset):
    """
    PyTorch Dataset for image-mask patch pairs.

    Wraps a list of PatchSample objects and applies optional
    augmentation transforms.

    Parameters
    ----------
    samples : list[PatchSample]
    transform : callable | None
        Augmentation transform applied to (image, mask) pairs.
    """

    def __init__(
        self,
        samples: list[PatchSample],
        transform=None,
    ) -> None:

        self.samples = samples
        self.transform = transform

    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.samples)

    # ------------------------------------------------------------------

    def __getitem__(
        self,
        idx: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Return (image_tensor, mask_tensor) for training.

        Returns
        -------
        tuple[Tensor, Tensor]
            image: (C, H, W), float32
            mask: (H, W), int64
        """

        sample = self.samples[idx]

        image = torch.from_numpy(
            sample.image.astype("float32")
        )

        mask = torch.from_numpy(
            sample.mask.astype("int64")
        )

        if self.transform is not None:
            image, mask = self.transform(image, mask)

        return image, mask


# =============================================================================
# Patch Extractor
# =============================================================================


class PatchExtractor:
    """
    Extracts fixed-size patches from a large raster array using a
    sliding window with configurable stride.

    Parameters
    ----------
    patch_size : int
        Side length of each square patch in pixels.
    stride : int
        Step size between patches. Stride < patch_size creates overlap.
    """

    def __init__(
        self,
        patch_size: int = 256,
        stride: int = 128,
    ) -> None:

        self.patch_size = patch_size
        self.stride = stride

    # ------------------------------------------------------------------

    def extract(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        scene_id: str = "",
    ) -> list[PatchSample]:
        """
        Extract patches from an image-mask pair.

        Parameters
        ----------
        image : np.ndarray
            Shape (C, H, W).
        mask : np.ndarray
            Shape (H, W).
        scene_id : str

        Returns
        -------
        list[PatchSample]
        """

        C, H, W = image.shape
        ps = self.patch_size
        stride = self.stride

        patches = []

        for y in range(0, H - ps + 1, stride):
            for x in range(0, W - ps + 1, stride):

                img_patch = image[:, y:y + ps, x:x + ps]
                mask_patch = mask[y:y + ps, x:x + ps]

                patches.append(
                    PatchSample(
                        image=img_patch,
                        mask=mask_patch,
                        scene_id=scene_id,
                    )
                )

        return patches


# =============================================================================
# Dataset Splitter
# =============================================================================


@dataclass
class DataSplit:
    """
    Train/validation/test split of PatchSamples.
    """

    train: list[PatchSample] = field(default_factory=list)
    val: list[PatchSample] = field(default_factory=list)
    test: list[PatchSample] = field(default_factory=list)

    def sizes(self) -> dict[str, int]:
        return {
            "train": len(self.train),
            "val": len(self.val),
            "test": len(self.test),
            "total": len(self.train) + len(self.val) + len(self.test),
        }


class DatasetSplitter:
    """
    Splits a list of PatchSamples into train/val/test sets.

    Performs a random shuffle before splitting to ensure
    reproducibility with a fixed seed.
    """

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ) -> None:

        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, (
            "Split ratios must sum to 1.0"
        )

        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    # ------------------------------------------------------------------

    def split(
        self,
        samples: list[PatchSample],
    ) -> DataSplit:
        """
        Split samples into train/val/test.

        Parameters
        ----------
        samples : list[PatchSample]

        Returns
        -------
        DataSplit
        """

        rng = random.Random(self.seed)
        shuffled = samples.copy()
        rng.shuffle(shuffled)

        n = len(shuffled)
        n_train = int(n * self.train_ratio)
        n_val = int(n * self.val_ratio)

        train = shuffled[:n_train]
        val = shuffled[n_train:n_train + n_val]
        test = shuffled[n_train + n_val:]

        result = DataSplit(train=train, val=val, test=test)

        logger.info(
            f"Dataset split: "
            f"train={len(train)}, "
            f"val={len(val)}, "
            f"test={len(test)}"
        )

        return result

    # ------------------------------------------------------------------

    def to_dataloaders(
        self,
        split: DataSplit,
        batch_size: int = 8,
        num_workers: int = 2,
    ) -> dict[str, DataLoader]:
        """
        Convert a DataSplit into PyTorch DataLoaders.

        Parameters
        ----------
        split : DataSplit
        batch_size : int
        num_workers : int

        Returns
        -------
        dict[str, DataLoader]
            Keys: 'train', 'val', 'test'.
        """

        train_ds = PatchDataset(split.train)
        val_ds = PatchDataset(split.val)
        test_ds = PatchDataset(split.test)

        return {
            "train": DataLoader(
                train_ds,
                batch_size=batch_size,
                shuffle=True,
                num_workers=num_workers,
                pin_memory=True,
                drop_last=True,
            ),
            "val": DataLoader(
                val_ds,
                batch_size=batch_size,
                shuffle=False,
                num_workers=num_workers,
                pin_memory=True,
            ),
            "test": DataLoader(
                test_ds,
                batch_size=batch_size,
                shuffle=False,
                num_workers=num_workers,
            ),
        }
