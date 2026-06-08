# Day 05 Project Log

Date: June 5, 2026

Status: Completed

---

# Objectives

* Learn Rasterio
* Access Sentinel-2 imagery programmatically
* Explore SAFE product structure
* Read raster metadata
* Understand band organization
* Visualize satellite bands

---

# Completed Tasks

## SAFE Product Exploration

Explored downloaded Sentinel-2 Level-2A SAFE product.

Understood:

* DATASTRIP
* GRANULE
* IMG_DATA
* QI_DATA

---

## Sentinel-2 Band Organization

Studied:

R10m

* B02
* B03
* B04
* B08

R20m

* B05
* B06
* B07
* B11
* B12

R60m

* B01
* B09
* B10

---

## Rasterio

Installed and verified Rasterio.

Successfully opened Sentinel-2 JP2 files.

---

## Metadata Exploration

Inspected:

* CRS
* Width
* Height
* Bounds
* Resolution
* Band information

---

## Raster Structure

Learned how Sentinel-2 bands are represented as NumPy arrays.

Established connection between remote sensing and machine learning pipelines.

---

## Visualization

Visualized Sentinel-2 bands.

Observed spectral differences between bands.

---

# Challenges Faced

Initial assumption was that Sentinel-2 imagery would be provided as a single GeoTIFF.

Discovered that official Sentinel-2 products are distributed as SAFE archives containing multiple JPEG2000 band files.

---

# Resolution

Adjusted workflow to use Sentinel-2 SAFE structure directly.

Learned how remote sensing researchers typically work with SAFE products.

---

# Learnings

* Sentinel-2 SAFE products contain structured datasets.
* Spectral bands are stored individually.
* Rasterio supports JPEG2000 files.
* Satellite imagery is fundamentally numerical raster data.
* Metadata is critical for geospatial workflows.
* B04 and B08 are essential for vegetation analysis.

---

# Decisions Made

## Preferred Product

Sentinel-2 Level-2A

---

## Primary Bands

B04 (Red)

B08 (NIR)

---

## Primary Raster Library

Rasterio

---

# Project Impact

Day 05 established the foundation for:

* NDVI generation
* Band processing
* Vegetation monitoring
* Future change detection workflows

The project is now capable of accessing and interpreting real Sentinel-2 datasets programmatically.

---

# Additional Progress

Continued strengthening understanding of:

* TorchGeo
* Sentinel-2 products
* Geospatial raster processing

Project remains ahead of schedule.

---

# Next Steps

Day 06:

* Read B04 and B08 bands
* Generate NDVI
* Visualize NDVI
* Perform first vegetation intelligence analysis
* Create first remote sensing output

---

# Completion Status

Day 05 Completed Successfully

Progress:

5 / 60 Days Completed

Project Status:

Ahead of Schedule
