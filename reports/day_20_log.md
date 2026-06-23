# Day 20 Project Log

Date: June 20, 2026

Status: Completed

---

# Objectives

- Design GeoSentinel dataset
- Define classes
- Define inputs
- Define outputs
- Select spectral indices
- Define patch strategy

---

# Completed Tasks

## Dataset Design

Created the first GeoSentinel dataset blueprint.

---

## Class Definition

Defined:

- Background
- Vegetation
- Urban
- Water

---

## Input Selection

Selected Sentinel-2 bands:

- B02
- B03
- B04
- B08

---

## Spectral Index Selection

Selected:

- NDVI
- NDBI
- EVI
- MSAVI

---

## Patch Strategy

Selected:

256 × 256 patches

---

## Training Workflow Design

Mapped:

Patch
↓
Model
↓
Mask

workflow.

---

# Challenges Faced

No major technical issues encountered.

---

# Learnings

- Dataset structure directly affects model quality.
- Class selection should remain manageable.
- Spectral indices provide domain-specific information.
- Patch-based workflows are essential.

---

# Decisions Made

GeoSentinel Phase 1 will focus on:

1. Vegetation
2. Urban
3. Water

before expanding to more classes.

---

# Project Impact

Day 20 marks the beginning of actual GeoSentinel system development.

This is the first day directly contributing to the final AI pipeline.

---

# Next Steps

Day 21:

- Label Generation Strategy
- Ground Truth Creation
- Mask Design
- Dataset Preparation for Training

---

# Completion Status

Day 20 Completed Successfully

Progress:

20 / 60 Days Completed

Project Status:

Core Development Started
