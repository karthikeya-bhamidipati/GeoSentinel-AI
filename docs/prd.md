# GeoSentinel AI
# Product Requirements Document (PRD)

Version: 1.0

Status: Frozen

Owner: Karthikeya Bhamidipati

Project Type:
Research-grade Geospatial AI Platform

---

# 1. Executive Summary

GeoSentinel AI is a modern geospatial decision-support platform designed for monitoring urban expansion and vegetation dynamics within the Hyderabad Metropolitan Region using Sentinel-2 imagery, Deep Learning, Temporal Analytics, and Explainable Artificial Intelligence.

Unlike conventional GIS workflows that require multiple software packages and significant manual intervention, GeoSentinel AI provides an integrated end-to-end workflow where users simply define an Area of Interest (AOI), choose a temporal range, and receive automated geospatial analytics and professional reports.

The platform is intended to bridge the gap between Earth Observation research and deployable geospatial software.

It should resemble a professional GIS application rather than an academic prototype.

---

# 2. Vision

To build the most complete open-source geospatial monitoring platform for urban expansion and vegetation dynamics using modern AI, Remote Sensing, and Full Stack technologies.

The platform should feel like:

• ArcGIS Pro
• Sentinel Hub EO Browser
• Google Earth Engine
• Planet Explorer

while remaining completely developed from scratch.

---

# 3. Product Goals

The platform shall

✓ Automatically retrieve Sentinel imagery

✓ Never require manual SAFE downloads

✓ Support temporal analysis

✓ Support explainable recommendations

✓ Generate professional reports

✓ Benchmark AI models

✓ Be Docker deployable

✓ Be maintainable

✓ Be modular

✓ Be reproducible

---

# 4. Target Users

Primary

• Researchers

• Urban planners

• Environmental scientists

• Government agencies

• MSc and PhD students

Secondary

• NGOs

• Smart city organizations

• Policy makers

---

# 5. Product Philosophy

GeoSentinel AI is NOT

• a notebook

• a deep learning demo

• a dashboard

• a GIS assignment

GeoSentinel AI IS

• a software platform

• a geospatial decision support system

• a cloud-native Earth Observation platform

• an AI-powered analytics system

---

# 6. Study Area

The entire platform is permanently restricted to

Hyderabad Metropolitan Region (HMR)

with approximately

150 km operational buffer.

The user cannot analyze any location outside this region.

The frontend must never display the entire world.

Only Hyderabad shall be visible.

---

# 7. User Journey

Step 1

User opens the application.

↓

Step 2

Interactive Hyderabad map is displayed.

↓

Step 3

User selects AOI.

↓

Step 4

User selects

Start Date

End Date

Maximum Cloud Cover

Spatial Resolution

↓

Step 5

Clicks

Analyze

↓

Step 6

System validates AOI.

↓

Step 7

System searches CDSE.

↓

Step 8

System selects best available imagery.

↓

Step 9

Only the requested AOI is downloaded.

↓

Step 10

Raster preprocessing.

↓

Step 11

Feature engineering.

↓

Step 12

AI segmentation.

↓

Step 13

Temporal comparison.

↓

Step 14

Spatial analytics.

↓

Step 15

Recommendation engine.

↓

Step 16

Dashboard updates.

↓

Step 17

Professional report generated.

---

# 8. Functional Requirements

## Earth Observation

The platform shall

Search CDSE

Authenticate using OAuth

Download only AOI

Cache imagery

Manage metadata

Support multiple acquisition dates

Support cloud filtering

Support future providers

---

## AI

The platform shall

Run U-Net inference

Support DeepLab benchmarking

Generate prediction masks

Generate confidence maps

Store model checkpoints

Evaluate performance

---

## Temporal

The platform shall

Compare two dates

Compare multiple dates

Generate trend statistics

Generate transition matrices

Generate hotspot maps

Generate urban growth statistics

Generate vegetation loss statistics

---

## Analytics

The platform shall

Calculate area

Calculate percentage change

District summaries

Land cover statistics

Charts

Tables

Graphs

---

## Recommendation Engine

Recommendations must include

Title

Priority

Confidence

Reason

Evidence

Affected Area

Suggested Action

Recommendations must be deterministic.

No LLMs.

No hallucinated advice.

---

## Reporting

Generate

PDF

CSV

GeoJSON

GeoTIFF

Reports shall contain

Executive Summary

AOI Information

Methodology

Maps

Charts

Statistics

Recommendations

Metadata

Appendix

---

# 9. Non Functional Requirements

Performance

The application should process AOIs efficiently using caching and tiled workflows.

Maintainability

Each subsystem should remain independently testable and replaceable.

Reliability

Failures in one subsystem should not corrupt other processing stages.

Scalability

Support future extension to larger study regions without redesigning the architecture.

Reproducibility

The same input parameters should produce identical outputs when data availability is unchanged.

Usability

Users should be able to complete a full analysis in only a few interactions.

---

# 10. Product Modules

The platform consists of the following major subsystems.

1.
Frontend

2.
Backend API

3.
Earth Observation Engine

4.
Preprocessing Engine

5.
Feature Engineering Engine

6.
AI Engine

7.
Benchmarking Engine

8.
Temporal Analytics Engine

9.
Spatial Analytics Engine

10.
Recommendation Engine

11.
Reporting Engine

12.
Docker Deployment

---

# 11. Success Criteria

The project is complete when a user can

✓ Open the platform

✓ Select an AOI

✓ Select dates

✓ Automatically retrieve Sentinel imagery

✓ Run AI segmentation

✓ Perform temporal analysis

✓ View interactive visualizations

✓ Download professional reports

✓ Compare benchmark models

✓ Deploy using Docker

without manual intervention.

---

# 12. Out of Scope

The following are intentionally excluded.

Google Earth Engine

Manual SAFE processing

Global analysis

SAR imagery

Drone imagery

Commercial cloud deployment

Multi-user authentication

Distributed training

---

# 13. Future Expansion

The architecture should support future integration of

ChangeFormer

BIT-CD

ScratchFormer

Additional EO providers

Additional cities

3D visualization

Mobile application

Ward-level analytics

Predictive urban growth modelling

---

# 14. Acceptance Criteria

The product shall be considered production-ready when

• Every subsystem passes unit tests.

• Every API endpoint functions correctly.

• The frontend integrates with the backend.

• Docker deployment succeeds.

• AI benchmarking is complete.

• Reports are generated automatically.

• Recommendations are explainable.

• The complete workflow executes from AOI selection to report generation.

---

# 15. Product Identity

GeoSentinel AI should feel like professional geospatial software.

It must never resemble a student project.

The platform should emphasize clarity, usability, reproducibility, engineering quality, and scientific transparency.

Every design decision should reinforce that identity.