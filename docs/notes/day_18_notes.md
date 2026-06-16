# Day 18 Notes

## Date

June 18, 2026

---

# Neural Network Training Fundamentals

Today focused on understanding how neural networks learn.

---

# 1. Forward Pass

The model receives input data and produces predictions.

Input
↓
Model
↓
Prediction

---

# 2. Loss Function

Measures prediction error.

Lower loss means better predictions.

---

# Example

Prediction = 5

Actual = 8

Loss > 0

---

# 3. Backpropagation

Backpropagation computes gradients.

These gradients indicate how model parameters should change.

---

# 4. Optimizer

Uses gradients to update model weights.

---

# Example

SGD

Adam

AdamW

---

# 5. Learning Rate

Controls update size.

---

# High Learning Rate

Fast but unstable.

---

# Low Learning Rate

Stable but slow.

---

# 6. Epoch

One complete pass through the dataset.

---

# Example

100 Epochs

Dataset processed 100 times.

---

# 7. Training Loop

Input
↓
Prediction
↓
Loss
↓
Backpropagation
↓
Optimizer Step
↓
Repeat

---

# 8. GeoSentinel Connection

Future Training Pipeline

Satellite Patch
↓
Segmentation Model
↓
Prediction Mask
↓
Loss Function
↓
Backpropagation
↓
Weight Update

---

# Key Learnings

- Neural networks learn by minimizing loss.
- Backpropagation computes gradients.
- Optimizers update model weights.
- Learning rate controls update magnitude.
- Epochs represent repeated training cycles.
