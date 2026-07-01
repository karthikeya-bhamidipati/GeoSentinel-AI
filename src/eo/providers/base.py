"""
===============================================================================
GeoSentinel AI

Module:
    base.py

Description:
    Abstract base class for all data providers.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseProvider(ABC):
    """
    Abstract base class for all Earth Observation data providers.

    Every provider (Local SAFE, Sentinel Hub, STAC, etc.) must inherit
    from this class and implement the required methods.
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    def connect(self) -> None:
        """
        Initialize the provider.

        Examples
        --------
        - Validate local SAFE directory
        - Authenticate Sentinel Hub
        - Connect to STAC catalog
        """
        raise NotImplementedError

    @abstractmethod
    def search(self, **kwargs) -> list[dict]:
        """
        Search for available scenes.

        Returns
        -------
        list[dict]
            List of matching scenes.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, source: str | Path) -> Any:
        """
        Load a dataset from the provider.

        Parameters
        ----------
        source : str | Path

        Returns
        -------
        Any
            Provider-specific scene object.
        """
        raise NotImplementedError

    @abstractmethod
    def metadata(self, source: str | Path) -> dict:
        """
        Extract metadata.

        Parameters
        ----------
        source : str | Path

        Returns
        -------
        dict
        """
        raise NotImplementedError

    @abstractmethod
    def available_bands(self, source: str | Path) -> list[str]:
        """
        Return available spectral bands.

        Parameters
        ----------
        source : str | Path

        Returns
        -------
        list[str]
        """
        raise NotImplementedError

    @abstractmethod
    def load_band(
        self,
        source: str | Path,
        band_name: str,
    ):
        """
        Load a specific spectral band.

        Parameters
        ----------
        source : str | Path

        band_name : str

        Returns
        -------
        Any
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """
        Release any resources used by the provider.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider='{self.provider_name}')"