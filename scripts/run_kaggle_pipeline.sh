#!/bin/bash
# ==============================================================================
# GeoSentinel AI - End-to-End Kaggle Training & Evaluation Pipeline
# ==============================================================================
# This script executes the three-phase methodology required for the thesis:
# 1. Semantic Anchor Pre-training (DeepLabV3+ with early stopping)
# 2. Elite Model Training (Semantic Anchor + U-Net)
# 3. Baseline Model Training (ImageNet + U-Net)
# 4. Comparative Evaluation

set -e

echo "======================================================================"
echo " Starting GeoSentinel-AI End-to-End Pipeline"
echo "======================================================================"

# Ensure output directory exists for metrics
mkdir -p outputs
mkdir -p data/weights

echo ""
echo ">>> PHASE 1: Semantic Anchor Pre-training (DeepLabV3+)"
echo "----------------------------------------------------------------------"
python scripts/train.py --model deeplabv3plus --epochs 100 --batch-size 8 --num-workers 4
echo "Phase 1 Complete. DeepLab weights saved to data/weights/deeplabv3plus_best.pt"

echo ""
echo ">>> PHASE 2: Elite Model Training (Semantic Anchor + U-Net)"
echo "----------------------------------------------------------------------"
python scripts/train_change.py --epochs 100 --batch-size 4 --num-workers 4
echo "Phase 2 Complete. Elite model weights saved to data/weights/change_unet_best.pt"

echo ""
echo ">>> PHASE 3: Baseline Model Training (ImageNet + U-Net Ablation)"
echo "----------------------------------------------------------------------"
python scripts/train_change.py --epochs 100 --batch-size 4 --num-workers 4 --ablation
echo "Phase 3 Complete. Baseline weights saved to data/weights/change_unet_baseline_best.pt"

echo ""
echo ">>> PHASE 4: Comparative Evaluation"
echo "----------------------------------------------------------------------"
echo "Evaluating Elite Model..."
python scripts/evaluate_change.py --weights data/weights/change_unet_best.pt --batch-size 1 > outputs/elite_final_metrics.txt

echo "Evaluating Baseline Model..."
python scripts/evaluate_change.py --weights data/weights/change_unet_baseline_best.pt --ablation --batch-size 1 > outputs/baseline_final_metrics.txt

echo "======================================================================"
echo " Pipeline Complete!"
echo " Results have been saved to:"
echo " - outputs/elite_final_metrics.txt"
echo " - outputs/baseline_final_metrics.txt"
echo "======================================================================"
