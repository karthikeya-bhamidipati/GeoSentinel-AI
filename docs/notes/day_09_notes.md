# Day 09 – TorchGeo Fundamentals

## Objective

To understand TorchGeo, its architecture, major components, and how it integrates with PyTorch for geospatial deep learning applications involving satellite imagery.

---

# What is TorchGeo?

TorchGeo is an open-source geospatial deep learning library built on top of PyTorch. It provides datasets, samplers, transforms, and utilities specifically designed for remote sensing and Earth Observation data.

TorchGeo simplifies handling:

* Satellite imagery
* GeoTIFF files
* Multi-band raster data
* Geographic coordinates
* Land-cover datasets
* Spatial sampling

---

# Why TorchGeo?

Traditional PyTorch datasets are designed for conventional image datasets.

Example:

Cats vs Dogs

```python
Dataset -> DataLoader -> Model
```

However, satellite imagery introduces additional challenges:

* Geographic coordinate systems
* Very large image sizes
* Multiple spectral bands
* Geospatial metadata
* Spatially aware sampling

TorchGeo addresses these challenges directly.

---

# TorchGeo Architecture

```text
Satellite Data
      ↓
GeoDataset
      ↓
GeoSampler
      ↓
DataLoader
      ↓
Transforms
      ↓
Model
      ↓
Prediction
```

---

# GeoDataset

Base class for all geospatial datasets.

Purpose:

* Stores geospatial metadata
* Handles spatial indexing
* Supports coordinate-based querying

Hierarchy:

```text
GeoDataset
    │
    ├── RasterDataset
    ├── VectorDataset
    └── IntersectionDataset
```

---

# RasterDataset

Used for raster-based imagery.

Examples:

* Sentinel-2
* Landsat
* NAIP
* DEM

Raster data consists of pixels arranged in a grid.

Example:

```text
[][][][]
[][][][]
[][][][]
```

Applications:

* Land-cover classification
* Change detection
* Semantic segmentation

---

# VectorDataset

Used for vector-based geographic data.

Examples:

* Building footprints
* Roads
* Administrative boundaries
* Rivers

Vector data contains:

* Points
* Lines
* Polygons

Applications:

* Ground-truth labels
* Spatial overlays
* Feature extraction

---

# IntersectionDataset

Combines multiple geospatial datasets spatially.

Example:

```python
dataset = image_dataset & label_dataset
```

Purpose:

* Align imagery and labels
* Create training-ready datasets
* Enable supervised learning workflows

---

# GeoSamplers

GeoSamplers determine how image patches are extracted.

---

## RandomGeoSampler

Randomly selects patches.

Used during:

* Training

Advantages:

* Better generalization
* Increased sample diversity

Concept:

```text
□     □
   □
      □
```

---

## GridGeoSampler

Extracts patches in a regular grid.

Used during:

* Validation
* Testing
* Inference

Concept:

```text
□ □ □
□ □ □
□ □ □
```

Advantages:

* Full image coverage
* Reproducible results

---

# DataModule

Organizes data pipelines.

Responsibilities:

* Training loader
* Validation loader
* Testing loader

Benefits:

* Cleaner code
* Reproducibility
* Easier experimentation

---

# Transforms

Used for preprocessing and augmentation.

Examples:

* Normalization
* Random Flip
* Random Rotation
* Band Selection

Example:

```python
transform = transforms.Compose([
    Normalize(),
    RandomFlip()
])
```

---

# Sample Output Structure

Typical TorchGeo sample:

```python
sample = dataset[0]
```

Output:

```python
{
    "image": tensor,
    "bbox": BoundingBox
}
```

Segmentation output:

```python
{
    "image": tensor,
    "mask": tensor,
    "bbox": BoundingBox
}
```

---

# Application to GeoSentinel AI

Project Workflow:

```text
Sentinel-2 Images
        ↓
RasterDataset
        ↓
RandomGeoSampler
        ↓
DataLoader
        ↓
Deep Learning Model
        ↓
Urban Expansion Detection
        ↓
Vegetation Loss Detection
        ↓
Change Maps
```

TorchGeo will be used for:

* Sentinel-2 data handling
* Patch extraction
* Data loading
* Training preparation
* Geospatial metadata management

---

# Key Learnings

1. TorchGeo extends PyTorch for geospatial applications.
2. RasterDataset handles satellite imagery.
3. VectorDataset manages geographic features.
4. IntersectionDataset merges imagery and labels.
5. RandomGeoSampler is used for training.
6. GridGeoSampler is used for inference.
7. TorchGeo simplifies large-scale satellite image workflows.

---

# Outcome

Successfully understood TorchGeo architecture and its role in the GeoSentinel AI project pipeline.
