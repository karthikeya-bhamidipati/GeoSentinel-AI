# Day 01 Notes

## Date

June 1, 2026

---

# Focus of the Day

Project initialization, architecture planning, environment setup, documentation, repository organization, and research foundation.

---

# Major Decisions Made

## Project Scope

GeoSentinel AI will focus exclusively on:

- Urban Expansion Detection
- Vegetation Loss Detection

using:

- Sentinel-2 Satellite Imagery
- Geospatial Analytics
- Computer Vision
- Deep Learning
- RAG
- Agent Workflows
- Automation Pipelines

No additional use cases will be added unless they are explicitly moved from Future Scope after MVP completion.

---

## Study Region

Selected Region:

Hyderabad, Telangana, India

Reasons:

- Rapid urban growth
- Strong satellite imagery availability
- Clear land-use changes
- Good demonstration potential

---

## Technology Stack

### Geospatial

- Rasterio
- GeoPandas
- GDAL
- QGIS

### Computer Vision

- OpenCV

### Deep Learning

- PyTorch

### Backend

- FastAPI

### Frontend

- React
- Leaflet

### AI Systems

- LangChain
- LangGraph
- ChromaDB

### Automation

- Prefect

### Deployment

- Docker

---

# Architecture Direction

Planned pipeline:

Satellite Imagery
↓
TorchGeo Data Pipeline
↓
Preprocessing
↓
NDVI Analysis
↓
Change Detection
↓
Urban Expansion Detection
↓
Vegetation Loss Detection
↓
Risk Analysis
↓
Report Generation
↓
RAG Query System
↓
Dashboard

---

# Research Findings

The following papers were identified as highly relevant:

## Strong Candidates

- TorchGeo (Stewart et al.)
- FC-Siam-Diff (Daudt et al.)
- OSCD Dataset

## Advanced Candidates

- BIT-CD (Chen et al.)
- ChangeFormer (Bandara & Patel)

## Literature Review References

- SNUNet-CD
- ScratchFormer
- SILI-CD
- TTP
- BiFA
- Amazon Deforestation FCNs

---

# Key Learnings

- Importance of project planning before implementation.
- Importance of scope control.
- Importance of version control from Day 1.
- Importance of maintaining research documentation.
- Difference between project ideas and project requirements.
- Research papers should guide implementation decisions, not dictate them.

---

# Questions To Explore Later

- Can TorchGeo simplify Sentinel-2 ingestion?
- Is FC-Siam-Diff sufficient for our use case?
- Is BIT-CD a practical advanced comparison model?
- How should NDVI and deep learning outputs be combined?

---

# Project Health

Architecture: Stable

Scope: Locked

Research Direction: Established

Repository Status: Healthy

Technical Debt: None

Risk Level: Low

---

# Day 01 Outcome

Day 01 completed successfully.

The project is fully initialized and ready for geospatial foundations in Day 02.
