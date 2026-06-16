# Day 17 Notes

## Date

June 17, 2026

---

# Segmentation Metrics

Today focused on evaluating segmentation models.

---

# 1. Confusion Matrix

Four possible outcomes:

TP = True Positive

TN = True Negative

FP = False Positive

FN = False Negative

---

# 2. Accuracy

Formula:

(TP + TN)
/
(TP + TN + FP + FN)

---

Limitation:

Can be misleading for imbalanced datasets.

---

# 3. Precision

Formula:

TP
/
(TP + FP)

---

Measures:

How many predicted positives are correct.

---

# 4. Recall

Formula:

TP
/
(TP + FN)

---

Measures:

How many actual positives were found.

---

# 5. F1 Score

Formula:

2 × Precision × Recall
/
(Precision + Recall)

---

Balances precision and recall.

---

# 6. IoU

Intersection over Union

Formula:

TP
/
(TP + FP + FN)

---

Most important segmentation metric.

---

# 7. Dice Score

Formula:

2TP
/
(2TP + FP + FN)

---

Commonly used in segmentation tasks.

---

# 8. GeoSentinel Connection

Future evaluation:

Vegetation Masks
↓
IoU

Urban Masks
↓
IoU

Change Maps
↓
IoU

---

# Key Learnings

- Accuracy alone is insufficient.
- Precision measures correctness.
- Recall measures completeness.
- F1 balances precision and recall.
- IoU is the primary segmentation metric.
- Dice Score is closely related to IoU.
