"""
===============================================================================
GeoSentinel AI

Module:
    tiling.py

Description:
    Sliding window tile extraction for large raster inference.

    Sentinel-2 scenes can be large (e.g., 10,000 x 10,000 pixels).
    Neural networks process fixed-size patches (256x256).
    This module extracts overlapping tiles for inference and
    records their positions for reconstruction.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Tile:
    """
    A single tile extracted from a raster array.

    Attributes
    ----------
    array : np.ndarray
        Shape (channels, height, width).
    row : int
        Top-left row position in the source array.
    col : int
        Top-left column position in the source array.
    height : int
        Tile height.
    width : int
        Tile width.
    """

    array: np.ndarray
    row: int
    col: int
    height: int
    width: int


class TileExtractor:
    """
    Extracts overlapping tiles from a multi-band raster array.

    Uses a sliding window approach with configurable tile size and stride.
    Smaller stride → more overlap → smoother blended predictions.
    Larger stride → fewer tiles → faster inference.

    Parameters
    ----------
    tile_size : int
        Tile size in pixels (default: 256).
    stride : int
        Step size between tiles (default: 192, ~75% overlap).
    """

    def __init__(
        self,
        tile_size: int = 256,
        stride: int = 192,
    ) -> None:

        self.tile_size = tile_size
        self.stride = stride

    # ------------------------------------------------------------------

    def extract(
        self,
        array: np.ndarray,
        pad_if_needed: bool = True,
    ) -> tuple[list[Tile], tuple[int, int, int]]:
        """
        Extract tiles from a (channels, height, width) array.

        Parameters
        ----------
        array : np.ndarray
            Shape (C, H, W).
        pad_if_needed : bool
            If True, pads the array so it is at least tile_size.

        Returns
        -------
        tuple[list[Tile], tuple[int, int, int]]
            (tiles, original_shape) where original_shape = (C, H, W).
        """

        original_shape = array.shape
        C, H, W = array.shape

        if pad_if_needed:
            array, (pad_h, pad_w) = self._pad(array)
            C, H, W = array.shape
        else:
            pad_h, pad_w = 0, 0

        tiles = []
        
        row_starts = list(range(0, H - self.tile_size + 1, self.stride))
        if H > self.tile_size and (H - self.tile_size) % self.stride != 0:
            row_starts.append(H - self.tile_size)
        if not row_starts:
            row_starts = [0]
            
        col_starts = list(range(0, W - self.tile_size + 1, self.stride))
        if W > self.tile_size and (W - self.tile_size) % self.stride != 0:
            col_starts.append(W - self.tile_size)
        if not col_starts:
            col_starts = [0]

        for row in row_starts:
            for col in col_starts:

                tile_array = array[
                    :,
                    row:row + self.tile_size,
                    col:col + self.tile_size,
                ]

                tiles.append(Tile(
                    array=tile_array,
                    row=row,
                    col=col,
                    height=self.tile_size,
                    width=self.tile_size,
                ))

        return tiles, original_shape

    # ------------------------------------------------------------------

    def _pad(
        self,
        array: np.ndarray,
    ) -> tuple[np.ndarray, tuple[int, int]]:
        """
        Pad an array to ensure it is at least tile_size.
        """

        C, H, W = array.shape
        ts = self.tile_size

        pad_h = max(0, ts - H)
        pad_w = max(0, ts - W)

        if pad_h > 0 or pad_w > 0:
            array = np.pad(
                array,
                ((0, 0), (0, pad_h), (0, pad_w)),
                mode="reflect",
            )

        return array, (pad_h, pad_w)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"TileExtractor("
            f"tile_size={self.tile_size}, "
            f"stride={self.stride})"
        )
