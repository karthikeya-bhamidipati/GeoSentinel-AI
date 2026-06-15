# Day 14 Notes

## Date

June 14, 2026

---

# GeoSamplers

Today focused on understanding how TorchGeo converts large geospatial datasets into training patches.

---

# 1. Why Sampling is Needed

Sentinel-2 scenes are extremely large.

Example:

10980 × 10980 pixels

Deep learning models require smaller image patches.

---

# 2. GeoSampler

A GeoSampler selects geographic regions from a dataset.

Unlike traditional PyTorch samplers, GeoSamplers work with spatial locations.

---

# 3. RandomGeoSampler

Purpose:

Training

---

Characteristics

- Random patch selection
- Different every epoch
- Better generalization

---

# 4. GridGeoSampler

Purpose:

Inference

---

Characteristics

- Systematic coverage
- Entire image processed
- Deterministic

---

# 5. Patch Size

Patch Size Used:

256 × 256

---

Why Important

Determines:

- Memory usage
- Training speed
- Spatial context

---

# 6. Training Pipeline

Dataset
↓
RandomGeoSampler
↓
Patch Extraction
↓
DataLoader
↓
Model

---

# 7. Inference Pipeline

Dataset
↓
GridGeoSampler
↓
Patch Extraction
↓
Predictions
↓
Final Map

---

# 8. GeoSentinel Connection

Training:

RandomGeoSampler

Inference:

GridGeoSampler

Both are essential for vegetation loss and urban expansion detection.

---

# Key Learnings

- Satellite scenes are too large for direct training.
- GeoSamplers create manageable patches.
- Random sampling improves training diversity.
- Grid sampling enables complete coverage.
- Sampling is a critical stage in geospatial deep learning.
