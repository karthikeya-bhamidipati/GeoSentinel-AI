# Day 19 Notes

## Date

June 19, 2026

---

# Segmentation Architectures

Today focused on the most important segmentation architectures used in computer vision and remote sensing.

---

# 1. FCN

Fully Convolutional Network.

---

## Importance

First major segmentation architecture.

Introduced pixel-wise prediction.

---

# 2. U-Net

Most widely used segmentation architecture.

---

## Structure

Encoder

↓

Bottleneck

↓

Decoder

---

## Key Feature

Skip Connections

---

## Advantages

- Preserves spatial information
- Works with small datasets
- Easy to train
- Popular in remote sensing

---

# 3. Skip Connections

Transfer feature maps directly from encoder to decoder.

---

## Benefit

Recover lost spatial information.

Improve segmentation accuracy.

---

# 4. DeepLabV3

State-of-the-art segmentation architecture.

---

## Key Feature

Atrous Convolution

---

## Advantages

- Large receptive field
- Multi-scale context
- Strong segmentation performance

---

# 5. Atrous Convolution

Introduces gaps between kernel elements.

Allows larger context without increasing parameters.

---

# 6. Architecture Comparison

FCN

Baseline

---

U-Net

Most Popular

---

DeepLabV3

Most Accurate

---

# 7. GeoSentinel Plan

Phase 1

U-Net

---

Phase 2

DeepLabV3

---

Evaluation

IoU

Dice Score

Inference Speed

---

# Key Learnings

- Segmentation requires specialized architectures.
- U-Net remains the most practical architecture.
- DeepLabV3 provides state-of-the-art performance.
- Skip connections are essential.
- Atrous convolution improves context capture.
