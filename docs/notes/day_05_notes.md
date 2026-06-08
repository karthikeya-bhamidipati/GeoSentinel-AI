# Day 05 Notes

## Date

June 5, 2026

---

# First Geospatial Programming Day

Today marked the transition from remote sensing theory to practical geospatial programming using Python and real Sentinel-2 Level-2A satellite products.

---

# 1. Sentinel-2 SAFE Product Structure

The downloaded Sentinel-2 dataset was provided as a SAFE product.

Example:

S2B_MSIL2A_20260601T050649_N0512_R019_T43QHV_20260601T085256.SAFE

---

## SAFE Product Components

DATASTRIP

Contains acquisition metadata.

---

GRANULE

Contains actual satellite imagery.

---

IMG_DATA

Contains spectral bands.

---

QI_DATA

Contains quality information.

---

# 2. Sentinel-2 Resolutions

Sentinel-2 bands are grouped by spatial resolution.

---

## R10m

10 meter resolution bands.

Contains:

* B02 (Blue)
* B03 (Green)
* B04 (Red)
* B08 (NIR)

These are the most important bands for GeoSentinel.

---

## R20m

20 meter resolution bands.

Contains:

* B05
* B06
* B07
* B11
* B12

---

## R60m

60 meter resolution bands.

Contains:

* B01
* B09
* B10

---

# 3. Rasterio

Rasterio was used to access Sentinel-2 imagery programmatically.

Example:

```python
import rasterio

dataset = rasterio.open("B04.jp2")
```

Rasterio supports:

* GeoTIFF
* JPEG2000 (.jp2)
* Metadata access
* CRS access
* Raster operations

---

# 4. Sentinel-2 Bands

## B04

Red Band

Used for:

* Vegetation monitoring
* NDVI calculation

Resolution:

10m

---

## B08

Near Infrared Band

Used for:

* Vegetation monitoring
* NDVI calculation

Resolution:

10m

---

## Importance

Healthy vegetation absorbs Red light and reflects Near Infrared energy.

---

# 5. Metadata Exploration

Examined:

* CRS
* Width
* Height
* Bounds
* Resolution
* Data Type

---

## Key Observation

Satellite imagery contains both image data and geospatial context.

Without metadata, spatial analysis would not be possible.

---

# 6. Raster Structure

Raster imagery is represented as NumPy arrays.

Example:

Rows × Columns

Every cell represents a pixel value.

---

## Relationship to Machine Learning

Sentinel-2
↓
Rasterio
↓
NumPy Arrays
↓
TorchGeo
↓
PyTorch
↓
Deep Learning

---

# 7. Band Visualization

Individual spectral bands were visualized.

Observations:

* Different bands emphasize different surface properties.
* Vegetation appears differently in Red and NIR bands.
* Spectral information is hidden from normal RGB imagery.

---

# 8. GeoSentinel Connection

Current pipeline understanding:

SAFE Product
↓
Band Extraction
↓
Rasterio
↓
NumPy Arrays
↓
NDVI Generation
↓
Change Detection
↓
Urban Expansion Detection
↓
Vegetation Loss Detection

---

# Key Learnings

* Sentinel-2 SAFE products contain structured satellite data.
* Bands are stored separately rather than in a single image.
* Rasterio can directly read Sentinel-2 JPEG2000 files.
* Metadata is essential for geospatial analysis.
* Sentinel imagery is fundamentally numerical data.
* B04 and B08 will become the primary inputs for NDVI.

---

# Questions For Future Exploration

* How should multiple bands be stacked?
* How will NDVI be generated from B04 and B08?
* How does TorchGeo handle SAFE products?
* How are Sentinel-2 scenes prepared for model training?
