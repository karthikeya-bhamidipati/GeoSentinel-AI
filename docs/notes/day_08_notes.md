# Day 08 Notes

## Date

June 8, 2026

---

# Spectral Indices for Urban and Vegetation Analysis

Today focused on extending vegetation analysis and introducing built-up area detection using spectral indices.

---

# 1. NDVI

## Definition

Normalized Difference Vegetation Index.

Formula:

NDVI = (NIR - Red) / (NIR + Red)

Bands:

- B08 (NIR)
- B04 (Red)

Purpose:

Vegetation monitoring.

---

# 2. EVI

## Definition

Enhanced Vegetation Index.

Formula:

EVI = 2.5 × (NIR - Red)
      /
      (NIR + 6×Red - 7.5×Blue + 1)

Bands:

- B08
- B04
- B02

---

## Advantages

- Better performance in dense vegetation
- Reduces atmospheric influence
- Improves vegetation discrimination

---

# 3. NDBI

## Definition

Normalized Difference Built-up Index.

Formula:

NDBI = (SWIR - NIR)
       /
       (SWIR + NIR)

Bands:

- B11 (SWIR)
- B08 (NIR)

Purpose:

Built-up area detection.

---

# 4. Resolution Differences

## B08

10m Resolution

---

## B11

20m Resolution

---

## Challenge

Different resolutions prevent direct pixel-wise calculations.

---

## Solution

Resampling

B11 was resampled to match B08 dimensions.

---

# 5. Resampling

## Definition

Process of changing raster resolution.

---

## Why Needed

To align multiple bands before analysis.

---

## Method Used

Bilinear Interpolation

---

# 6. Urban Spectral Behavior

Urban surfaces typically show:

- Lower NDVI
- Higher NDBI

---

# 7. Vegetation Spectral Behavior

Vegetation typically shows:

- High NDVI
- High EVI
- Low NDBI

---

# 8. NDVI vs EVI

| Feature | NDVI | EVI |
|----------|----------|----------|
| Vegetation Detection | Good | Better |
| Dense Vegetation | Moderate | Strong |
| Atmospheric Resistance | Moderate | Better |

---

# 9. NDVI vs NDBI

NDVI:

Vegetation Detection

NDBI:

Built-up Area Detection

---

# 10. GeoSentinel Connection

NDVI
↓
Vegetation

NDBI
↓
Built-up Areas

Compare Over Time
↓
Urban Expansion Detection

---

# Key Learnings

- Multiple indices provide richer information.
- EVI improves vegetation analysis.
- NDBI enables urban detection.
- Resampling is essential in multispectral workflows.
- Urban expansion and vegetation loss are closely related.

---

# Questions For Future Exploration

- Can NDVI and NDBI be combined?
- How will temporal analysis use these indices?
- How can deep learning improve built-up detection?
