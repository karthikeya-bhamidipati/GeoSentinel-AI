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

        channel_names = []
        arrays = []

        for name, arr in {**bands, **indices}.items():
            channel_names.append(name)
            arr_2d = arr.squeeze()
            arrays.append(arr_2d.astype("float32"))

        # Verify all arrays are the same shape
        shapes = [a.shape for a in arrays]
        if len(set(shapes)) > 1:
            raise ValueError(
                f"All channels must have the same spatial shape. "
                f"Got: {dict(zip(channel_names, shapes))}"
            )

        stacked = np.stack(arrays, axis=0)

        # Replace NaN with 0 for model input
        stacked = np.nan_to_num(stacked, nan=0.0)

        return FeatureStack(
            array=stacked,
            channel_names=channel_names,
        )

    def __repr__(self) -> str:
        return "FeatureStackBuilder()"
