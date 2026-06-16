# Day 15 Notes

## Date

June 15, 2026

---

# DataLoaders and DataModules

Today focused on understanding how geospatial datasets are transformed into batches for deep learning.

---

# 1. DataLoader

## Definition

A DataLoader provides batches of data during training.

---

## Responsibilities

- Batch creation
- Shuffling
- Efficient loading
- Parallel processing

---

# 2. Batch

## Definition

A batch is a collection of samples processed together.

---

Example:

Batch Size = 4

Input Shape:

(4,4,256,256)

---

# 3. Batch Dimensions

(B,C,H,W)

Where:

B = Batch Size

C = Channels

H = Height

W = Width

---

# 4. Why Batches Are Needed

Benefits:

- Faster training
- Better GPU utilization
- Stable gradient updates

---

# 5. DataModule

## Definition

A DataModule organizes:

- Training Data
- Validation Data
- Test Data
- DataLoaders

into a single structure.

---

## Benefits

- Cleaner code
- Reproducibility
- Easier experimentation

---

# 6. GeoSentinel Pipeline

Sentinel-2
↓
RasterDataset
↓
GeoSampler
↓
DataLoader
↓
Batch
↓
Model

---

# 7. Sample Structure

Image:

(4,256,256)

Mask:

(256,256)

---

# Key Learnings

- DataLoaders create batches.
- Batch size affects training efficiency.
- Models consume batches, not individual images.
- DataModules organize datasets and loaders.
- TorchGeo integrates seamlessly with PyTorch DataLoaders.
