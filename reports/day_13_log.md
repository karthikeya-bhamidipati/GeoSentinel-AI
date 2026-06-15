# Day 13 Project Log

Date: June 13, 2026

Status: Completed

---

# Objectives

- Learn RasterDataset
- Learn GeoDataset
- Understand Bounding Boxes
- Understand CRS
- Explore Sentinel2 Dataset Class
- Understand TorchGeo Architecture

---

# Completed Tasks

## RasterDataset Exploration

Studied TorchGeo RasterDataset and its role in geospatial machine learning.

---

## GeoDataset Exploration

Studied GeoDataset as the parent class for geospatial datasets.

---

## Bounding Box Exploration

Created and inspected sample bounding boxes.

Learned how TorchGeo uses spatial queries.

---

## CRS Understanding

Reviewed coordinate reference systems and their role in geospatial analysis.

---

## Sentinel2 Dataset Investigation

Explored Sentinel2 class hierarchy and metadata.

---

## Architecture Study

Mapped the relationship between:

GeoDataset
↓
RasterDataset
↓
Sentinel2

---

# Challenges Faced

No major technical issues encountered.

Main challenge was understanding the conceptual shift from index-based datasets to spatially queried datasets.

---

# Resolution

Used examples and class inspection to understand the TorchGeo architecture.

---

# Learnings

- TorchGeo datasets are location-aware.
- Bounding boxes are the primary access mechanism.
- RasterDataset abstracts raster management.
- GeoDataset provides geospatial capabilities.
- CRS enables Earth-referenced data access.

---

# Decisions Made

Future GeoSentinel development will use TorchGeo abstractions rather than manual Rasterio-only workflows.

---

# Project Impact

Day 13 establishes the dataset foundation required for:

- Patch generation
- Sampling
- DataLoaders
- Deep learning training

This is a critical prerequisite for future model development.

---

# Next Steps

Day 14:

- GeoSamplers
- RandomGeoSampler
- GridGeoSampler
- Patch extraction
- Training sample generation

---

# Completion Status

Day 13 Completed Successfully

Progress:

13 / 60 Days Completed

Project Status:

On Track
