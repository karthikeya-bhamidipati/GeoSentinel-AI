# Day 06 Notes

## Date

June 6, 2026

---

# First NDVI Analysis

Today marked the first remote sensing analysis performed within GeoSentinel AI.

Using Sentinel-2 imagery, vegetation information was extracted through the Normalized Difference Vegetation Index (NDVI).

This is the first intelligence product generated from real satellite data.

---

# 1. NDVI

## Definition

NDVI stands for:

Normalized Difference Vegetation Index

It is one of the most widely used vegetation indicators in remote sensing.

---

## Formula

NDVI = (B08 - B04) / (B08 + B04)

Where:

* B04 = Red Band
* B08 = Near Infrared Band (NIR)

---

## NDVI Range

Theoretical range:

-1 to +1

---

## Interpretation

| NDVI Value | Interpretation      |
| ---------- | ------------------- |
| < 0.0      | Water               |
| 0.0 - 0.1  | Urban/Barren        |
| 0.1 - 0.3  | Sparse Vegetation   |
| 0.3 - 0.6  | Moderate Vegetation |
| > 0.6      | Dense Vegetation    |

---

# 2. Why NDVI Works

Healthy vegetation behaves differently from urban surfaces.

Vegetation:

* Absorbs Red light
* Reflects Near Infrared light

As a result:

NIR > Red

which produces higher NDVI values.

---

## Urban Areas

Urban surfaces generally have similar reflectance values across Red and NIR bands.

This produces lower NDVI values.

---

# 3. Sentinel-2 Bands Used

## B04

Red Band

Resolution:

10m

Purpose:

* Vegetation monitoring
* NDVI generation

---

## B08

Near Infrared Band

Resolution:

10m

Purpose:

* Vegetation monitoring
* NDVI generation

---

# 4. Data Preparation

Loaded:

* B04 (Red)
* B08 (NIR)

from the Sentinel-2 SAFE product.

---

## Validation Checks

Verified:

* Same dimensions
* Same CRS
* Same resolution
* Same spatial bounds

---

## Importance

NDVI calculation requires perfectly aligned bands.

---

# 5. NDVI Generation

Workflow:

SAFE Product
↓
Extract B04
↓
Extract B08
↓
Convert to Float
↓
Apply NDVI Formula
↓
Generate NDVI Raster

---

## Statistical Analysis

Computed:

* Minimum NDVI
* Maximum NDVI
* Mean NDVI

These values provide insight into overall vegetation conditions.

---

# 6. NDVI Visualization

NDVI map visualized using:

RdYlGn Color Map

---

## Color Interpretation

Red:

* Urban areas
* Bare soil
* Built-up regions

---

Yellow:

* Sparse vegetation

---

Green:

* Dense vegetation
* Parks
* Agricultural land

---

# 7. Vegetation Classification

NDVI values categorized into:

Dense Vegetation

NDVI > 0.6

---

Moderate Vegetation

0.3 ≤ NDVI ≤ 0.6

---

Sparse Vegetation

0.1 ≤ NDVI < 0.3

---

Urban/Barren

NDVI < 0.1

---

# 8. GeoSentinel Connection

NDVI is the foundation of vegetation monitoring within GeoSentinel.

Future workflow:

Sentinel-2
↓
NDVI
↓
Multi-Temporal NDVI
↓
Vegetation Change Detection
↓
Vegetation Loss Detection
↓
Risk Analysis

---

# 9. Importance of NDVI

NDVI transforms imagery into quantitative information.

Instead of visually observing vegetation, NDVI measures vegetation health and density numerically.

This makes automated analysis possible.

---

# Key Learnings

* NDVI is generated from Red and NIR bands.
* Vegetation reflects NIR strongly.
* Satellite imagery can be transformed into measurable indicators.
* NDVI is a foundational remote sensing product.
* GeoSentinel will use NDVI for vegetation monitoring and change detection.
* Remote sensing combines physics, imagery, and data analysis.

---

# Questions For Future Exploration

* How does NDVI change across seasons?
* How can NDVI be compared across years?
* What are NDVI limitations?
* How can NDVI support change detection models?
* How can NDVI be combined with deep learning outputs?
