# Day 04 Notes

## Date

June 4, 2026

---

# First Interaction with Real Satellite Data

Today focused on understanding how satellite imagery is discovered, evaluated, downloaded, and prepared for future processing within GeoSentinel AI.

---

# 1. Copernicus Browser

## Overview

Copernicus Browser is a web platform that provides access to Sentinel satellite imagery and Earth observation datasets.

It enables:

* Satellite imagery exploration
* Time-series visualization
* Metadata inspection
* Scene selection
* Data download

---

## Activities Completed

* Navigated to Hyderabad
* Explored timeline functionality
* Explored layer selection
* Explored metadata panels
* Examined available Sentinel-2 imagery

---

## Key Learning

Copernicus Browser is useful for discovering and inspecting imagery before downloading datasets.

---

# 2. Sentinel Hub

## Overview

Sentinel Hub is a cloud-based platform for accessing and processing satellite imagery.

Unlike Copernicus Browser, Sentinel Hub is designed for developers and large-scale applications.

---

## Key Capabilities

* API-based imagery access
* On-demand processing
* Cloud infrastructure
* Large-scale geospatial workflows

---

## Potential Role in GeoSentinel

* Automated imagery retrieval
* Future data pipelines
* Scalable processing workflows

---

# 3. Copernicus Browser vs Sentinel Hub

| Feature          | Copernicus Browser       | Sentinel Hub      |
| ---------------- | ------------------------ | ----------------- |
| Primary Purpose  | Visualization & Download | Processing & APIs |
| User Type        | Researchers & Analysts   | Developers        |
| Interface        | Web GUI                  | APIs & Services   |
| Download Support | Yes                      | Yes               |
| Automation       | Limited                  | Extensive         |

---

# 4. Sentinel-2 Scene Exploration

## Study Region

Hyderabad, Telangana, India

---

## Observations

Examined available Sentinel-2 scenes for Hyderabad.

Observed:

* Urban areas
* Vegetation regions
* Water bodies
* Seasonal variation

---

## Importance

Understanding scene selection is critical before preprocessing and analysis.

---

# 5. Level-1C vs Level-2A

## Level-1C

Top Of Atmosphere Reflectance

Characteristics:

* Atmospheric effects present
* Rawer form of imagery

---

## Level-2A

Bottom Of Atmosphere Reflectance

Characteristics:

* Atmospherically corrected
* Better for vegetation analysis
* Better for NDVI

---

## GeoSentinel Decision

Preferred Product:

Level-2A

Reason:

Provides cleaner surface reflectance values for environmental analysis.

---

# 6. Satellite Metadata

## Important Metadata Fields

### Acquisition Date

Date imagery was captured.

---

### Cloud Cover

Percentage of cloud contamination.

---

### CRS

Coordinate Reference System.

---

### Spatial Resolution

Ground area represented by a pixel.

---

### Product ID

Unique dataset identifier.

---

### Tile ID

Spatial tile identifier.

---

## Why Metadata Matters

Metadata enables:

* Dataset filtering
* Quality assessment
* Temporal analysis
* Spatial consistency

---

# 7. Cloud Cover

## Importance

Clouds can hide important surface information.

High cloud cover can:

* Reduce image quality
* Create false detections
* Affect NDVI calculations

---

## GeoSentinel Strategy

Prefer imagery with:

Cloud Cover < 10%

when possible.

---

# 8. Downloaded Dataset

## Status

Successfully downloaded first Sentinel-2 imagery.

---

## Storage Location

data/raw/day04/

---

## Purpose

Used for:

* GeoTIFF exploration
* Metadata inspection
* Future preprocessing exercises

---

# 9. GeoTIFF Inspection

Explored imagery using QGIS.

Observed:

* Spatial referencing
* Layer properties
* Metadata structure
* Geospatial alignment

---

## Key Learning

A GeoTIFF is much more than an image.

It contains:

* Pixel values
* Coordinates
* CRS
* Resolution
* Geographic metadata

---

# 10. GeoSentinel Data Workflow

Planned workflow:

Sentinel-2 Imagery
↓
Metadata Validation
↓
Cloud Filtering
↓
Download
↓
Preprocessing
↓
NDVI Generation
↓
Change Detection
↓
Urban Expansion Analysis
↓
Vegetation Loss Analysis
↓
Risk Detection
↓
Report Generation
↓
RAG Query System
↓
Dashboard

---

# Dataset Inventory

| Dataset    | Status    |
| ---------- | --------- |
| Sentinel-2 | Selected  |
| Landsat    | Backup    |
| OSCD       | Candidate |
| S2Looking  | Candidate |

---

# Key Learnings

* Copernicus Browser is useful for imagery exploration.
* Sentinel Hub is designed for scalable geospatial workflows.
* Level-2A imagery is preferred for GeoSentinel.
* Metadata plays a critical role in dataset quality.
* Cloud filtering is essential before analysis.
* Real satellite imagery contains far more information than standard images.
* GeoTIFF is the primary format used in remote sensing workflows.

---

# Questions For Future Exploration

* How is cloud masking implemented?
* How are Sentinel-2 tiles organized?
* How will TorchGeo load downloaded imagery?
* How should imagery be prepared for model training?
