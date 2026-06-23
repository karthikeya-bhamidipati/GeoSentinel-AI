# Day 25 Notes

## Date

June 25, 2026

---

# Multi-Temporal Dataset Preparation

Today focused on preparing Sentinel-2 imagery from two different years for change analysis.

---

# Available Datasets

T1:

Sentinel-2 L2A (2021)

---

T2:

Sentinel-2 L2A (2026)

---

# Selected Bands

B02

Blue

---

B03

Green

---

B04

Red

---

B08

Near Infrared (NIR)

---

# Why These Bands

These bands are required for:

- RGB Visualization
- NDVI Computation
- Vegetation Analysis
- Future Segmentation Tasks

---

# Multi-Temporal Analysis

Definition:

Comparing satellite imagery acquired at different times to identify changes.

---

# GeoSentinel Objective

Detect:

- Vegetation Loss
- Urban Expansion

using temporal differences between 2021 and 2026 imagery.

---

# RGB Composite Generation

Generated comparable RGB visualizations for both years.

Purpose:

- Visual Inspection
- Change Identification
- Data Quality Verification

---

# Temporal Consistency

Requirements:

- Same Tile
- Same Resolution
- Same Projection
- Same Sensor Family

to ensure valid comparison.

---

# Future Analysis

Next steps include:

- NDVI 2021
- NDVI 2026
- NDBI 2021
- NDBI 2026
- Change Maps

---

# Key Learnings

- Multi-temporal analysis is the basis of change detection.
- Consistent preprocessing improves reliability.
- Visual inspection is important before quantitative analysis.
