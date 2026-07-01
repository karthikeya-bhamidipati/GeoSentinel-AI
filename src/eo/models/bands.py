"""
===============================================================================
GeoSentinel AI

Module:
    bands.py

Description:
    Sentinel-2 Spectral Band Definitions.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from enum import Enum


class Band(Enum):
    """
    Sentinel-2 Spectral Bands.

    Value = Official Sentinel-2 Band Name
    """

    COASTAL = "B01"

    BLUE = "B02"

    GREEN = "B03"

    RED = "B04"

    RED_EDGE_1 = "B05"

    RED_EDGE_2 = "B06"

    RED_EDGE_3 = "B07"

    NIR = "B08"

    NARROW_NIR = "B8A"

    WATER_VAPOR = "B09"

    CIRRUS = "B10"

    SWIR_1 = "B11"

    SWIR_2 = "B12"

    AOT = "AOT"

    WVP = "WVP"

    SCL = "SCL"

    TCI = "TCI"

    @property
    def code(self) -> str:
        """
        Returns the Sentinel-2 band code.
        """

        return self.value

    def __str__(self) -> str:
        return self.value


# --------------------------------------------------------------------------
# Frequently Used Band Groups
# --------------------------------------------------------------------------

RGB_BANDS = (
    Band.RED,
    Band.GREEN,
    Band.BLUE,
)

FALSE_COLOR_BANDS = (
    Band.NIR,
    Band.RED,
    Band.GREEN,
)

AI_BANDS = (
    Band.BLUE,
    Band.GREEN,
    Band.RED,
    Band.NIR,
    Band.SWIR_1,
)

ALL_BANDS = tuple(Band)