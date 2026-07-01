"""
===============================================================================
GeoSentinel AI

Module:
    unet.py

Description:
    U-Net segmentation model for land cover classification.

    Primary model for the GeoSentinel AI platform.

    Architecture:
    - Encoder: ResNet34 (ImageNet pretrained, first conv adapted to N channels)
    - Decoder: Standard U-Net skip connections with transpose convolution
    - Output: Softmax over 6 land cover classes

    Land Cover Classes:
    0 = Background / No Data
    1 = Urban / Built-up
    2 = Vegetation
    3 = Water
    4 = Bare Soil / Barren
    5 = Agriculture

    Reference:
    Ronneberger, O., Fischer, P., & Brox, T. (2015). U-Net: Convolutional
    Networks for Biomedical Image Segmentation. MICCAI 2015.

    Implemented using segmentation_models_pytorch:
    https://github.com/qubvel/segmentation_models.pytorch

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from enum import IntEnum

import torch
import torch.nn as nn

try:
    import segmentation_models_pytorch as smp
    SMP_AVAILABLE = True
except ImportError:
    SMP_AVAILABLE = False


# =============================================================================
# Land Cover Classes
# =============================================================================


class LandCoverClass(IntEnum):
    """
    Land cover class definitions for GeoSentinel AI segmentation.
    """

    BACKGROUND = 0
    URBAN = 1
    VEGETATION = 2
    WATER = 3
    BARREN = 4
    AGRICULTURE = 5


LAND_COVER_NAMES: dict[int, str] = {
    LandCoverClass.BACKGROUND: "Background",
    LandCoverClass.URBAN: "Urban",
    LandCoverClass.VEGETATION: "Vegetation",
    LandCoverClass.WATER: "Water",
    LandCoverClass.BARREN: "Barren",
    LandCoverClass.AGRICULTURE: "Agriculture",
}

LAND_COVER_COLORS: dict[int, tuple[int, int, int]] = {
    LandCoverClass.BACKGROUND: (0, 0, 0),
    LandCoverClass.URBAN: (220, 20, 60),
    LandCoverClass.VEGETATION: (34, 139, 34),
    LandCoverClass.WATER: (30, 144, 255),
    LandCoverClass.BARREN: (210, 180, 140),
    LandCoverClass.AGRICULTURE: (255, 215, 0),
}

NUM_CLASSES = len(LandCoverClass)
DEFAULT_IN_CHANNELS = 12  # 5 bands + 7 indices


# =============================================================================
# U-Net with SMP
# =============================================================================


class GeoSentinelUNet(nn.Module):
    """
    U-Net land cover segmentation model.

    Uses segmentation_models_pytorch with a ResNet34 encoder.
    The first convolutional layer is adapted from the standard 3-channel
    input to accept the full 12-channel feature stack.

    Parameters
    ----------
    in_channels : int
        Number of input channels (default: 12).
    num_classes : int
        Number of output classes (default: 6).
    encoder_name : str
        SMP encoder backbone (default: 'resnet34').
    encoder_weights : str | None
        Pretrained weights (default: 'imagenet').
        Set to None to train from scratch.
    """

    def __init__(
        self,
        in_channels: int = DEFAULT_IN_CHANNELS,
        num_classes: int = NUM_CLASSES,
        encoder_name: str = "resnet34",
        encoder_weights: str | None = "imagenet",
    ) -> None:

        super().__init__()

        if not SMP_AVAILABLE:
            raise ImportError(
                "segmentation_models_pytorch is required. "
                "Install with: pip install segmentation-models-pytorch"
            )

        self.in_channels = in_channels
        self.num_classes = num_classes
        self.encoder_name = encoder_name

        self.model = smp.Unet(
            encoder_name=encoder_name,
            encoder_weights=encoder_weights,
            in_channels=in_channels,
            classes=num_classes,
            activation=None,  # raw logits — loss handles activation
        )

    # ------------------------------------------------------------------

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Parameters
        ----------
        x : torch.Tensor
            Shape (batch, in_channels, height, width).

        Returns
        -------
        torch.Tensor
            Logits of shape (batch, num_classes, height, width).
        """

        return self.model(x)

    # ------------------------------------------------------------------

    def predict(self, x: torch.Tensor) -> torch.Tensor:
        """
        Run inference and return class predictions.

        Parameters
        ----------
        x : torch.Tensor
            Shape (batch, in_channels, height, width).

        Returns
        -------
        torch.Tensor
            Predicted class indices (batch, height, width).
        """

        with torch.no_grad():
            logits = self.forward(x)
            return torch.argmax(logits, dim=1)

    # ------------------------------------------------------------------

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """
        Run inference and return class probabilities.

        Parameters
        ----------
        x : torch.Tensor

        Returns
        -------
        torch.Tensor
            Probabilities (batch, num_classes, height, width).
        """

        with torch.no_grad():
            logits = self.forward(x)
            return torch.softmax(logits, dim=1)

    # ------------------------------------------------------------------

    def parameter_count(self) -> int:
        """Return total number of trainable parameters."""

        return sum(
            p.numel()
            for p in self.parameters()
            if p.requires_grad
        )

    # ------------------------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"GeoSentinelUNet("
            f"encoder={self.encoder_name}, "
            f"in={self.in_channels}, "
            f"classes={self.num_classes}, "
            f"params={self.parameter_count():,})"
        )


# =============================================================================
# DeepLabV3+ (comparison model)
# =============================================================================


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
