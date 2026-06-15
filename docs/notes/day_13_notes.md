# Day 13 Notes

## Date

June 13, 2026

---

# TorchGeo RasterDataset and GeoDataset

Today focused on understanding the core dataset architecture used by TorchGeo.

Rather than manually loading raster files using Rasterio, TorchGeo provides geospatially-aware dataset abstractions that support machine learning workflows.

---

# 1. Why TorchGeo Exists

Traditional remote sensing workflows use:

- Rasterio
- GDAL
- NumPy

These approaches require manual handling of:

- Raster indexing
- Spatial queries
- CRS management
- Patch extraction

TorchGeo automates these tasks.

---

# 2. RasterDataset

## Definition

RasterDataset is TorchGeo's base class for raster imagery.

Examples:

- Sentinel-2
- Landsat
- NAIP

---

## Responsibilities

- Raster indexing
- Spatial queries
- CRS handling
- Bounding box extraction
- Metadata management

---

## Benefits

Instead of manually reading raster files, the dataset becomes spatially queryable.

---

# 3. GeoDataset

## Definition

GeoDataset is the parent class for all geospatial datasets in TorchGeo.

---

## Purpose

Provides:

- CRS support
- Spatial indexing
- Geospatial querying

---

## Dataset Hierarchy

GeoDataset
↓
RasterDataset
↓
Sentinel2

---

# 4. Bounding Boxes

## Definition

A bounding box defines a geographic region.

Structure:

xmin
ymin
xmax
ymax

---

## Why Important

TorchGeo retrieves data using geographic locations instead of numerical indices.

Traditional Dataset:

dataset[5]

TorchGeo:

dataset[bbox]

---

# 5. Coordinate Reference Systems (CRS)

## Definition

A CRS defines how coordinates relate to locations on Earth.

---

## Examples

EPSG:4326

Latitude / Longitude

---

EPSG:32643

UTM Zone 43N

---

## Importance

Allows geospatial data to be accurately aligned.

---

# 6. Rasterio vs RasterDataset

## Rasterio

- Manual loading
- Manual cropping
- Manual indexing

---

## RasterDataset

- Automatic indexing
- Spatial querying
- Deep learning integration

---

# 7. Sentinel2 Dataset Class

TorchGeo already includes a Sentinel2 dataset implementation.

The Sentinel2 class inherits from:

Sentinel2
↓
RasterDataset
↓
GeoDataset

---

# 8. GeoSentinel Connection

Current Workflow

SAFE Product
↓
RasterDataset
↓
Bounding Boxes
↓
Samplers
↓
Training Patches
↓
Deep Learning Models

---

# Key Learnings

- TorchGeo is built around spatial data access.
- Bounding boxes replace numerical indexing.
- RasterDataset manages geospatial rasters.
- GeoDataset is the foundation of TorchGeo.
- CRS is essential for geospatial consistency.
- TorchGeo simplifies preparation of satellite imagery for machine learning.

---

# Questions For Future Exploration

- How are patches sampled?
- What is a GeoSampler?
- How are labels associated with imagery?
- How does TorchGeo create DataLoaders?
- How will GeoSentinel use TorchGeo datasets?
