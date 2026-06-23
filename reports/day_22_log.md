# Day 22 Notes

## Date

June 22, 2026

---

# ESA WorldCover Investigation

Today focused on validating ESA WorldCover as the primary label source for GeoSentinel.

---

# Why ESA WorldCover

Advantages:

- Global Coverage
- Free Access
- 10m Resolution
- Compatible with Sentinel-2

---

# ESA WorldCover Classes

10 Tree Cover

20 Shrubland

30 Grassland

40 Cropland

50 Built-up

60 Bare/Sparse Vegetation

70 Snow/Ice

80 Permanent Water

90 Herbaceous Wetland

95 Mangroves

100 Moss/Lichen

---

# GeoSentinel Class Mapping

## Vegetation

WorldCover:

10
20
30
40

↓

GeoSentinel:

1 Vegetation

---

## Urban

WorldCover:

50

↓

GeoSentinel:

2 Urban

---

## Water

WorldCover:

80

↓

GeoSentinel:

3 Water

---

## Background

Remaining Classes

↓

0 Background

---

# Benefits

- Simplifies training
- Reduces class imbalance
- Easier evaluation
- Suitable for Phase 1

---

# Potential Limitations

- WorldCover contains labeling errors
- Temporal mismatch possible
- Urban boundaries may not be perfect

---

# Key Learnings

- WorldCover is suitable for GeoSentinel Phase 1.
- Class aggregation is a common research strategy.
- Sentinel-2 and WorldCover share compatible resolution.
- Proper class mapping is critical for segmentation.
