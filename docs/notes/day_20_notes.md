# Day 20 Notes

## Date

June 20, 2026

---

# GeoSentinel Dataset Design

Today focused on designing the first real dataset structure for GeoSentinel AI.

---

# 1. Dataset Goal

Create a segmentation dataset capable of detecting:

- Vegetation
- Urban Areas
- Water Bodies

using Sentinel-2 imagery.

---

# 2. Classes

Class 0

Background

---

Class 1

Vegetation

---

Class 2

Urban

---

Class 3

Water

---

# 3. Input Data

Sentinel-2 Bands:

- B02 (Blue)
- B03 (Green)
- B04 (Red)
- B08 (NIR)

---

# 4. Spectral Indices

NDVI

Vegetation Detection

---

NDBI

Urban Detection

---

EVI

Dense Vegetation Analysis

---

MSAVI

Sparse Vegetation Analysis

---

# 5. Patch Strategy

Patch Size:

256 × 256

---

Reason

Suitable for:

- GPU memory
- U-Net
- TorchGeo workflows

---

# 6. Training Sample

Input:

Image Patch

Shape:

(4,256,256)

---

Output:

Mask

Shape:

(256,256)

---

# 7. GeoSentinel Pipeline

Sentinel-2

↓

Indices

↓

Patch Extraction

↓

Dataset

↓

U-Net

↓

Segmentation Mask

---

# Key Learnings

- Dataset design determines model capability.
- Proper class definition is essential.
- Spectral indices improve feature representation.
- Patch-based training enables large-scene processing.

---

# Decisions Made

Phase 1 Classes:

Background

Vegetation

Urban

Water

Future classes may be added after baseline model validation.
