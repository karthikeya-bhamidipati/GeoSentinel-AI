# Day 10 – TorchGeo Datasets Deep Dive

Date: June 10, 2026

## Objective

Understand TorchGeo dataset architecture and Sentinel-2 data handling.

## Topics Covered

* GeoDataset
* RasterDataset
* Dataset metadata
* CRS
* Bounding Boxes
* Spatial indexing
* Patch extraction
* Sentinel-2 structure

## GeoDataset

Base class for all TorchGeo datasets.

Responsibilities:

* Geographic metadata
* CRS management
* Spatial querying

## RasterDataset

Used for raster imagery.

Examples:

* Sentinel-2
* Landsat
* DEM

Benefits:

* Efficient patch loading
* Spatial indexing
* Geospatial metadata handling

## Sentinel-2 Bands

B2 → Blue

B3 → Green

B4 → Red

B8 → NIR

B11 → SWIR

B12 → SWIR

## CRS

Coordinate Reference System.

Example:

EPSG:4326

Defines geographic location.

## Bounding Box

Defines spatial region.

Contains:

* minx
* maxx
* miny
* maxy

## Spatial Indexing

Allows fast lookup of image patches.

## Patch-Based Learning

Instead of loading:

10980 × 10980

load:

256 × 256

Benefits:

* Faster training
* Lower memory usage
* Better scalability

## GeoSentinel AI Application

Sentinel-2 Imagery

↓

RasterDataset

↓

Patch Extraction

↓

Urban Expansion Detection

↓

Vegetation Loss Detection

## Key Learnings

1. GeoDataset is the base class.
2. RasterDataset handles satellite imagery.
3. CRS defines location.
4. Bounding boxes define regions.
5. Patch extraction is essential for deep learning.

## Outcome

Successfully understood TorchGeo dataset architecture and Sentinel-2 data organization.
