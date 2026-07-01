"""
===============================================================================
GeoSentinel AI

Module:
    exceptions.py

Description:
    Custom exceptions for the GeoSentinel AI Earth Observation Engine.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations


class GeoSentinelError(Exception):
    """
    Base exception for the GeoSentinel AI platform.
    """

    pass


# =============================================================================
# AOI Exceptions
# =============================================================================

class AOIError(GeoSentinelError):
    """
    Base AOI exception.
    """

    pass


class AOIValidationError(AOIError):
    """
    Raised when an AOI is invalid.
    """

    pass


class AOIOutsideBoundaryError(AOIValidationError):
    """
    Raised when AOI lies outside the supported study region.
    """

    pass


class InvalidGeometryError(AOIValidationError):
    """
    Raised when AOI geometry is invalid.
    """

    pass


class AOITooLargeError(AOIValidationError):
    """
    Raised when AOI exceeds the maximum allowed area.
    """

    pass


# =============================================================================
# CDSE Exceptions
# =============================================================================

class CDSEError(GeoSentinelError):
    """
    Base CDSE exception.
    """

    pass


class AuthenticationError(CDSEError):
    """
    Authentication failed.
    """

    pass


class AuthorizationError(CDSEError):
    """
    Authorization failed.
    """

    pass


class TokenExpiredError(AuthenticationError):
    """
    Access token expired.
    """

    pass


class SearchError(CDSEError):
    """
    Scene search failed.
    """

    pass


class DownloadError(CDSEError):
    """
    Scene download failed.
    """

    pass


class SceneNotFoundError(SearchError):
    """
    No Sentinel scene found.
    """

    pass


# =============================================================================
# Raster Exceptions
# =============================================================================

class RasterError(GeoSentinelError):
    """
    Base raster exception.
    """

    pass


class RasterReadError(RasterError):
    """
    Unable to read raster.
    """

    pass


class RasterWriteError(RasterError):
    """
    Unable to write raster.
    """

    pass


class BandNotFoundError(RasterError):
    """
    Requested band does not exist.
    """

    pass


class InvalidRasterError(RasterError):
    """
    Invalid raster dataset.
    """

    pass


# =============================================================================
# Cache Exceptions
# =============================================================================

class CacheError(GeoSentinelError):
    """
    Base cache exception.
    """

    pass


class CacheMissError(CacheError):
    """
    Requested cache entry does not exist.
    """

    pass


class CacheWriteError(CacheError):
    """
    Unable to write cache.
    """

    pass


class CacheReadError(CacheError):
    """
    Unable to read cache.
    """

    pass


# =============================================================================
# Provider Exceptions
# =============================================================================

class ProviderError(GeoSentinelError):
    """
    Base provider exception.
    """

    pass


class ProviderConnectionError(ProviderError):
    """
    Provider connection failed.
    """

    pass


class UnsupportedProviderError(ProviderError):
    """
    Unsupported EO provider.
    """

    pass


# =============================================================================
# Processing Exceptions
# =============================================================================

class ProcessingError(GeoSentinelError):
    """
    Base processing exception.
    """

    pass


class PreprocessingError(ProcessingError):
    """
    Preprocessing failed.
    """

    pass


class FeatureEngineeringError(ProcessingError):
    """
    Feature generation failed.
    """

    pass


class ModelInferenceError(ProcessingError):
    """
    AI inference failed.
    """

    pass


class TemporalAnalysisError(ProcessingError):
    """
    Temporal analysis failed.
    """

    pass


class AnalyticsError(ProcessingError):
    """
    Spatial analytics failed.
    """

    pass


class ReportGenerationError(ProcessingError):
    """
    Report generation failed.
    """

    pass