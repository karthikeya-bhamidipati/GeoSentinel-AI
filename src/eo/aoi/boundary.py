"""
===============================================================================
GeoSentinel AI

Module:
    boundary.py

Description:
    Hyderabad Metropolitan Region Boundary Manager

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

from src.utils.paths import paths
from src.eo.exceptions import InvalidGeometryError


class BoundaryManager:
    """
    Loads and manages the project study area boundary.

    This class loads the Hyderabad Metropolitan Region (HMR)
    boundary and exposes utility methods required throughout
    the project.

    Singleton class.
    """

    _instance = None

    def __new__(cls):

        if cls._instance is None:

            cls._instance = super().__new__(cls)

            cls._instance._initialize()

        return cls._instance

    # ------------------------------------------------------------------

    def _initialize(self):

        self.boundary_path = paths.HMR_BOUNDARY

        if not self.boundary_path.exists():

            raise FileNotFoundError(

                f"HMR boundary not found:\n{self.boundary_path}"

            )

        self.gdf = gpd.read_file(self.boundary_path)

        if self.gdf.empty:

            raise InvalidGeometryError(

                "Boundary GeoJSON is empty."

            )

        self.gdf = self.gdf.to_crs(epsg=4326)

        self.geometry = unary_union(self.gdf.geometry)

        self.crs = CRS.from_epsg(4326)

    # ------------------------------------------------------------------

    @property
    def polygon(self) -> Polygon | MultiPolygon:

        return self.geometry

    # ------------------------------------------------------------------

    @property
    def bounds(self):

        return self.geometry.bounds

    # ------------------------------------------------------------------

    @property
    def centroid(self):

        return self.geometry.centroid

    # ------------------------------------------------------------------

    @property
    def area_sqkm(self):

        projected = self.gdf.to_crs(epsg=3857)

        return projected.area.sum() / 1_000_000

    # ------------------------------------------------------------------

    @property
    def perimeter_km(self):

        projected = self.gdf.to_crs(epsg=3857)

        return projected.length.sum() / 1000

    # ------------------------------------------------------------------

    def contains(
        self,
        geometry,
    ) -> bool:
        """
        Check whether a geometry lies completely
        inside the study area.
        """

        return self.geometry.contains(geometry)

    # ------------------------------------------------------------------

    def intersects(
        self,
        geometry,
    ) -> bool:
        """
        Check whether a geometry intersects
        the study area.
        """

        return self.geometry.intersects(geometry)

    # ------------------------------------------------------------------

    def distance(
        self,
        geometry,
    ) -> float:
        """
        Distance to boundary (meters).
        """

        boundary = self.gdf.to_crs(3857).geometry.iloc[0]

        geometry = gpd.GeoSeries(

            [geometry],

            crs=4326,

        ).to_crs(3857).iloc[0]

        return boundary.distance(geometry)

    # ------------------------------------------------------------------

    def summary(self):

        return {

            "boundary_file": str(self.boundary_path),

            "crs": self.crs.to_epsg(),

            "area_sqkm": round(

                self.area_sqkm,

                2,

            ),

            "perimeter_km": round(

                self.perimeter_km,

                2,

            ),

            "bounds": self.bounds,

        }

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"BoundaryManager("

            f"{self.area_sqkm:.2f} km²)"

        )


# =============================================================================
# Lazy Singleton Factory
# =============================================================================

_boundary_instance: "BoundaryManager | None" = None


def get_boundary() -> "BoundaryManager":
    """
    Return the module-level BoundaryManager singleton.

    Lazy-initialised on first call so that importing this module does not
    crash when the HMR boundary file is absent (e.g. during unit tests that
    mock the file-system).

    Returns
    -------
    BoundaryManager
    """
    global _boundary_instance

    if _boundary_instance is None:
        _boundary_instance = BoundaryManager()

    return _boundary_instance