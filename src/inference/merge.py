"""
===============================================================================
GeoSentinel AI

Module:
    merge.py

Description:
    Tile merging with overlap averaging (soft blending).

    When tiles overlap, predictions in the overlap region are averaged
    across all contributing tiles. This eliminates edge artifacts
    and produces smooth segmentation maps.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import numpy as np

from src.inference.tiling import Tile


class TileMerger:
    """
    Merges overlapping tile predictions into a full-scene output.

    Uses a weight accumulation approach:
    - Each tile contributes its predicted probabilities to an output canvas.
    - A weight canvas tracks how many tiles covered each pixel.
    - Final prediction = sum of probabilities / weight count.

    Parameters
    ----------
    output_height : int
    output_width : int
    num_classes : int
    """

    def __init__(
        self,
        output_height: int,
        output_width: int,
        num_classes: int,
    ) -> None:

        self.output_height = output_height
        self.output_width = output_width
        self.num_classes = num_classes

        # Accumulated probability scores (float64 for precision)
        self._score_canvas = np.zeros(
            (num_classes, output_height, output_width),
            dtype=np.float32,
        )

        # Weight canvas: count of tiles covering each pixel
        self._weight_canvas = np.zeros(
            (output_height, output_width),
            dtype=np.float32,
        )

    # ------------------------------------------------------------------

    def add_tile(
        self,
        tile: Tile,
        probabilities: np.ndarray,
    ) -> None:
        """
        Add a tile's probability predictions to the canvas.

        Parameters
        ----------
        tile : Tile
            Tile metadata (position and size).
        probabilities : np.ndarray
            Shape (num_classes, tile_h, tile_w), float32.
        """

        r, c = tile.row, tile.col
        h, w = tile.height, tile.width

        # Clip to canvas bounds (handles edge tiles)
        r_end = min(r + h, self.output_height)
        c_end = min(c + w, self.output_width)
        h_crop = r_end - r
        w_crop = c_end - c

        self._score_canvas[
            :,
            r:r_end,
            c:c_end,
        ] += probabilities[:, :h_crop, :w_crop]

        self._weight_canvas[r:r_end, c:c_end] += 1.0

    # ------------------------------------------------------------------

    def get_prediction(self) -> np.ndarray:
        """
        Compute the final segmentation prediction.

        Returns
        -------
        np.ndarray
            Shape (height, width), int32 class indices.
        """

        # Avoid division by zero in uncovered areas
        weight = np.maximum(self._weight_canvas, 1.0)

        averaged = self._score_canvas / weight[np.newaxis, ...]

        return averaged.argmax(axis=0).astype(np.int32)

    # ------------------------------------------------------------------

    def get_probabilities(self) -> np.ndarray:
        """
        Return averaged probability map.

        Returns
        -------
        np.ndarray
            Shape (num_classes, height, width), float32.
        """

        weight = np.maximum(self._weight_canvas, 1.0)

        return (
            self._score_canvas / weight[np.newaxis, ...]
        ).astype(np.float32)

    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear the canvas for reuse."""

        self._score_canvas[:] = 0.0
        self._weight_canvas[:] = 0.0

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"TileMerger("
            f"{self.output_height}x{self.output_width}, "
            f"{self.num_classes} classes)"
        )
