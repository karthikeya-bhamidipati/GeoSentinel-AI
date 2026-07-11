# GeoSentinel AI
# Feature Specifications

Version: 1.0

Status: Frozen

This document defines every functional feature of GeoSentinel AI.

Each feature contains:

- Purpose
- User Story
- Functional Behaviour
- UI Requirements
- Backend Requirements
- Acceptance Criteria
- Future Extensions

---

# FEATURE 01

# Interactive HMR Map

Priority

★★★★★ Critical

---

## Description

The landing page shall display an interactive map centered on the Hyderabad Metropolitan Region (HMR).

This map is the primary workspace of the platform.

The application should feel similar to professional GIS software rather than a website.

---

## User Story

As a user,

I want to immediately see Hyderabad on launch,

so that I can begin analysis without navigation.

---

## Functional Behaviour

• Map loads automatically.

• HMR boundary highlighted.

• Outside region greyed out.

• User cannot pan outside operational extent.

• Default zoom shows complete HMR.

---

## Supported Basemaps

Satellite

Hybrid

OpenStreetMap

Terrain

Road

---

## Map Controls

Zoom

Home

North Arrow

Scale Bar

Coordinates

Measurement Tool

Layer Manager

Fullscreen

---

## Acceptance Criteria

✓ Loads within 3 seconds.

✓ Only Hyderabad visible.

✓ Responsive.

✓ Smooth zoom.

---

# FEATURE 02

# AOI Selection

Priority

★★★★★ Critical

---

## Supported Selection

Rectangle

Polygon

Circle

Freehand

---

## Behaviour

User draws AOI.

↓

AOI validated.

↓

AOI displayed.

↓

Area calculated.

↓

Centroid calculated.

↓

Ready for analysis.

---

## Restrictions

Cannot draw outside HMR.

Maximum AOI area configurable.

Invalid geometries rejected.

---

## Acceptance Criteria

✓ AOI editable.

✓ AOI removable.

✓ Area displayed.

✓ Coordinates available.

---

# FEATURE 03

# Timeline Selection

Priority

★★★★★ Critical

---

## Inputs

Start Date

End Date

Maximum Cloud %

Resolution

Preferred Bands

---

## Behaviour

System automatically selects nearest available Sentinel imagery.

User never manually selects products.

---

## Acceptance Criteria

✓ Calendar UI.

✓ Validation.

✓ Date range preview.

---

# FEATURE 04

# CDSE Retrieval

Priority

★★★★★ Critical

---

## Behaviour

Authenticate.

↓

Search scenes.

↓

Rank candidates.

↓

Select best.

↓

Download AOI.

↓

Cache.

↓

Return Scene.

---

## Ranking Factors

Lowest cloud cover.

Closest acquisition date.

Correct processing level.

Coverage completeness.

---

## Acceptance Criteria

✓ OAuth.

✓ Retry.

✓ Timeout handling.

✓ Download progress.

---

# FEATURE 05

# Raster Processing

Priority

★★★★★ Critical

---

## Operations

Load bands.

Normalize.

Clip AOI.

Align.

Resample.

Cloud mask.

Create Scene.

---

## Supported Bands

B02

B03

B04

B08

B11

---

# FEATURE 06

# Feature Engineering

Priority

★★★★★ Critical

---

## Indices

NDVI

NDBI

NDWI

EVI

SAVI

MSAVI

BSI

---

## Output

Feature Stack

Statistics

Visual Layers

---

# FEATURE 07

# AI Segmentation

Priority

★★★★★ Critical

---

## Primary

U-Net

---

## Benchmark

DeepLabV3+

---

## Outputs

Urban Mask

Vegetation Mask

Confidence Map

Probability Map

Inference Metrics

---

## Acceptance Criteria

Prediction completes.

Masks visualized.

Metrics available.

---

# FEATURE 08

# Temporal Analytics

Priority

★★★★★ Critical

---

## Comparisons

Two Dates

Multiple Dates

---

## Analytics

Urban Growth

Vegetation Loss

NDVI Change

NDBI Change

Transition Matrix

Hotspots

Trend Curves

---

## Visualization

Animated timeline.

Difference maps.

Heatmaps.

Trend charts.

---

# FEATURE 09

# Spatial Analytics

Priority

★★★★★ Critical

---

## Statistics

Area

Percentage

District Summary

Class Distribution

Transition Statistics

Largest Changes

---

## Charts

Pie

Bar

Timeline

Histogram

---

# FEATURE 10

# Recommendation Engine

Priority

★★★★★ Critical

---

Recommendations must be deterministic.

No LLM.

Every recommendation contains

Title

Priority

Confidence

Reason

Evidence

Affected Area

Suggested Action

Supporting Statistics

---

Example

Vegetation Loss

↓

High Priority

↓

Evidence

↓

Recommendation

---

# FEATURE 11

# Interactive Dashboard

Priority

★★★★★ Critical

---

Layout

Left Sidebar

↓

Large Map

↓

Statistics Panel

↓

Timeline

↓

Recommendations

---

Widgets

Comparison Viewer

Swipe Slider

Opacity Slider

Layer Manager

Legend

Charts

Statistics

Downloads

---

# FEATURE 12

# Comparison Viewer

Priority

★★★★★ Critical

---

Supports

Before / After

Swipe

Opacity

Split View

Difference Layer

Classification Layer

NDVI Layer

NDBI Layer

---

# FEATURE 13

# Report Generation

Priority

★★★★★ Critical

---

Formats

PDF

CSV

GeoJSON

GeoTIFF

---

Sections

Cover

Executive Summary

Methodology

AOI

Maps

Charts

Statistics

Recommendations

Metadata

Appendix

---

# FEATURE 14

# Benchmark Dashboard

Priority

★★★★☆

---

Compare

U-Net

DeepLabV3+

---

Metrics

IoU

Dice

Precision

Recall

F1

Accuracy

Inference Time

Memory Usage

Training Curves

---

# FEATURE 15

# Settings

Priority

★★★★☆

---

Configuration

CDSE Credentials

Cache

Models

Theme

Downloads

Outputs

Reference Data

Logs

Docker Status

---

# FEATURE 16

# Docker Deployment

Priority

★★★★★ Critical

---

Single command

docker compose up --build

Must launch

Frontend

Backend

AI Engine

Volumes

Outputs

Cache

Logs

---

# FEATURE 17

# Logging

Priority

★★★★★

---

Every request receives

Request ID

Timestamp

AOI Hash

Duration

Errors

Warnings

Progress

---

# FEATURE 18

# Benchmark Datasets

Priority

★★★★★

---

OSCD

S2Looking

WorldCover

---

Evaluation

IoU

Dice

Precision

Recall

F1

Accuracy

---

# FEATURE 19

# Future Ready

Priority

★★★☆☆

---

Architecture prepared for

ChangeFormer

BIT-CD

ScratchFormer

SAM

Additional cities

Ward analytics

3D visualization

Predictive modelling

Cloud deployment

---

# PRODUCT ACCEPTANCE

GeoSentinel AI is considered complete when

✓ Entire workflow is automated

✓ No manual Sentinel downloads

✓ Professional GIS interface

✓ Explainable recommendations

✓ Temporal analytics

✓ AI benchmarking

✓ Professional reports

✓ Docker deployment

✓ Production-quality codebase

✓ Modular architecture

✓ Fully reproducible research platform