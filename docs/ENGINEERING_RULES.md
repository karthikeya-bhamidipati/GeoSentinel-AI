# GeoSentinel AI
# Engineering Rules & Development Standards

Version: 1.0

Status: Frozen

Document Type:
Engineering Constitution

---

# Purpose

This document defines the mandatory engineering rules for the GeoSentinel AI project.

These rules govern:

- Repository organization
- Software architecture
- Code quality
- Module responsibilities
- Naming conventions
- Error handling
- Logging
- Testing
- Performance
- Security
- Deployment

All generated code must comply with these rules.

---

# Engineering Philosophy

GeoSentinel AI is a production-quality software platform.

It is NOT

- a prototype
- a notebook collection
- a proof of concept
- a college assignment

Treat every module as production software.

Prioritize

- readability
- maintainability
- modularity
- scalability
- reproducibility

over writing clever code.

---

# Architecture

The project follows

- SOLID Principles
- Clean Architecture
- Domain Driven Design
- Layered Architecture
- Modular Design
- Separation of Concerns

Every module owns exactly one responsibility.

---

# Layer Structure

Presentation Layer

↓

Application Layer

↓

Domain Layer

↓

Processing Layer

↓

Infrastructure Layer

↓

Storage Layer

Layers communicate only through public interfaces.

Never bypass architectural boundaries.

---

# Module Ownership

Every subsystem owns one responsibility.

| Module | Responsibility |
|----------|---------------|
| EO | Earth Observation |
| Preprocessing | Raster preprocessing |
| Feature Engineering | Spectral indices |
| Models | Neural network definitions |
| Training | Model training |
| Inference | Prediction |
| Temporal | Change detection |
| Analytics | Spatial statistics |
| Recommendation | Decision engine |
| Reporting | Report generation |
| Backend | REST API |
| Frontend | User interface |

No module may perform another module's responsibility.

---

# Repository Rules

Every directory has one purpose.

Never create miscellaneous folders.

Never duplicate functionality.

Never create utility files containing unrelated functions.

---

# Folder Responsibilities

src/

Contains only production source code.

backend/

Contains only API code.

frontend/

Contains only UI code.

scripts/

Contains executable scripts.

tests/

Contains automated tests only.

docs/

Contains documentation only.

data/

Contains runtime data only.

outputs/

Contains generated artifacts only.

---

# Dependency Rules

Allowed

EO → Utils

Preprocessing → EO

Feature Engineering → Preprocessing

Training → Models + Datasets

Inference → Models

Temporal → Inference

Analytics → Temporal

Recommendation → Analytics

Reporting → Analytics + Recommendation

Backend → All Processing Modules

Frontend → Backend API

Forbidden

Frontend → EO

Frontend → AI

Backend → Frontend

Reporting → AI

Recommendation → Raster Processing

Circular imports

---

# Coding Style

Language

Python 3.12+

Every file must include

- module docstring
- type hints
- descriptive comments only where necessary

Avoid unnecessary comments.

Code should explain itself.

---

# Naming Conventions

Files

snake_case.py

Classes

PascalCase

Functions

snake_case

Variables

snake_case

Constants

UPPER_CASE

Enums

PascalCase

Private Members

_prefix

---

# Imports

Always use absolute imports.

Correct

from src.eo.scene import SentinelScene

Incorrect

from ..scene import SentinelScene

Wildcard imports are prohibited.

---

# File Size

Target

200–400 lines.

Maximum

600 lines.

If exceeded,

split the file.

---

# Class Design

One public class per file.

Keep classes cohesive.

Prefer composition over inheritance.

Avoid God classes.

---

# Function Design

One function

↓

One responsibility

Maximum recommended length

50 lines.

Prefer pure functions whenever possible.

---

# Configuration

Never hardcode

- paths
- credentials
- URLs
- model names
- thresholds
- resolutions

Everything must come from

configs/

---

# Logging

Never use

print()

Always use

logging

Every public operation logs

Start

Finish

Duration

Warnings

Errors

Request ID

---

# Error Handling

Never catch generic Exception unless re-raising.

Create domain-specific exceptions.

Examples

AOIValidationError

CDSEAuthenticationError

RasterLoadError

ModelInferenceError

ReportGenerationError

Errors should contain

- cause
- message
- suggested action

---

# Type Safety

Every public function must include type hints.

Avoid Any unless unavoidable.

Prefer dataclasses for immutable domain objects.

---

# Domain Models

Domain models contain

- data
- validation

They should not contain business logic.

Examples

AOI

Raster

Scene

AnalysisRequest

Metadata

---

# AI Rules

The AI module performs only

- training
- inference
- evaluation

It must never

- download imagery
- preprocess files
- generate reports

---

# EO Rules

The EO module owns

- CDSE
- cache
- raster loading
- scene management

It must never perform AI inference.

---

# Frontend Rules

Frontend performs

- visualization
- interaction
- validation of user input

Frontend must never

- access CDSE directly
- run AI
- manipulate rasters

---

# Backend Rules

Backend coordinates the workflow.

Backend should not contain heavy business logic.

Business logic belongs to services and engines.

---

# UI Rules

The application must resemble professional GIS software.

Inspired by

- ArcGIS Pro
- Sentinel Hub EO Browser
- Planet Explorer

Not inspired by

- startup dashboards
- cyberpunk interfaces
- flashy animations

The map is always the primary focus.

---

# Performance

Prefer

streaming

lazy loading

tiling

caching

vectorized computation

Avoid

loading unnecessary imagery

duplicating arrays

blocking UI

---

# Security

Never expose

CDSE credentials

API secrets

environment variables

Validate

AOI

dates

inputs

file paths

before processing.

---

# Testing

Every public module requires

Unit Tests

Every workflow requires

Integration Tests

AI requires

Benchmark Tests

Reports require

Output Validation

---

# Docker

The entire application must start with

docker compose up --build

without manual configuration.

---

# Documentation

Every public class

↓

Docstring

Every public function

↓

Docstring

Every API endpoint

↓

Description

Parameters

Returns

Errors

---

# Code Generation Rules

When generating code

Generate complete implementations.

Do not generate placeholders.

Do not generate TODO comments.

Do not omit imports.

Do not assume hidden files exist.

Do not simplify implementations.

Code should be production-ready.

---

# Pull Request Rules

Every change should

- compile
- pass tests
- follow architecture
- preserve modularity

---

# Definition of Done

A module is complete only when

✓ Code implemented

✓ Tested

✓ Documented

✓ Logged

✓ Configurable

✓ Docker compatible

✓ Integrated

---

# Final Rule

If there is uncertainty between

"quick implementation"

and

"clean architecture"

always choose

clean architecture.