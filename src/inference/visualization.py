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

        fig, ax = plt.subplots(figsize=(10, 8))

        ax.imshow(color_image)
        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.axis("off")

        if show_legend:
            from matplotlib.patches import Patch

            legend_elements = [
                Patch(
                    facecolor=tuple(c / 255 for c in color),
                    edgecolor="white",
                    label=LAND_COVER_NAMES[cls],
                )
                for cls, color in LAND_COVER_COLORS.items()
                if LAND_COVER_NAMES.get(cls)
            ]

            ax.legend(
                handles=legend_elements,
                loc="lower right",
                framealpha=0.9,
                fontsize=9,
                title="Land Cover",
                title_fontsize=10,
            )

        plt.tight_layout()
        fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)

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

        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(
            change_array,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
        )

        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
        ax.axis("off")

        plt.tight_layout()
        fig.savefig(output_path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Change map saved: {output_path.name}")

        return output_path
