"""
===============================================================================
GeoSentinel AI

Module:
    visualization.py (inference)

Description:
    Colormap and visualization utilities for segmentation outputs.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.models.unet import LAND_COVER_NAMES, LAND_COVER_COLORS
from src.utils.logger import logger


class SegmentationVisualizer:
    """
    Converts segmentation masks to RGB color images and plots.

    Uses the LAND_COVER_COLORS mapping to apply class-specific colors.
    Exports PNG images for display in the dashboard.
    """

    def __init__(self, dpi: int = 150) -> None:
        self.dpi = dpi

    # ------------------------------------------------------------------

    def apply_colormap(
        self,
        mask: np.ndarray,
    ) -> np.ndarray:
        """
        Apply class colormap to a segmentation mask.

        Parameters
        ----------
        mask : np.ndarray
            Shape (H, W), integer class indices.

        Returns
        -------
        np.ndarray
            Shape (H, W, 3), uint8 RGB image.
        """

        H, W = mask.shape
        color_image = np.zeros((H, W, 3), dtype=np.uint8)

        for class_idx, color in LAND_COVER_COLORS.items():
            color_image[mask == class_idx] = color

        return color_image

    # ------------------------------------------------------------------

    def save_mask_png(
        self,
        mask: np.ndarray,
        output_path: Path,
        title: str = "Land Cover Map",
        show_legend: bool = True,
    ) -> Path:
        """
        Save a colorized segmentation mask as a PNG file.

        Parameters
        ----------
        mask : np.ndarray
        output_path : Path
        title : str
        show_legend : bool

        Returns
        -------
        Path
        """

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        color_image = self.apply_colormap(mask)
        
        from PIL import Image
        img = Image.fromarray(color_image, mode="RGB")
        # Upscale 4x (nearest neighbor preserves categorical class colors)
        img = img.resize((img.width * 4, img.height * 4), resample=Image.Resampling.NEAREST)
        img.save(output_path)
        
        logger.info(f"Mask visualization saved: {output_path.name}")
        return output_path

    # ------------------------------------------------------------------

    def save_change_map_png(
        self,
        change_array: np.ndarray,
        output_path: Path,
        title: str = "Change Map",
        vmin: float = -1.0,
        vmax: float = 1.0,
        cmap: str = "RdYlGn",
        **kwargs,
    ) -> Path:
        """
        Save a continuous change raster (NDVI/NDBI delta) as a PNG.

        Parameters
        ----------
        change_array : np.ndarray
            Shape (H, W), float values (e.g., NDVI delta).
        output_path : Path
        title : str
        vmin, vmax : float
            Colormap range.
        cmap : str
            Matplotlib colormap name.

        Returns
        -------
        Path
        """

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
        from PIL import Image

        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        mapper = cm.ScalarMappable(norm=norm, cmap=cmap)
        
        # Apply colormap (returns RGBA floats 0-1)
        rgba = mapper.to_rgba(change_array)
        rgb_uint8 = (rgba[:, :, :3] * 255).astype(np.uint8)
        
        img = Image.fromarray(rgb_uint8, mode="RGB")
        # Upscale 4x (nearest neighbor preserves delta gradients precisely)
        img = img.resize((img.width * 4, img.height * 4), resample=Image.Resampling.NEAREST)
        img.save(output_path)

        logger.info(f"Change map saved: {output_path.name}")

        return output_path

    # ------------------------------------------------------------------

    def save_rgb_png(
        self,
        stack,
        output_path: Path,
        brightness: float = 2.5,
    ) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        r = stack.channel("B04")
        g = stack.channel("B03")
        b = stack.channel("B02")

        rgb = np.dstack([r, g, b])
        
        # Strictly handle NaNs (no-data regions) to prevent color artifacts
        rgb = np.nan_to_num(rgb, nan=0.0)
        
        # Apply brightness and strictly clip to valid [0, 1] range
        rgb = np.clip(rgb * brightness, 0.0, 1.0)
        rgb_uint8 = (rgb * 255).astype(np.uint8)

        from PIL import Image
        img = Image.fromarray(rgb_uint8, mode="RGB")
        # Upscale 4x (nearest neighbor preserves raw pixel boundaries)
        img = img.resize((img.width * 4, img.height * 4), resample=Image.Resampling.NEAREST)
        img.save(output_path)

        logger.info(f"RGB image saved: {output_path.name}")
        return output_path
