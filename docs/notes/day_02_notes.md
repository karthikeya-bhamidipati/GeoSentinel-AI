# Day 02 Notes

## Date

June 2, 2026

---

# Geospatial Foundations

Today focused on understanding the fundamental concepts behind remote sensing and geospatial data before working with satellite imagery.

---

# 1. Raster Data

## Definition

Raster data is a grid-based representation of information where each cell (pixel) contains a value.

Examples:

* Satellite imagery
* Elevation maps
* NDVI maps
* Temperature maps

## Advantages

* Excellent for imagery
* Suitable for computer vision
* Works naturally with deep learning models

## Disadvantages

* Large storage requirements
* Resolution dependent

## GeoSentinel Usage

Raster data will be used for:

* Sentinel-2 imagery
* NDVI generation
* Change detection
* Vegetation analysis
* Urban expansion analysis

---

# 2. Vector Data

## Definition

Vector data represents geographic features using geometric shapes.

Types:

### Point

Represents a single location.

Examples:

* City location
* Sensor location

### Line

Represents a path.

Examples:

* Roads
* Rivers

### Polygon

Represents an area.

Examples:

* District boundaries
* Administrative regions

## Advantages

* Compact storage
* High precision
* Easy spatial querying

## Disadvantages

* Not suitable for image processing

## GeoSentinel Usage

Vector data will be used for:

* Hyderabad boundary
* Area selection
* Region filtering
* Spatial analysis

---

# 3. Coordinate Reference Systems (CRS)

## Definition

A Coordinate Reference System defines how geographic locations are represented mathematically.

Since the Earth is spherical and computer screens are flat, projections are required.

## Common CRS

### EPSG:4326

Also known as:

WGS84

Used by:

* GPS
* Google Maps
* Most mapping systems

## Why CRS Matters

Different datasets may use different coordinate systems.

If two datasets use different CRS values:

* Layers may not align correctly
* Analysis may become inaccurate

## GeoSentinel Usage

All satellite imagery and vector boundaries must use compatible CRS values before analysis.

---

# 4. GeoTIFF

## Definition

GeoTIFF is a TIFF image containing geographic metadata.

It stores:

* Pixel values
* Geographic coordinates
* CRS information
* Resolution information

## Difference Between JPG and GeoTIFF

JPG:

* Only image information

GeoTIFF:

* Image information
* Geographic information

## GeoSentinel Usage

GeoTIFF will be the primary format used for:

* Satellite imagery
* NDVI outputs
* Change maps

---

# 5. Sentinel-2 Bands

Sentinel-2 contains 13 spectral bands.

For GeoSentinel, the most important bands initially are:

| Band | Description         |
| ---- | ------------------- |
| B2   | Blue                |
| B3   | Green               |
| B4   | Red                 |
| B8   | Near Infrared (NIR) |

## B2 - Blue

Useful for:

* Water observation
* Coastal monitoring

## B3 - Green

Useful for:

* Vegetation appearance
* Natural color images

## B4 - Red

Useful for:

* Vegetation analysis
* NDVI calculation

## B8 - Near Infrared

Useful for:

* Vegetation monitoring
* NDVI calculation

Plants strongly reflect NIR energy.

---

# 6. NDVI

## Definition

NDVI stands for:

Normalized Difference Vegetation Index

It is one of the most widely used vegetation indicators in remote sensing.

Formula:

NDVI = (B8 - B4) / (B8 + B4)

Where:

* B8 = Near Infrared
* B4 = Red

## Why NDVI Works

Healthy vegetation:

* Reflects Near Infrared strongly
* Absorbs Red light

This creates high NDVI values.

## Interpretation

| NDVI Range | Meaning           |
| ---------- | ----------------- |
| > 0.6      | Dense Vegetation  |
| 0.2 – 0.5  | Sparse Vegetation |
| < 0.1      | Urban/Barren Land |

## GeoSentinel Usage

NDVI will help:

* Detect vegetation loss
* Monitor environmental changes
* Support change detection models
* Generate risk indicators

---

# 7. QGIS Exploration

## Activities Completed

* Installed QGIS
* Explored interface
* Explored Layers Panel
* Explored Browser Panel
* Explored Map Canvas

## Learning

QGIS acts as a GIS visualization and analysis tool similar to how Photoshop works for images.

---

# 8. Connection To GeoSentinel

Raster Data:
Satellite imagery

Vector Data:
Administrative boundaries

CRS:
Spatial alignment

GeoTIFF:
Primary storage format

Bands:
Input features

NDVI:
Vegetation intelligence

Change Detection:
Temporal comparison of imagery and vegetation indicators

---

# Key Learnings

* Satellite imagery is geospatial raster data.
* Every pixel corresponds to a real-world location.
* CRS is critical for accurate spatial analysis.
* GeoTIFF stores both imagery and geographic information.
* Sentinel-2 provides multiple spectral bands.
* NDVI is a powerful vegetation indicator.
* These concepts form the foundation of GeoSentinel AI.

---

# Questions For Further Exploration

* How are Sentinel-2 images downloaded?
* How are NDVI maps generated programmatically?
* How will change detection models use multi-temporal imagery?
* How can NDVI and deep learning outputs be combined?
