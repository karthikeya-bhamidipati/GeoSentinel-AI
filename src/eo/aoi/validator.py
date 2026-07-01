"""
===============================================================================
GeoSentinel AI

Module:
    validator.py

Description:
    AOI Validator

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from shapely.validation import explain_validity

from src.eo.aoi.boundary import boundary
from src.eo.aoi.geometry import AOI
from src.eo.exceptions import (
    AOIOutsideBoundaryError,
    AOITooLargeError,
    InvalidGeometryError,
)


class AOIValidator:
    """
    Validates an AOI before it is processed by the platform.

    Validation includes:

    - Geometry validity
    - Empty geometry
    - Study area boundary
    - Maximum area
    """

    DEFAULT_MAX_AREA = 2500.0  # km²

    def __init__(
        self,
        max_area_sqkm: float = DEFAULT_MAX_AREA,
    ):

        self.max_area_sqkm = max_area_sqkm

    # ------------------------------------------------------------------

    def validate_geometry(
        self,
        aoi: AOI,
    ) -> None:
        """
        Validate polygon geometry.
        """

        if aoi.geometry.is_empty:

            raise InvalidGeometryError(
                "AOI geometry is empty."
            )

        if not aoi.geometry.is_valid:

            raise InvalidGeometryError(
                explain_validity(aoi.geometry)
            )

    # ------------------------------------------------------------------

    def validate_boundary(
        self,
        aoi: AOI,
    ) -> None:
        """
        Ensure AOI lies completely inside HMR.
        """

        if not boundary.contains(aoi.geometry):

            raise AOIOutsideBoundaryError(
                "AOI lies outside the supported study area."
            )

    # ------------------------------------------------------------------

    def validate_area(
        self,
        aoi: AOI,
    ) -> None:
        """
        Validate AOI size.
        """

        if aoi.area_sqkm > self.max_area_sqkm:

            raise AOITooLargeError(

                f"AOI area ({aoi.area_sqkm:.2f} km²) "

                f"exceeds maximum allowed "

                f"({self.max_area_sqkm:.2f} km²)."

            )

    # ------------------------------------------------------------------

    def validate(
        self,
        aoi: AOI,
    ) -> bool:
        """
        Perform all validations.
        """

        self.validate_geometry(aoi)

        self.validate_boundary(aoi)

        self.validate_area(aoi)

        return True

    # ------------------------------------------------------------------

    def __call__(
        self,
        aoi: AOI,
    ) -> bool:

        return self.validate(aoi)

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"AOIValidator("

            f"max_area={self.max_area_sqkm} km²)"

        )