"""
===============================================================================
GeoSentinel AI — Test Suite: U-Net Model and ModelFactory
===============================================================================
Tests the model forward pass, factory, and metrics with synthetic tensors.
Uses CPU-only; no GPU required.
"""

from __future__ import annotations

import pytest
import numpy as np


# ---------------------------------------------------------------------------
# LandCoverClass enum
# ---------------------------------------------------------------------------

class TestLandCoverClass:

    def test_values_are_defined(self):
        from src.models.unet import LandCoverClass
        assert LandCoverClass.BACKGROUND == 0
        assert LandCoverClass.URBAN == 1
        assert LandCoverClass.VEGETATION == 2
        assert LandCoverClass.WATER == 3
        assert LandCoverClass.BARREN == 4

    def test_count_is_5(self):
        from src.models.unet import LandCoverClass
        assert len(list(LandCoverClass)) == 5


# ---------------------------------------------------------------------------
# ModelFactory
# ---------------------------------------------------------------------------

class TestModelFactory:

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("segmentation_models_pytorch"),
        reason="segmentation_models_pytorch not installed"
    )
    def test_create_unet(self):
        """Factory should create a UNet model."""
        from src.models.model_factory import ModelFactory
        from src.models.unet import DEFAULT_IN_CHANNELS, NUM_CLASSES

        factory = ModelFactory()
        model = factory.create_model(
            model_type="unet",
            in_channels=DEFAULT_IN_CHANNELS,
            num_classes=NUM_CLASSES,
            encoder_weights=None,
        )
        assert model is not None

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("segmentation_models_pytorch"),
        reason="segmentation_models_pytorch not installed"
    )
    def test_create_deeplabv3plus(self):
        from src.models.model_factory import ModelFactory
        from src.models.unet import DEFAULT_IN_CHANNELS, NUM_CLASSES

        factory = ModelFactory()
        model = factory.create_model(
            model_type="deeplabv3plus",
            in_channels=DEFAULT_IN_CHANNELS,
            num_classes=NUM_CLASSES,
            encoder_weights=None,
        )
        assert model is not None

    def test_invalid_model_type_raises(self):
        from src.models.model_factory import ModelFactory

        factory = ModelFactory()
        with pytest.raises((ValueError, KeyError, Exception)):
            factory.create_model(
                model_type="unknown_model",
                in_channels=12,
                num_classes=6,
                encoder_weights=None,
            )


# ---------------------------------------------------------------------------
# Segmentation Metrics
# ---------------------------------------------------------------------------

class TestSegmentationMetrics:

    def test_perfect_prediction_iou_is_1(self):
        """Identical predictions and labels should yield IoU = 1.0."""
        import torch
        from src.training.metrics import SegmentationMetricCalculator

        calc = SegmentationMetricCalculator(num_classes=6)
        labels = torch.randint(0, 6, (16, 64, 64))
        preds = labels.clone()  # Perfect prediction

        metrics = calc.compute(predictions=preds, targets=labels)
        assert abs(metrics.iou - 1.0) < 0.01

    def test_metrics_values_in_01(self):
        """All metric values must be in [0, 1]."""
        import torch
        from src.training.metrics import SegmentationMetricCalculator

        calc = SegmentationMetricCalculator(num_classes=6)
        labels = torch.randint(0, 6, (4, 32, 32))
        preds = torch.randint(0, 6, (4, 32, 32))

        metrics = calc.compute(predictions=preds, targets=labels)
        for attr in ["iou", "dice", "precision", "recall", "f1", "accuracy"]:
            value = getattr(metrics, attr)
            assert 0.0 <= value <= 1.0, f"{attr} = {value} is out of [0, 1]"

    def test_metrics_shape_consistency(self):
        """per_class_iou should have one entry per class."""
        import torch
        from src.training.metrics import SegmentationMetricCalculator

        calc = SegmentationMetricCalculator(num_classes=6)
        labels = torch.randint(0, 6, (2, 64, 64))
        preds = torch.randint(0, 6, (2, 64, 64))

        metrics = calc.compute(predictions=preds, targets=labels)
        assert len(metrics.per_class_iou) == 6
