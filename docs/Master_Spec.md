# GeoSentinel AI - Master Project Specification

You are a senior Software Architect, Geospatial AI Engineer, Remote Sensing Engineer, Machine Learning Engineer, and Full Stack Developer.

Your task is to generate production-quality code for the GeoSentinel AI platform.

This is NOT a prototype.

This is NOT a notebook project.

This is NOT an academic assignment.

Treat this as a real production software platform.

Every file you generate must follow clean software engineering principles.

---

# Project Overview

GeoSentinel AI is a cloud-native geospatial analytics platform for monitoring urban expansion and vegetation dynamics using Sentinel-2 imagery.

The study area is permanently restricted to the Hyderabad Metropolitan Region (HMR).

The user interacts through a web application.

The user workflow is:

1. Open the web application.
2. View only the Hyderabad Metropolitan Region map.
3. Draw an Area of Interest (AOI).
4. Select two dates.
5. Click Analyze.
6. The platform automatically retrieves Sentinel-2 imagery from CDSE.
7. Only the requested AOI is downloaded.
8. Spectral indices are computed.
9. A U-Net segmentation model performs land-cover prediction.
10. Temporal analysis compares the two dates.
11. Spatial analytics compute area changes and statistics.
12. A rule-based recommendation engine generates recommendations.
13. The platform displays an interactive dashboard.
14. The user downloads a PDF report.

No manual Sentinel download.

No manual preprocessing.

Everything is automated.

---

# Study Area

The platform ONLY supports Hyderabad Metropolitan Region.

The frontend map must always be restricted to the HMR plus approximately 150 km operational buffer.

The user cannot analyze any location outside this region.

AOIs outside the boundary must be rejected.

---

# Earth Observation

Imagery source:

Copernicus Data Space Ecosystem (CDSE)

Do NOT use Google Earth Engine.

Do NOT use Sentinel Hub unless specifically required later.

Use the official CDSE APIs.

Only download imagery intersecting the AOI.

Never download an entire Sentinel scene when an AOI request is sufficient.

Use caching to avoid repeated downloads.

---

# Processing Workflow

AOI

↓

Validation

↓

Cache Lookup

↓

CDSE Search

↓

Download AOI

↓

Raster Loading

↓

Preprocessing

↓

Feature Engineering

↓

Deep Learning

↓

Temporal Analysis

↓

Spatial Analytics

↓

Recommendation Engine

↓

Reporting

↓

Dashboard

---

# Spectral Features

Generate at minimum:

- NDVI
- NDBI
- NDWI
- EVI
- SAVI
- MSAVI
- BSI

These become additional model features and analytical layers.

---

# AI

Primary segmentation model:

U-Net

Comparison model:

DeepLabV3+

Benchmark datasets:

- OSCD
- S2Looking

Evaluation metrics:

- IoU
- Dice
- Precision
- Recall
- F1
- Accuracy

---

# Temporal Analysis

Perform:

NDVI Change

NDBI Change

Segmentation Change

Transition Matrix

Urban Expansion

Vegetation Loss

Hotspot Detection

Trend Statistics

---

# Recommendation Engine

Implement a rule-based explainable recommendation engine.

Recommendations are generated from spatial statistics.

Do NOT use an LLM.

Recommendations must be deterministic.

Example:

Large vegetation loss

↓

Recommend afforestation.

Urban expansion near water

↓

Recommend planning restrictions.

Every recommendation must explain WHY it was generated.

---

# Reporting

Generate:

PDF

CSV

GeoJSON

GeoTIFF

Include:

Maps

Charts

Statistics

Recommendations

Metadata

Model metrics

Confidence

---

# Backend

Framework:

FastAPI

Responsibilities:

Validation

Pipeline orchestration

AI execution

Report generation

REST API

The backend owns all processing.

---

# Frontend

Framework:

Next.js

React

TypeScript

Leaflet

Responsibilities:

Map

AOI drawing

Date selection

Dashboard

Timeline

Charts

Reports

The frontend performs NO GIS processing.

---

# Docker

The project must run using:

docker compose up --build

Containers:

Frontend

Backend

Python AI Engine

Volumes:

Cache

Outputs

Models

Data

---

# Repository Philosophy

Every folder owns one responsibility.

Every class owns one responsibility.

Every file owns one responsibility.

Use SOLID principles.

Avoid circular dependencies.

Avoid God classes.

Prefer composition over inheritance.

---

# Coding Standards

Use:

Python 3.12+

Type hints everywhere.

Dataclasses for domain models.

Enums for constants.

Absolute imports.

Google-style docstrings.

Logging instead of print().

Custom exceptions.

No hardcoded paths.

No hardcoded credentials.

No duplicated code.

Small cohesive classes.

---

# Architecture

Presentation Layer

↓

FastAPI

↓

Application Services

↓

Earth Observation Engine

↓

Preprocessing

↓

Feature Engineering

↓

AI Engine

↓

Temporal Engine

↓

Analytics

↓

Recommendation

↓

Reporting

↓

Infrastructure

---

# Earth Observation Engine

Contains:

AOI

AnalysisRequest

Scene

Raster

Metadata

Providers

CDSE

Cache

Raster Loader

No AI code belongs here.

---

# Preprocessing

Responsible for:

Normalization

Clipping

Alignment

Resampling

Cloud Masking

No feature computation here.

---

# Feature Engineering

Responsible only for spectral indices.

No AI.

---

# AI

Responsible only for:

Training

Inference

Evaluation

No raster downloading.

---

# Temporal

Responsible only for comparing two processed scenes.

---

# Analytics

Responsible for:

Statistics

Area calculations

District summaries

Transition tables

---

# Reporting

Responsible only for exporting outputs.

---

# File Generation Rules

When generating code:

Generate complete production-quality files.

Never generate placeholders.

Never generate TODO comments.

Never omit imports.

Never assume hidden code exists.

Every file must be independently executable where appropriate.

Every public class must include documentation.

Every function must include type hints.

---

# Testing

Every module should be written to be unit-testable.

Separate business logic from I/O.

Use dependency injection where appropriate through FastAPI.

---

# Goal

Build a complete production-quality GeoAI platform that demonstrates:

Remote Sensing

Deep Learning

Geospatial Analytics

Temporal Change Detection

Explainable Recommendations

Professional Reporting

Modern Full Stack Development

Docker Deployment

Maintainability

Scalability

Research Reproducibility

Do not simplify the implementation.

Generate code as if this platform will be deployed and maintained long-term.