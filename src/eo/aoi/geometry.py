"""
===============================================================================
GeoSentinel AI

Module:
    geometry.py

Description:
    Area of Interest (AOI) Domain Model

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

import geopandas as gpd
from shapely.geometry import Polygon, mapping
from shapely.ops import transform
from pyproj import CRS, Transformer


@dataclass(slots=True)
class AOI:
    """
    Area Of Interest (AOI).

    This is the central spatial object used throughout the
    GeoSentinel AI platform.

    It stores the user-selected polygon and exposes common
    geometric properties.
    """

    geometry: Polygon

    crs: CRS = field(
        default_factory=lambda: CRS.from_epsg(4326)
    )

    # ------------------------------------------------------------------
    # Basic Properties
    # ------------------------------------------------------------------

    @property
    def bounds(self):
        """
        Bounding box.
        """

        return self.geometry.bounds

    # ------------------------------------------------------------------

    @property
    def centroid(self):

        return self.geometry.centroid

    # ------------------------------------------------------------------

    @property
    def area_sqkm(self) -> float:
        """
        Polygon area in square kilometres.
        """

        projected = self.to_crs(3857)

        return projected.geometry.area / 1_000_000

    # ------------------------------------------------------------------

    @property
    def perimeter_km(self) -> float:
        """
        Polygon perimeter in kilometres.
        """

        projected = self.to_crs(3857)

        return projected.geometry.length / 1000

    # ------------------------------------------------------------------

    @property
    def bbox_polygon(self):

        minx, miny, maxx, maxy = self.bounds

        return Polygon(
            [
                (minx, miny),
                (maxx, miny),
                (maxx, maxy),
                (minx, maxy),
            ]
        )

    # ------------------------------------------------------------------
    # CRS
    # ------------------------------------------------------------------

    def to_crs(
        self,
        epsg: int,
    ) -> "AOI":
        """
        Reproject AOI.
        """

        destination = CRS.from_epsg(epsg)

        transformer = Transformer.from_crs(
            self.crs,
            destination,
            always_xy=True,
        )

        new_geometry = transform(
            transformer.transform,
            self.geometry,
        )

        return AOI(
            geometry=new_geometry,
            crs=destination,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @property
    def geojson(self) -> dict[str, Any]:

        return mapping(
            self.geometry
        )

    # ------------------------------------------------------------------

    @property
    def wkt(self) -> str:

        return self.geometry.wkt

    # ------------------------------------------------------------------

    @property
    def geodataframe(self):

        return gpd.GeoDataFrame(

            geometry=[self.geometry],

            crs=self.crs,

        )

    # ------------------------------------------------------------------
    # Cache Hash
    # ------------------------------------------------------------------

    @property
    def hash(self) -> str:
        """
        Stable AOI hash.
        """

        geojson = json.dumps(

            self.geojson,

            sort_keys=True,

        )

        return hashlib.sha256(

            geojson.encode("utf-8")

        ).hexdigest()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> dict:

        return {

            "crs": self.crs.to_epsg(),

            "area_sqkm": round(
                self.area_sqkm,
                3,
            ),

            "perimeter_km": round(
                self.perimeter_km,
                3,
            ),

            "bounds": self.bounds,

            "centroid": (
                self.centroid.x,
                self.centroid.y,
            ),

            "hash": self.hash,

        }

    # ------------------------------------------------------------------

    def __repr__(self):

        return (

            f"AOI("
            f"{self.area_sqkm:.2f} km²)"

        )