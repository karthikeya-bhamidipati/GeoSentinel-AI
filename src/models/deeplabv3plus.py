"""
===============================================================================
GeoSentinel AI

Module:
    deeplabv3plus.py

Description:
    DeepLabV3+ segmentation model for land cover classification.

    Uses atrous spatial pyramid pooling (ASPP) and a ResNet50 encoder.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import torch
import torch.nn as nn

from src.models.unet import DEFAULT_IN_CHANNELS, NUM_CLASSES, SMP_AVAILABLE

if SMP_AVAILABLE:
    import segmentation_models_pytorch as smp


class GeoSentinelDeepLabV3Plus(nn.Module):
    """
    DeepLabV3+ land cover segmentation model.

    Comparison model used to benchmark against U-Net.
    Uses atrous spatial pyramid pooling (ASPP) and a ResNet50 encoder.

    Reference:
    Chen et al. (2018). Encoder-Decoder with Atrous Separable Convolution
    for Semantic Image Segmentation. ECCV 2018.
    """

    def __init__(
        self,
        in_channels: int = DEFAULT_IN_CHANNELS,
        num_classes: int = NUM_CLASSES,
        encoder_name: str = "resnet50",
        encoder_weights: str | None = "imagenet",
    ) -> None:

        super().__init__()

        if not SMP_AVAILABLE:
            raise ImportError(
                "segmentation_models_pytorch is required."
            )

        self.in_channels = in_channels
        self.num_classes = num_classes
        self.encoder_name = encoder_name

        self.model = smp.DeepLabV3Plus(
            encoder_name=encoder_name,
            encoder_weights=encoder_weights,
            in_channels=in_channels,
            classes=num_classes,
            activation=None,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def predict(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return torch.argmax(self.forward(x), dim=1)

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return torch.softmax(self.forward(x), dim=1)

    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def __repr__(self) -> str:
        return (
            f"GeoSentinelDeepLabV3Plus("
            f"encoder={self.encoder_name}, "
            f"in={self.in_channels}, "
            f"classes={self.num_classes}, "
            f"params={self.parameter_count():,})"
        )
