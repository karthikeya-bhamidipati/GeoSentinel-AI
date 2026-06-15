# Day 12 – Sentinel-2 Visualization & Band Combinations

Date: June 12, 2026

## Objective

Learn how to visualize Sentinel-2 imagery using different band combinations.

## Key Band Combinations

### RGB Composite

R = B4

G = B3

B = B2

Purpose:

- Natural color visualization

### False Color Composite

R = B8

G = B4

B = B3

Purpose:

- Vegetation analysis

Vegetation appears bright red.

### Urban Composite

R = B12

G = B11

B = B4

Purpose:

- Urban monitoring
- Built-up area identification

## Important Bands

B2 → Blue

B3 → Green

B4 → Red

B8 → Near Infrared

B11 → SWIR

B12 → SWIR

## Observations

Vegetation reflects NIR strongly.

Urban areas reflect SWIR strongly.

False Color imagery highlights vegetation.

Urban composites highlight built-up regions.

## GeoSentinel AI Relevance

These visualizations will be used to:

- Understand training data
- Detect vegetation loss
- Identify urban expansion

## Deliverables

- rgb_composite.png
- false_color_composite.png
- urban_composite.png
- band_statistics.csv

## Outcome

Successfully visualized Sentinel-2 imagery using multiple band combinations.
