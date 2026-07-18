"""
===============================================================================
GeoSentinel AI

Module:
    predictor.py

Description:
    Scene predictor — runs tiled inference on a full FeatureStack.

    Orchestrates tile extraction → batch inference → tile merging.
    Returns the full-scene segmentation mask and probability map.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

from src.feature_engineering.stack import FeatureStack
from src.inference.tiling import TileExtractor, Tile
from src.inference.merge import TileMerger
from src.models.unet import NUM_CLASSES
from src.eo.exceptions import ModelInferenceError
from src.utils.logger import logger


@dataclass
class PredictionResult:
    """
    Output of the scene predictor.

    Attributes
    ----------
    mask : np.ndarray
        Shape (H, W), int32 class indices.
    probabilities : np.ndarray
        Shape (num_classes, H, W), float32 class probabilities.
    confidence : np.ndarray
        Shape (H, W), float32 max probability per pixel.
    mean_confidence : float
        Spatial mean confidence score.
    """

    mask: np.ndarray
    probabilities: np.ndarray
    confidence: np.ndarray
    mean_confidence: float

    def summary(self) -> dict:

        unique, counts = np.unique(self.mask, return_counts=True)

        return {
            "shape": list(self.mask.shape),
            "num_classes_present": int(len(unique)),
            "mean_confidence": round(float(self.mean_confidence), 4),
            "class_distribution": {
                int(k): int(v) for k, v in zip(unique, counts)
            },
        }


class ScenePredictor:
    """
    Runs segmentation inference on a full-scene FeatureStack.

    Uses tiled inference with overlap merging to handle scenes
    of arbitrary size. Supports both CPU and GPU inference.

    Parameters
    ----------
    model : nn.Module
        A trained GeoSentinelUNet or compatible model.
    tile_size : int
        Inference tile size (must match model input).
    stride : int
        Tile stride. Lower values = more overlap = smoother output.
    device : str
        'cuda' or 'cpu'.
    batch_size : int
        Number of tiles per inference batch.
    """

    def __init__(
        self,
        model: nn.Module,
        tile_size: int = 256,
        stride: int = 192,
        device: str = "cpu",
        batch_size: int = 4,
        num_classes: int = NUM_CLASSES,
    ) -> None:

        self.model = model
        self.tile_size = tile_size
        self.stride = stride
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.device = torch.device(device)

        self._tile_extractor = TileExtractor(
            tile_size=tile_size,
            stride=stride,
        )

        self.model.eval()
        self.model.to(self.device)

    # ------------------------------------------------------------------

    def predict(
        self,
        feature_stack: FeatureStack,
    ) -> PredictionResult:
        """
        Run tiled inference on a FeatureStack.

        Parameters
        ----------
        feature_stack : FeatureStack

        Returns
        -------
        PredictionResult
        """

        logger.info(
            f"Running inference: {feature_stack.height}x"
            f"{feature_stack.width}, "
            f"{feature_stack.n_channels} channels"
        )

        try:
            return self._predict_tiled(feature_stack)

        except Exception as exc:
            raise ModelInferenceError(
                f"Scene inference failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------

    def _predict_tiled(
        self,
        feature_stack: FeatureStack,
    ) -> PredictionResult:
        """
        Internal tiled prediction logic.
        """

        array = feature_stack.array  # (C, H, W)
        C, H, W = array.shape

        tiles, _ = self._tile_extractor.extract(array, pad_if_needed=True)

        merger = TileMerger(
            output_height=H,
            output_width=W,
            num_classes=self.num_classes,
        )

        # Process tiles in batches
        for batch_start in range(0, len(tiles), self.batch_size):
            batch_tiles = tiles[batch_start:batch_start + self.batch_size]

            batch_arrays = np.stack(
                [t.array for t in batch_tiles], axis=0
            )  # (B, C, H, W)

            batch_tensor = torch.from_numpy(
                batch_arrays.astype("float32")
            ).to(self.device)

            with torch.no_grad():
                logits = self.model(batch_tensor)
                probs = torch.softmax(logits, dim=1)

            probs_np = probs.cpu().numpy()

            for i, tile in enumerate(batch_tiles):
                merger.add_tile(tile, probs_np[i])

        # Crop output back to original scene size (remove padding)
        prediction = merger.get_prediction()[:H, :W]
        probabilities = merger.get_probabilities()[:, :H, :W]
        
        # Merge Agriculture (5) into Vegetation (2) as they are visually similar
        prediction[prediction == 5] = 2

        confidence = probabilities.max(axis=0)
        mean_confidence = float(confidence.mean())

        logger.info(
            f"Inference complete. "
            f"Mean confidence: {mean_confidence:.3f}"
        )

        return PredictionResult(
            mask=prediction,
            probabilities=probabilities,
            confidence=confidence,
            mean_confidence=mean_confidence,
        )

    # ------------------------------------------------------------------

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: Path,
        model: nn.Module,
        device: str = "cpu",
        **kwargs,
    ) -> "ScenePredictor":
        """
        Load a predictor from a saved checkpoint.

        Parameters
        ----------
        checkpoint_path : Path
        model : nn.Module
            Uninitialized model with matching architecture.
        device : str
        **kwargs
            Additional arguments passed to ScenePredictor.

        Returns
        -------
        ScenePredictor
        """

        checkpoint = torch.load(
            checkpoint_path,
            map_location=device,
        )

        # Handle both nested dictionaries (old style) and direct state_dicts (new style)
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)

        logger.info(
            f"Loaded checkpoint: {checkpoint_path.name}"
        )

        return cls(model=model, device=device, **kwargs)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"ScenePredictor("
            f"tile={self.tile_size}, "
            f"stride={self.stride}, "
            f"device={self.device})"
        )

class SiameseScenePredictor:
    """
    Runs dual-input change detection inference on two FeatureStacks (T1 and T2).
    """

    def __init__(
        self,
        model: nn.Module,
        tile_size: int = 256,
        stride: int = 192,
        device: str = "cpu",
        batch_size: int = 4,
        num_classes: int = 2,
    ) -> None:

        self.model = model
        self.tile_size = tile_size
        self.stride = stride
        self.batch_size = batch_size
        self.num_classes = num_classes
        self.device = torch.device(device)

        self._tile_extractor = TileExtractor(
            tile_size=tile_size,
            stride=stride,
        )

        self.model.eval()
        self.model.to(self.device)

    def predict(
        self,
        feature_stack_t1: FeatureStack,
        feature_stack_t2: FeatureStack,
    ) -> PredictionResult:
        logger.info(
            f"Running Siamese inference: {feature_stack_t1.height}x"
            f"{feature_stack_t1.width}"
        )

        array_t1 = feature_stack_t1.array
        array_t2 = feature_stack_t2.array
        _, H, W = array_t1.shape

        tiles_t1, _ = self._tile_extractor.extract(array_t1, pad_if_needed=True)
        tiles_t2, _ = self._tile_extractor.extract(array_t2, pad_if_needed=True)

        merger = TileMerger(
            output_height=H,
            output_width=W,
            num_classes=self.num_classes,
        )

        for batch_start in range(0, len(tiles_t1), self.batch_size):
            batch_tiles_t1 = tiles_t1[batch_start:batch_start + self.batch_size]
            batch_tiles_t2 = tiles_t2[batch_start:batch_start + self.batch_size]

            batch_arrays_t1 = np.stack([t.array for t in batch_tiles_t1], axis=0)
            batch_arrays_t2 = np.stack([t.array for t in batch_tiles_t2], axis=0)

            tensor_t1 = torch.from_numpy(batch_arrays_t1.astype("float32")).to(self.device)
            tensor_t2 = torch.from_numpy(batch_arrays_t2.astype("float32")).to(self.device)

            with torch.no_grad():
                logits = self.model(tensor_t1, tensor_t2)
                # Ensure output is explicitly 2-class or 1-class logic handled
                if logits.shape[1] == 1:
                    # BCE format (B, 1, H, W)
                    probs = torch.sigmoid(logits)
                    # Convert to (B, 2, H, W) pseudo-probs for TileMerger
                    probs = torch.cat([1 - probs, probs], dim=1)
                else:
                    probs = torch.softmax(logits, dim=1)

            probs_np = probs.cpu().numpy()

            for i, tile in enumerate(batch_tiles_t1):
                # We use tile coordinates from t1, they are identical for t2
                merger.add_tile(tile, probs_np[i])

        probabilities = merger.get_probabilities()[:, :H, :W]
        # Force a strict 75% confidence threshold for "Change" (class 1)
        # to aggressively suppress false-positive wobble.
        prediction = (probabilities[1] > 0.75).astype(np.int32)

        confidence = probabilities.max(axis=0)
        mean_confidence = float(confidence.mean())

        logger.info(f"Siamese Inference complete. Mean confidence: {mean_confidence:.3f}")

        return PredictionResult(
            mask=prediction,
            probabilities=probabilities,
            confidence=confidence,
            mean_confidence=mean_confidence,
        )

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: Path,
        model: nn.Module,
        device: str = "cpu",
        **kwargs,
    ) -> "SiameseScenePredictor":
        checkpoint = torch.load(checkpoint_path, map_location=device)
        if "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)
        logger.info(f"Loaded siamese checkpoint: {checkpoint_path.name}")
        return cls(model=model, device=device, **kwargs)
