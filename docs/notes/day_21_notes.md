# Day 21 Notes

## Date

June 21, 2026

---

# Ground Truth and Label Generation

Today focused on defining how GeoSentinel will obtain training labels.

---

# Why Labels Are Required

Segmentation models require:

- Input Image
- Ground Truth Mask

Without labels, supervised training is impossible.

---

# Ground Truth

Ground truth represents the correct class assignment for each pixel.

Example:

0 = Background

1 = Vegetation

2 = Urban

3 = Water

---

# Label Sources

## Manual Annotation

Using QGIS polygons.

Advantages:

- High accuracy

Disadvantages:

- Time consuming

---

## Existing Land Cover Products

Examples:

- ESA WorldCover
- Dynamic World

Advantages:

- Fast
- Large scale

Disadvantages:

- Minor labeling errors

---

# GeoSentinel Strategy

Primary Label Source:

ESA WorldCover

---

# Class Mapping

WorldCover Classes

↓

GeoSentinel Classes

0 = Background

1 = Vegetation

2 = Urban

3 = Water

---

# Training Pair

Input:

Sentinel-2 Patch

Output:

Segmentation Mask

---

# Future Workflow

Sentinel-2
      ↓
WorldCover
      ↓
Mask Generation
      ↓
Dataset
      ↓
U-Net Training

---

# Key Learnings

- Labels are essential for segmentation.
- Ground truth defines the learning target.
- Existing land-cover datasets can accelerate development.
- WorldCover is suitable for GeoSentinel Phase 1.
