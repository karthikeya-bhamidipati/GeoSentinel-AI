// Generated from outputs/oscd/summary.json (full-scene OSCD evaluation, tau = 0.5). Do not edit by hand.
export const CHANGE_RESULTS = [
  { model: "Proposed (land-cover anchor + linear attention)", oa: { mean: 96.12, sd: 0.23 }, precision: { mean: 66.55, sd: 4.01 }, recall: { mean: 50.58, sd: 3.54 }, f1: { mean: 57.36, sd: 2.24 }, iou: { mean: 40.23, sd: 2.21 }, params: "64.1M" },
  { model: "Baseline (ImageNet-initialised ResNet-50 branch)", oa: { mean: 95.5, sd: 0.18 }, precision: { mean: 58.47, sd: 4.09 }, recall: { mean: 48.16, sd: 8.06 }, f1: { mean: 52.33, sd: 3.26 }, iou: { mean: 35.48, sd: 2.97 }, params: "64.1M" },
];

// Land-cover anchor per-class validation metrics as reported in the manuscript (Table 1).
export const LAND_COVER = [
  { cls: "Water bodies", precision: 96.29, recall: 96.94, f1: 96.61, iou: 93.45 },
  { cls: "Urban / built-up", precision: 90.05, recall: 92.45, f1: 91.23, iou: 83.89 },
  { cls: "Vegetation", precision: 77.47, recall: 81.88, f1: 79.61, iou: 66.13 },
  { cls: "Barren / bare soil", precision: 68.3, recall: 70.1, f1: 69.19, iou: 52.88 },
  { cls: "Background / no data", precision: 92.5, recall: 91.1, f1: 91.79, iou: 84.83 },
  { cls: "Macro-average", precision: 84.92, recall: 86.49, f1: 85.69, iou: 76.24 },
];

export const PROTOCOL = {
  seeds: 3,
  items: [
    { label: "Dataset", value: "OSCD: 11 training cities, 3 held-out validation cities (Beirut, Bordeaux, Cupertino), 10 test cities" },
    { label: "Input", value: "12 channels: B02, B03, B04, B08, B11 + NDVI, NDBI, NDWI, SAVI, EVI, MNDWI, BSI" },
    { label: "Training crops", value: "256 × 256 px, flips and 90° rotations, 50 crops per city per epoch" },
    { label: "Optimiser", value: "AdamW, lr 1e-4 (1e-5 encoders), weight decay 1e-4, batch size 4" },
    { label: "Loss", value: "Focal Tversky (α 0.3, β 0.7, γ 4/3), class weights [0.15, 0.85]" },
    { label: "Model selection", value: "Lowest validation loss on held-out cities; early stopping after 20 epochs" },
    { label: "Evaluation", value: "Full test scenes, 256 px sliding window (stride 128), pooled confusion matrix" },
    { label: "Seeds", value: "3 per configuration; mean ± standard deviation reported" },
  ],
};
