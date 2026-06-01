# GeoSentinel AI Research Library

This document contains research papers, datasets, frameworks, and technical references relevant to the GeoSentinel AI project.

---

# Paper Evaluation Status

Legend:

- 🔴 Not Reviewed
- 🟡 Under Review
- 🟢 Reviewed
- ⭐ Selected for Project
- 📚 Literature Review Only

---

## 1. TorchGeo: Deep Learning With Geospatial Data

Status: ⭐ Selected for Project

Authors:

- Stewart et al.

Domain:

- Geospatial Deep Learning
- Remote Sensing

Problem Solved:

- Handling geospatial imagery in machine learning pipelines
- Coordinate Reference Systems (CRS)
- Multi-spectral imagery
- Geospatial sampling

Key Contributions:

- Geospatial datasets
- Geospatial samplers
- Sentinel-2 support
- Multi-band processing

Potential Use In GeoSentinel:

- Satellite imagery ingestion
- Geospatial preprocessing
- Dataset management

Implementation Difficulty:

- Medium

Project Phase:

- Week 1

---

## 2. Fully Convolutional Siamese Networks for Change Detection

Status: ⭐ Selected for Project

Authors:

- Rodrigo Caye Daudt
- Bertrand Le Saux
- Alexandre Boulch

Domain:

- Change Detection

Architectures:

- FC-EF
- FC-Siam-conc
- FC-Siam-diff

Problem Solved:

- Bitemporal satellite image change detection

Key Contributions:

- Lightweight change detection models
- Shared-weight Siamese architecture

Potential Use In GeoSentinel:

- Baseline model

Implementation Difficulty:

- Medium

Project Phase:

- Week 2

---

## 3. SNUNet-CD

Status: 📚 Literature Review

Authors:

- Fang et al.

Domain:

- Change Detection

Problem Solved:

- Fine-grained localization of changes

Key Contributions:

- Dense skip connections
- Attention mechanisms

Potential Use In GeoSentinel:

- Advanced comparison model

Implementation Difficulty:

- High

Project Phase:

- Week 3

---

## 4. ChangeFormer

Status: 🟡 Candidate

Authors:

- Bandara & Patel

Domain:

- Transformer Change Detection

Problem Solved:

- Long-range spatial-temporal reasoning

Key Contributions:

- Siamese Vision Transformer
- Transformer-based change detection

Potential Use In GeoSentinel:

- Advanced model comparison

Implementation Difficulty:

- High

Project Phase:

- Week 3

---

## 5. BIT-CD

Status: 🟡 Candidate

Authors:

- Chen et al.

Domain:

- Hybrid CNN + Transformer

Problem Solved:

- Computationally efficient transformer change detection

Key Contributions:

- Semantic tokens
- Lightweight transformer architecture

Potential Use In GeoSentinel:

- Advanced comparison model

Implementation Difficulty:

- Medium

Project Phase:

- Week 3

---

## 6. ScratchFormer

Status: 📚 Literature Review

Authors:

- Noman et al.

Domain:

- Transformer Change Detection

Problem Solved:

- Training transformers from scratch

Key Contributions:

- CEFF module
- Domain-specific learning

Potential Use:

- Research understanding

Implementation:

- Not planned

---

## 7. SILI-CD

Status: 📚 Literature Review

Authors:

- Chen et al.

Domain:

- Cross-Resolution Change Detection

Problem Solved:

- Comparing imagery with different resolutions

Potential Use:

- Research understanding

Implementation:

- Not planned

---

## 8. TTP (Time Travelling Pixels)

Status: 📚 Literature Review

Domain:

- Foundation Models

Problem Solved:

- Integrating foundation models into change detection

Potential Use:

- Future project extension

Implementation:

- Not planned

---

## 9. BiFA

Status: 📚 Literature Review

Authors:

- Zhang et al.

Domain:

- Feature Alignment

Problem Solved:

- Registration errors
- Misaligned satellite imagery

Potential Use:

- Understanding preprocessing challenges

Implementation:

- Not planned

---

## 10. Deforestation Detection with Fully Convolutional Networks in the Amazon Forest

Status: 📚 Literature Review

Authors:

- Torres et al.

Domain:

- Vegetation Monitoring

Problem Solved:

- Deforestation segmentation

Potential Use:

- Vegetation loss analysis

Implementation:

- Conceptual reference

---

## Datasets

---

## OSCD Dataset

Status: ⭐ Selected

Paper:

- Onera Satellite Change Detection Dataset

Use:

- Baseline urban change detection

Priority:

- High

---

## S2Looking Dataset

Status: 🟡 Candidate

Use:

- Robustness evaluation

Priority:

- Medium

---

## Future Papers To Explore

(To be filled throughout project)

- TBD

---

## Notes

As the project evolves:

- Add new papers
- Update implementation status
- Record architecture decisions
- Track model comparisons
- Record dataset evaluations
