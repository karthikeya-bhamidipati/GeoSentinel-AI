"""
===============================================================================
GeoSentinel AI

Module:
    stack.py

Description:
    Feature stack builder — combines spectral bands and indices into a
    unified multi-channel array for AI model input.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import zoom


@dataclass
class FeatureStack:
    """
    Multi-channel feature array ready for AI model input.

    Attributes
    ----------
    array : np.ndarray
        Shape (channels, height, width), dtype float32.
    channel_names : list[str]
        Name of each channel in order.
    height : int
    width : int
    n_channels : int
    """

    array: np.ndarray
    channel_names: list[str] = field(default_factory=list)
    nan_mask: np.ndarray = field(default_factory=lambda: np.zeros((1, 1), dtype=bool))

    @property
    def height(self) -> int:
        return self.array.shape[1]

    @property
    def width(self) -> int:
        return self.array.shape[2]

    @property
    def n_channels(self) -> int:
        return self.array.shape[0]

    def channel(self, name: str) -> np.ndarray:
        """
        Return a single channel by name.

        Parameters
        ----------
        name : str

        Returns
        -------
        np.ndarray
            2D array (height, width).
        """

        idx = self.channel_names.index(name)
        return self.array[idx]

    def summary(self) -> dict:

        return {
            "channels": self.n_channels,
            "height": self.height,
            "width": self.width,
            "channel_names": self.channel_names,
            "dtype": str(self.array.dtype),
            "min": float(np.nanmin(self.array)),
            "max": float(np.nanmax(self.array)),
            "has_nan": bool(np.isnan(self.array).any()),
        }

    def __repr__(self) -> str:
        return (
            f"FeatureStack("
            f"{self.n_channels}ch, "
            f"{self.height}x{self.width})"
        )


class FeatureStackBuilder:
    """
    Assembles spectral bands and computed indices into a FeatureStack.

    The stack is built by concatenating arrays along the channel axis.
    NaN values (from cloud masking) are filled with zero before
    model input, with a NaN-aware approach.
    """

    def build(
        self,
        bands: dict[str, np.ndarray],
        indices: dict[str, np.ndarray],
    ) -> FeatureStack:
        """
        Build a FeatureStack from band and index arrays.

        Parameters
        ----------
        bands : dict[str, np.ndarray]
            Spectral band arrays keyed by band name (e.g. "B02").
        indices : dict[str, np.ndarray]
            Index arrays keyed by index name (e.g. "NDVI").

        Returns
        -------
        FeatureStack
        """

        EXPECTED_CHANNELS = ["B02", "B03", "B04", "B08", "B11", "NDVI", "NDBI", "NDWI", "SAVI", "EVI", "MNDWI", "BSI"]
        channel_names = []
        arrays = []
        
        all_features = {**bands, **indices}
        for name in EXPECTED_CHANNELS:
            if name in all_features:
                channel_names.append(name)
                arr_2d = all_features[name].squeeze()
                arrays.append(arr_2d.astype("float32"))
            else:
                raise ValueError(f"Missing required channel for inference: {name}")

        # Find the maximum shape (target 10m resolution)
        max_h = max(a.shape[0] for a in arrays)
        max_w = max(a.shape[1] for a in arrays)

        # Resize all arrays to max shape
        resized_arrays = []
        for arr in arrays:
            if arr.shape[0] != max_h or arr.shape[1] != max_w:
                zoom_y = max_h / arr.shape[0]
                zoom_x = max_w / arr.shape[1]
                arr = zoom(arr, (zoom_y, zoom_x), order=0)  # order=0 = nearest-neighbor
                # Safety crop in case of floating-point rounding
                arr = arr[:max_h, :max_w]
            resized_arrays.append(arr)

        stacked = np.stack(resized_arrays, axis=0)

        # Build validity mask BEFORE replacing NaN — a pixel is invalid
        # if ANY channel is NaN (cloud-masked, alignment border, nodata)
        nan_mask = np.isnan(stacked).any(axis=0)  # (H, W) bool

        # Replace NaN with 0 for model input
        stacked = np.nan_to_num(stacked, nan=0.0)

        return FeatureStack(
            array=stacked,
            channel_names=channel_names,
            nan_mask=nan_mask,
        )

    def __repr__(self) -> str:
        return "FeatureStackBuilder()"
