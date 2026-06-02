# Day 03 Notes

## Date

June 3, 2026

---

# Satellite Ecosystem Fundamentals

Today focused on understanding the satellite missions, data sources, metadata, and acquisition workflows that will power GeoSentinel AI.

---

# 1. Copernicus Program

## What is Copernicus?

Copernicus is the Earth Observation Programme of the European Union.

It provides free and open access to Earth observation data through the Sentinel satellite missions.

---

## Objectives

* Environmental monitoring
* Land monitoring
* Climate monitoring
* Disaster management
* Security applications

---

## Sentinel Missions

Examples:

* Sentinel-1 (SAR Radar)
* Sentinel-2 (Optical Imagery)
* Sentinel-3 (Ocean & Land Monitoring)
* Sentinel-5P (Atmospheric Monitoring)

---

## Importance for GeoSentinel

GeoSentinel relies on Sentinel-2 imagery provided through the Copernicus Programme.

Benefits:

* Free access
* Global coverage
* Frequent revisits
* High spatial resolution

---

# 2. Sentinel-2 Mission

## Overview

Sentinel-2 is an Earth observation mission designed for land monitoring.

Satellites:

* Sentinel-2A
* Sentinel-2B

Together they provide global coverage.

---

## Key Characteristics

### Spatial Resolution

10m
20m
60m

Meaning:

A 10m resolution pixel represents a 10m × 10m area on the Earth's surface.

---

### Temporal Resolution

5-day revisit cycle

Meaning:

The same location is typically observed every 5 days.

---

### Spectral Resolution

13 spectral bands

Including:

* Blue
* Green
* Red
* Near Infrared
* Short Wave Infrared

---

## Why GeoSentinel Uses Sentinel-2

Advantages:

* Free and open
* High spatial resolution
* Frequent revisit cycle
* Strong vegetation monitoring capabilities
* Excellent support in remote sensing research

---

## Limitations

* Cloud cover
* Optical imagery only
* Weather dependent

---

# 3. Landsat Program

## Overview

Landsat is a long-running Earth observation mission jointly operated by:

* NASA
* USGS

---

## Importance

Provides one of the longest Earth observation archives available.

---

## Sentinel-2 vs Landsat

| Feature               | Sentinel-2 | Landsat 8/9 |
| --------------------- | ---------- | ----------- |
| Spatial Resolution    | 10m        | 30m         |
| Revisit Time          | 5 Days     | 16 Days     |
| Bands                 | 13         | 11          |
| Vegetation Monitoring | Excellent  | Good        |
| Urban Monitoring      | Excellent  | Moderate    |

---

## Why GeoSentinel Chooses Sentinel-2

* Higher resolution
* Better revisit frequency
* Better urban expansion monitoring
* Better vegetation monitoring

---

# 4. Satellite Resolutions

## Spatial Resolution

Definition:

The ground area represented by a single pixel.

Example:

10m resolution means:

1 Pixel = 10m × 10m

Higher spatial resolution provides more detail.

---

## Temporal Resolution

Definition:

How frequently a satellite revisits the same location.

Example:

Sentinel-2 revisits approximately every 5 days.

---

## Spectral Resolution

Definition:

Number and quality of wavelength bands captured by a sensor.

Example:

Sentinel-2 captures 13 spectral bands.

Different bands provide different information about the Earth's surface.

---

# 5. Satellite Metadata

## Definition

Metadata describes information about the satellite image.

---

## Common Metadata Fields

### Acquisition Date

Date image was captured.

---

### Cloud Cover

Percentage of image obscured by clouds.

---

### CRS

Coordinate Reference System.

---

### Spatial Resolution

Pixel size.

---

### Bounding Box

Geographic extent of the image.

---

### Sensor Information

Satellite and instrument details.

---

## Why Metadata Matters

Metadata helps:

* Filter usable imagery
* Remove cloudy images
* Align datasets correctly
* Track acquisition dates
* Support temporal analysis

---

# 6. Google Earth Engine (GEE)

## Definition

Google Earth Engine is a cloud-based geospatial analysis platform.

It hosts large Earth observation datasets and enables large-scale geospatial processing.

---

## Capabilities

* Satellite imagery access
* Geospatial analytics
* Time-series analysis
* Cloud computing

---

## Why Researchers Use It

* No need to download massive datasets
* Scalable processing
* Access to global archives

---

## Potential GeoSentinel Usage

* Data discovery
* Satellite imagery acquisition
* Exploratory analysis
* Time-series visualization

---

# 7. OSCD Dataset

## Full Name

Onera Satellite Change Detection Dataset

---

## Purpose

Benchmark dataset for change detection research.

---

## Contents

* Sentinel-2 imagery
* Multi-temporal image pairs
* Change labels

---

## Relevance

Strong candidate dataset for GeoSentinel model development.

---

# 8. S2Looking Dataset

## Purpose

Building change detection dataset.

---

## Contents

* High-resolution image pairs
* Change annotations

---

## Relevance

Potential evaluation dataset.

---

# OSCD vs S2Looking

| Feature     | OSCD                     | S2Looking                 |
| ----------- | ------------------------ | ------------------------- |
| Data Source | Sentinel-2               | High Resolution Imagery   |
| Focus       | General Change Detection | Building Change Detection |
| Priority    | High                     | Medium                    |

---

# 9. GeoSentinel Data Workflow

Proposed workflow:

Sentinel-2 Imagery
↓
Image Selection
↓
Metadata Validation
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
Risk Assessment
↓
Report Generation
↓
RAG Query System
↓
Dashboard

---

# 10. Level-1C vs Level-2A

## Level-1C

Top of Atmosphere Reflectance

Contains atmospheric effects.

---

## Level-2A

Bottom of Atmosphere Reflectance

Atmospheric correction applied.

---

## Note

Need deeper understanding during imagery acquisition phase.

---

# Key Learnings

* Copernicus provides open Earth observation data.
* Sentinel-2 is the primary imagery source for GeoSentinel.
* Spatial, temporal, and spectral resolutions determine image usefulness.
* Metadata is critical for remote sensing workflows.
* Google Earth Engine is a major platform for geospatial analysis.
* OSCD is a strong candidate dataset.
* Sentinel-2 provides the best balance between quality and accessibility for the project.

---

# Questions For Future Exploration

* How are Sentinel-2 scenes selected?
* How is cloud masking performed?
* How is Level-2A imagery obtained?
* How are image pairs prepared for change detection?
* How will TorchGeo integrate with Sentinel-2 datasets?
