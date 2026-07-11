# GeoSentinel AI
# Project Context

Version: 1.0

Status: Frozen

Purpose:
This document contains the immutable facts and core decisions of the GeoSentinel AI project.

Every AI coding agent, developer and contributor must read this document before making any changes to the project.

The information contained here is considered the source of truth.

---

# Project Identity

Project Name

GeoSentinel AI

Type

Production-quality GeoAI Platform

Category

Earth Observation

Remote Sensing

Deep Learning

Temporal Analytics

Full Stack GIS Application

Target

M.Sc Research Project with production-quality software engineering standards.

---

# Project Goal

Develop an end-to-end geospatial analytics platform capable of

• Automatically retrieving Sentinel-2 imagery

• Monitoring urban expansion

• Monitoring vegetation dynamics

• Performing temporal analysis

• Running AI segmentation

• Producing explainable recommendations

• Generating professional reports

The platform should function as a complete geospatial decision support system.

---

# Study Area

The project is permanently restricted to

Hyderabad Metropolitan Region (HMR)

with approximately

150 km operational operational buffer.

The platform shall not support global analysis.

The frontend shall only display the supported region.

AOIs outside the supported boundary shall be rejected.

---

# Earth Observation Provider

Official Provider

Copernicus Data Space Ecosystem (CDSE)

Authentication

OAuth2

Imagery

Sentinel-2 Level-2A

Primary Bands

B02

B03

B04

B08

B11

The platform should always use the official CDSE APIs.

Google Earth Engine is not used.

Sentinel Hub is not the primary provider.

---

# Data Retrieval Philosophy

The platform never downloads an entire Sentinel scene unless technically unavoidable.

Workflow

User AOI

↓

Search CDSE

↓

Select Best Scene

↓

Download Only AOI

↓

Cache

↓

Process

This minimizes

storage

network usage

processing time

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

AOI Download

↓

Raster Loading

↓

Preprocessing

↓

Feature Engineering

↓

AI Segmentation

↓

Temporal Analytics

↓

Spatial Analytics

↓

Recommendation Engine

↓

Report Generation

↓

Interactive Dashboard

This workflow is frozen.

---

# Spectral Indices

The platform computes

NDVI

NDBI

NDWI

EVI

SAVI

MSAVI

BSI

Indices are used for

analytics

visualization

AI feature stacks

temporal analysis

recommendation engine

---

# Artificial Intelligence

Primary Model

U-Net

Benchmark Model

DeepLabV3+

Benchmark Datasets

OSCD

S2Looking

Evaluation Metrics

IoU

Dice

Precision

Recall

F1 Score

Accuracy

Inference Time

Memory Usage

The AI model is only one subsystem of the platform.

---

# Temporal Analytics

The platform performs

Vegetation Loss Detection

Urban Expansion Detection

NDVI Change

NDBI Change

Transition Matrix Generation

Hotspot Detection

Trend Analysis

The platform should support

Two-Date Analysis

and

Multi-Date Analysis.

---

# Recommendation Engine

Recommendations are

Rule Based

Explainable

Deterministic

Each recommendation contains

Title

Priority

Confidence

Evidence

Affected Area

Reason

Suggested Action

The platform shall not use LLM-generated recommendations.

---

# Reporting

Supported Formats

PDF

CSV

GeoJSON

GeoTIFF

Every report includes

Executive Summary

AOI Information

Maps

Charts

Statistics

Recommendations

Metadata

Appendix

---

# Frontend

Framework

Next.js

React

TypeScript

Leaflet

The frontend performs

User Interaction

Visualization

Dashboard

AOI Selection

Timeline

Reporting

The frontend never performs

AI

Raster Processing

Earth Observation Processing

GIS Analysis

---

# Backend

Framework

FastAPI

Responsibilities

Request Validation

Workflow Orchestration

EO Pipeline

AI Pipeline

Temporal Pipeline

Analytics

Recommendation Engine

Report Generation

---

# User Workflow

User opens application

↓

Interactive Hyderabad map displayed

↓

User draws AOI

↓

User selects dates

↓

User clicks Analyze

↓

System performs complete workflow automatically

↓

Results displayed

↓

Report available for download

The user never manually downloads Sentinel imagery.

---

# User Interface Philosophy

The application should resemble

ArcGIS Pro

Sentinel Hub EO Browser

Google Earth Engine

Planet Explorer

QGIS

The application should NOT resemble

Startup Landing Pages

Cyberpunk Dashboards

Glassmorphism-heavy UIs

Marketing Websites

The map is always the primary interface.

---

# Software Architecture

The project consists of

Frontend

Backend API

Earth Observation Engine

Preprocessing Engine

Feature Engineering Engine

AI Engine

Benchmarking Engine

Temporal Analytics Engine

Spatial Analytics Engine

Recommendation Engine

Reporting Engine

Docker Deployment

Each subsystem owns exactly one responsibility.

---

# Engineering Principles

Follow

SOLID

Clean Architecture

Domain Driven Design

Strong Typing

Modular Design

Production Quality

Avoid

Hardcoded Values

Duplicate Logic

Circular Dependencies

God Classes

Prototype Code

Notebook Style Code

---

# Deployment

Deployment Method

Docker Compose

Command

docker compose up --build

The complete application should run without additional manual configuration.

---

# Repository Status

Architecture

Frozen

Technology Stack

Frozen

Study Area

Frozen

Processing Workflow

Frozen

Repository Structure

Frozen

Only implementation is allowed to evolve.

Core architecture shall remain unchanged.

---

# Definition of Success

GeoSentinel AI is considered complete when a user can

✓ Open the application

✓ Draw an AOI inside Hyderabad

✓ Select dates

✓ Automatically retrieve Sentinel-2 imagery

✓ Run AI segmentation

✓ Perform temporal analysis

✓ View interactive analytics

✓ Receive explainable recommendations

✓ Download professional reports

✓ Deploy the entire platform using Docker

without manual intervention.

---

# Final Statement

GeoSentinel AI is not a machine learning project with a web interface.

It is a complete geospatial decision support platform.

Every engineering decision should reinforce this identity.

If any future implementation conflicts with the principles defined in this document, this document takes precedence.