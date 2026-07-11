# GeoSentinel AI
# User Interface & User Experience Specification

Version: 1.0

Status: Frozen

---

# Purpose

This document defines the visual language, interaction model, user experience, layouts, workflows, components, animations and design philosophy of GeoSentinel AI.

The objective is to build a professional geospatial application rather than a generic web dashboard.

The application should resemble enterprise GIS software while remaining modern, clean and intuitive.

---

# Design Philosophy

The application should feel like

✓ ArcGIS Pro

✓ Sentinel Hub EO Browser

✓ Planet Explorer

✓ Google Earth Engine

✓ QGIS

NOT

✗ Startup Landing Page

✗ Cyberpunk Dashboard

✗ Hacker UI

✗ Glassmorphism Everywhere

✗ Fancy Animations

✗ Oversized Cards

---

# Design Principles

Professional

Minimal

Engineering Focused

Map First

Data Driven

Accessible

Fast

Responsive

Consistent

---

# Visual Identity

The map is the product.

Everything else supports the map.

The interface should disappear behind the data.

Users should never feel overwhelmed.

The application should communicate

precision

reliability

professionalism

scientific credibility

---

# Color Palette

Primary

Blue

Used for

Buttons

Highlights

Selection

Links

---

Secondary

Green

Used only for

Vegetation

Positive indicators

Healthy regions

---

Warning

Orange

Urban expansion

Attention

Medium severity

---

Critical

Red

High vegetation loss

Errors

Critical recommendations

---

Neutral

White backgrounds

Light grey panels

Dark grey text

Very subtle borders

---

Dark Theme

Optional

Not default.

---

# Typography

Modern sans-serif.

Recommended

Inter

or

Source Sans Pro

Hierarchy

Heading 1

Heading 2

Section

Body

Caption

Monospace

Never use decorative fonts.

---

# Layout Philosophy

The application should always prioritize

MAP

over

PANELS

The user should always feel that they are working with geospatial information.

---

# Application Layout

--------------------------------------------------

Top Navigation

--------------------------------------------------

Left Sidebar

↓

Map Workspace

↓

Right Information Panel

↓

Bottom Status Bar

--------------------------------------------------

---

# Top Navigation

Contains

Project Name

Current Analysis

Search

Notifications

Settings

User Menu (future)

Height

Minimal

Fixed

---

# Left Sidebar

Persistent.

Collapsed by default.

Contains

Analysis

Layers

Timeline

Analytics

Reports

Benchmark

Settings

Help

Icons always visible.

---

# Main Workspace

Occupies approximately

70–80%

of the viewport.

Contains

Interactive map.

Comparison viewer.

Raster overlays.

AOI.

No unnecessary widgets.

---

# Right Sidebar

Context aware.

Changes depending on workflow.

Examples

AOI Statistics

Temporal Statistics

Layer Properties

Recommendations

Metadata

Report Preview

---

# Bottom Status Bar

Always visible.

Contains

Coordinates

Zoom Level

CRS

Current Layer

Scale

Selected Pixel Value

Processing Status

---

# Landing Screen

When application opens

User immediately sees

Hyderabad Metropolitan Region

No marketing.

No hero image.

No feature cards.

No scrolling.

The application opens directly into analysis mode.

---

# Map Behaviour

Default View

Hyderabad Metropolitan Region

Outside Area

Greyed Out

Cannot Pan Outside

Cannot Draw Outside

Default Zoom

Entire HMR visible

---

# Supported Basemaps

Satellite

Hybrid

OpenStreetMap

Terrain

Road

Dark (optional)

---

# Map Controls

Zoom

Home

Scale Bar

North Arrow

Coordinate Display

Fullscreen

Layer Control

Opacity

Swipe

Measurement

Legend

---

# AOI Tools

Rectangle

Polygon

Circle

Freehand

Edit

Delete

Undo

Redo

Area

Perimeter

Centroid

---

# Analysis Panel

Should appear as a clean side panel.

Contains only

AOI Summary

Start Date

End Date

Cloud %

Resolution

Model

Analyze Button

Nothing else.

---

# Progress Experience

When processing

Display

Pipeline

✓ AOI Validated

✓ Searching CDSE

✓ Downloading

✓ Preprocessing

✓ Computing Features

✓ Running AI

✓ Temporal Analysis

✓ Generating Report

Progress should be informative.

Never use spinning loaders alone.

---

# Results Workspace

Large comparison map.

Layer manager.

Statistics panel.

Recommendation panel.

Timeline.

Charts.

Everything synchronized.

---

# Comparison Viewer

Support

Before

After

Swipe

Opacity

Difference

Side-by-side

Linked Zoom

---

# Layer Manager

Toggle

Satellite

Segmentation

NDVI

NDBI

NDWI

Urban

Vegetation

Change Map

Heatmap

Confidence

Labels

---

# Timeline

Slider.

Supports

Multiple years.

Animation.

Play.

Pause.

Forward.

Backward.

---

# Charts

Professional.

No 3D charts.

Use

Bar

Pie

Line

Area

Histogram

Box Plot

Scatter

Charts should support export.

---

# Recommendation Panel

Each recommendation displayed as

Title

Priority

Confidence

Evidence

Affected Area

Reason

Suggested Action

Recommendations should never appear as plain text.

---

# Report Preview

Mini report viewer.

Cover page preview.

Generated pages.

Download buttons.

---

# Benchmark Page

Professional comparison.

Columns

Model

IoU

Dice

Precision

Recall

F1

Inference Time

Training Time

Memory

Training Curves

Confusion Matrix

---

# Settings

General

Downloads

Cache

Models

CDSE

Docker

Appearance

Reference Data

Logging

---

# Notifications

Minimal.

Bottom-right.

Auto dismiss.

Never intrusive.

---

# Error States

Every error should explain

What happened.

Why it happened.

How to fix it.

Never expose stack traces.

---

# Empty States

Instead of empty pages

Show

Helpful illustration.

Simple explanation.

Suggested next action.

---

# Loading States

Skeleton screens.

Pipeline progress.

Estimated remaining step.

Avoid indefinite loading indicators.

---

# Animations

Fast.

Subtle.

Functional.

Never decorative.

---

# Responsiveness

Desktop First.

Tablet Supported.

Mobile

Read-only.

Analysis should not run on mobile.

---

# Accessibility

Keyboard navigation.

High contrast support.

Screen reader labels.

Color independent indicators.

---

# Icons

Lucide

or

Heroicons

No emoji.

No decorative icons.

---

# UI Components

Buttons

Inputs

Dropdowns

Calendars

Layer Tree

Timeline

Cards

Charts

Dialogs

Tables

Tooltips

Notifications

Progress

Everything should be reusable.

---

# Overall User Feeling

The application should feel like

"I am using professional GIS software."

NOT

"I am browsing a website."

---

# Acceptance Criteria

✓ Map is always primary.

✓ Clean engineering aesthetic.

✓ No cyberpunk design.

✓ No startup landing page.

✓ Minimal clicks.

✓ Professional GIS workflow.

✓ Responsive.

✓ Accessible.

✓ Consistent.

✓ Production quality.