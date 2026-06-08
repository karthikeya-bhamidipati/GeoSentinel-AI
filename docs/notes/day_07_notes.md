# Day 07 Notes

## Date

June 7, 2026

---

# Spectral Analysis and Remote Sensing Interpretation

Today focused on understanding how different Sentinel-2 bands represent the Earth's surface and why multispectral imagery provides more information than traditional RGB imagery.

---

# 1. True Color (RGB) Imagery

## Definition

True Color imagery attempts to reproduce how the human eye sees the Earth.

Band Composition:

* Red = B04
* Green = B03
* Blue = B02

---

## Characteristics

Advantages:

* Natural appearance
* Easy interpretation
* Familiar to humans

Limitations:

* Limited analytical information
* Cannot reveal hidden spectral patterns

---

## GeoSentinel Usage

Used for:

* Visualization
* Reporting
* User-friendly displays

---

# 2. False Color Imagery

## Definition

False Color imagery maps spectral bands to different display channels.

Composition:

* Red Channel = B08 (NIR)
* Green Channel = B04 (Red)
* Blue Channel = B03 (Green)

---

## Characteristics

Vegetation appears bright red.

Reason:

Healthy vegetation reflects Near Infrared strongly.

---

## Advantages

* Highlights vegetation clearly
* Reveals information invisible to humans
* Useful for environmental monitoring

---

## GeoSentinel Usage

Used for:

* Vegetation analysis
* Visual validation
* Environmental interpretation

---

# 3. Near Infrared (NIR)

## Sentinel-2 Band

B08

Resolution:

10m

---

## Importance

Near Infrared is one of the most important bands in remote sensing.

Healthy vegetation reflects NIR strongly.

---

## Observation

Bright Areas:

* Dense vegetation
* Healthy vegetation

Dark Areas:

* Water
* Urban surfaces

---

# 4. Spectral Signatures

## Definition

A spectral signature is the unique reflectance pattern of a material across different wavelengths.

Different materials reflect energy differently.

---

## Examples

### Vegetation

Red:

Low

NIR:

High

NDVI:

High

---

### Water

Red:

Low

NIR:

Very Low

NDVI:

Negative

---

### Urban Areas

Red:

Moderate

NIR:

Moderate

NDVI:

Low

---

## Importance

Spectral signatures enable automated classification and remote sensing analysis.

---

# 5. Material Interpretation Table

| Material    | Red Reflectance | NIR Reflectance | NDVI            |
| ----------- | --------------- | --------------- | --------------- |
| Vegetation  | Low             | High            | High            |
| Water       | Low             | Very Low        | Negative        |
| Urban Areas | Moderate        | Moderate        | Low             |
| Bare Soil   | Moderate        | Moderate        | Low to Moderate |

---

# 6. RGB vs False Color vs NDVI

## RGB

Best For:

Human interpretation

Advantages:

Natural appearance

Limitations:

Limited analytical value

---

## False Color

Best For:

Vegetation identification

Advantages:

Highlights vegetation clearly

Limitations:

Requires remote sensing understanding

---

## NDVI

Best For:

Vegetation analysis

Advantages:

Quantitative measurement

Limitations:

Only focuses on vegetation

---

# Comparison Summary

RGB
↓
Human Vision

False Color
↓
Enhanced Vegetation Visibility

NDVI
↓
Vegetation Intelligence

---

# 7. Why Multispectral Imagery Matters

A normal camera captures:

* Blue
* Green
* Red

---

A Sentinel-2 satellite captures:

* Blue
* Green
* Red
* Near Infrared
* Short Wave Infrared
* Atmospheric Bands

---

This allows satellites to detect:

* Vegetation health
* Moisture
* Land cover
* Environmental changes

that are invisible to human vision.

---

# 8. GeoSentinel Connection

Current understanding:

Sentinel-2
↓
Multiple Spectral Bands
↓
Spectral Analysis
↓
NDVI
↓
Vegetation Monitoring
↓
Change Detection
↓
Risk Analysis

---

# Key Learnings

* Satellites observe more than visible light.
* NIR is critical for vegetation monitoring.
* Spectral signatures enable land cover analysis.
* False Color imagery reveals information hidden from RGB imagery.
* NDVI is built upon spectral differences.
* Remote sensing combines imagery and spectral science.

---

# Questions For Future Exploration

* How do SWIR bands contribute to analysis?
* How are spectral signatures used in deep learning?
* How can multiple indices be combined?
* How do change detection models use multispectral imagery?
