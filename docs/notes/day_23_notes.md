# Day 23 Notes

## Date

June 23, 2026

---

# GeoSentinel Dataset Organization

Today focused on defining how the final dataset should be structured.

---

# Why Dataset Organization Matters

Proper dataset structure improves:

- Reproducibility
- Training stability
- Experiment management

---

# Recommended Structure

data/

raw/

processed/

labels/

train/

val/

test/

---

# Dataset Splits

Training

70%

---

Validation

15%

---

Testing

15%

---

# Training Set

Purpose:

Model Learning

Weights are updated using training data.

---

# Validation Set

Purpose:

Model Selection

Hyperparameter tuning.

---

# Test Set

Purpose:

Final Evaluation

Used only after training.

---

# Data Leakage

Occurs when information from the test set appears during training.

Can produce misleading performance metrics.

---

# GeoSentinel Strategy

Prefer geographic separation between:

- Training Areas
- Validation Areas
- Test Areas

to improve generalization.

---

# Future Dataset Components

Images

Sentinel-2 patches

---

Masks

WorldCover-derived labels

---

Metadata

Location
Date
Tile Information

---

# Key Learnings

- Dataset organization is critical.
- Proper train/val/test splits are required.
- Data leakage must be avoided.
- Geographic separation improves evaluation quality.
