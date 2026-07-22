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

        from src.models.attention import SpectralAttentionGate
        self.scag = SpectralAttentionGate(in_channels=in_channels, reduction_ratio=4)

        self.model = smp.DeepLabV3Plus(
            encoder_name=encoder_name,
            encoder_weights=encoder_weights,
            in_channels=in_channels,
            classes=num_classes,
            activation=None,
        )

        # Smart multi-spectral initialization (if imagenet weights were loaded)
        if encoder_weights == "imagenet" and in_channels != 3:
            self._initialize_multispectral_weights()

    def _initialize_multispectral_weights(self):
        """
        Carefully initializes the first convolution layer to handle 12 channels
        by replicating the mean of the pre-trained 3-channel RGB weights.
        This preserves edge-detection gradients better than random initialization.
        """
        # Find the first convolution layer (usually in the encoder)
        for name, module in self.model.encoder.named_modules():
            if isinstance(module, nn.Conv2d):
                if module.in_channels == self.in_channels:
                    with torch.no_grad():
                        # The weights are [out_channels, in_channels, H, W]
                        weights = module.weight.data
                        # Assuming SMP initialized the first 3 channels with ImageNet and others randomly
                        # We take the mean of the first 3 channels (RGB)
                        rgb_mean = weights[:, :3, :, :].mean(dim=1, keepdim=True)
                        # Copy the mean to the remaining channels
                        for i in range(3, self.in_channels):
                            weights[:, i:i+1, :, :] = rgb_mean
                    break # Only do this for the very first conv layer

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Apply Spectral-Channel Attention Gating first
        x = self.scag(x)
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
