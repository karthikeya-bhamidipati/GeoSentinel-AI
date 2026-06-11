# Day 11 – TorchGeo Samplers Deep Dive

Date: June 11, 2026

## Objective

Understand TorchGeo samplers and patch generation workflows.

## Topics Covered

* RandomGeoSampler
* GridGeoSampler
* Patch extraction
* Patch size selection
* DataLoader integration

## Why Samplers?

Satellite imagery is too large to process at once.

Example:

10980 × 10980

Instead:

256 × 256 patches

are extracted.

## RandomGeoSampler

Used for:

* Training

Advantages:

* Diverse samples
* Better generalization
* Reduced overfitting

## GridGeoSampler

Used for:

* Validation
* Testing
* Inference

Advantages:

* Complete image coverage
* Reproducible results

## Patch Sizes

Common values:

* 128
* 256
* 512

Recommended for GeoSentinel AI:

256 × 256

## Workflow

RasterDataset

↓

Sampler

↓

Patch Extraction

↓

DataLoader

↓

Model

## GeoSentinel AI Application

Training:

Sentinel-2

↓

RandomGeoSampler

↓

Model Training

Inference:

Sentinel-2

↓

GridGeoSampler

↓

Urban Expansion Map

↓

Vegetation Loss Map

## Key Learnings

1. Samplers generate training patches.
2. RandomGeoSampler is used for training.
3. GridGeoSampler is used for inference.
4. Patch size affects performance and memory.
5. Samplers work with DataLoaders.

## Outcome

Successfully understood TorchGeo sampling workflows.
