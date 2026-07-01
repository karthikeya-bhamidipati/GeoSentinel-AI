"""
===============================================================================
GeoSentinel AI

Module:
    sentinelhub.py

Description:
    Sentinel Hub provider stub.

    This provider is reserved for future integration with the
    Sentinel Hub commercial API. The primary provider for this
    project is CDSE (see stac.py).

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.eo.providers.base import BaseProvider
from src.eo.exceptions import UnsupportedProviderError


class SentinelHubProvider(BaseProvider):
    """
    Sentinel Hub commercial API provider stub.

    Not implemented in the current version.
    Use CDSEProvider for all data access.
    """

    def __init__(self) -> None:

        super().__init__("sentinelhub")

    def connect(self) -> None:

        raise UnsupportedProviderError(
            "SentinelHub provider is not implemented. "
            "Use CDSEProvider instead."
        )

    def search(self, **kwargs: Any) -> list[dict]:

        raise UnsupportedProviderError(
            "SentinelHub provider is not implemented."
        )

    def load(self, source: str | Path) -> Any:

        raise UnsupportedProviderError(
            "SentinelHub provider is not implemented."
        )

    def metadata(self, source: str | Path) -> dict:

        raise UnsupportedProviderError(
            "SentinelHub provider is not implemented."
        )

    def available_bands(self, source: str | Path) -> list[str]:

        raise UnsupportedProviderError(
            "SentinelHub provider is not implemented."
        )

    def load_band(
        self,
        source: str | Path,
        band_name: str,
    ) -> Any:

        raise UnsupportedProviderError(
            "SentinelHub provider is not implemented."
        )

    def close(self) -> None:

        pass
