# Day 16 Notes

## Date

June 16, 2026

---

# Semantic Segmentation

Today focused on understanding semantic segmentation, masks, and labels.

---

# 1. What is Semantic Segmentation?

Semantic segmentation assigns a class label to every pixel in an image.

---

# Example

Pixel

↓

Vegetation

Urban

Water

Background

---

# 2. Classification vs Segmentation

Classification:

Image → Label

---

Segmentation:

Image → Pixel-Level Labels

---

# 3. Segmentation Mask

A segmentation mask is an image where each pixel represents a class.

---

Example

0 = Background

1 = Vegetation

2 = Urban

3 = Water

---

# 4. Labels

Labels represent land-cover categories.

---

GeoSentinel Classes

Vegetation

Urban

Water

Background

---

# 5. Ground Truth

Ground truth masks represent the correct class assignments.

They are used for model training.

---

# 6. Prediction Mask

Produced by a trained model.

Compared against ground truth during evaluation.

---

# 7. Segmentation Workflow

Image

↓

Mask

↓

Model

↓

Prediction

↓

Evaluation

---

# 8. GeoSentinel Connection

Vegetation Loss Detection:

Vegetation Mask (Year A)

↓

Vegetation Mask (Year B)

↓

Difference

↓

Vegetation Loss

---

Urban Expansion Detection:

Urban Mask (Year A)

↓

Urban Mask (Year B)

↓

Difference

↓

Urban Expansion

---

# Key Learnings

- Segmentation predicts labels for every pixel.
- Masks store class information.
- Ground truth is required for training.
- Segmentation is central to GeoSentinel.
