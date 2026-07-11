"""
===============================================================================
GeoSentinel AI

Module:
    model_factory.py

Description:
    Model factory for creating segmentation models by configuration key.

    Decouples model instantiation from the rest of the platform.
    All model creation should go through this factory.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

from enum import Enum

import torch.nn as nn

from src.models.unet import GeoSentinelUNet
from src.models.deeplabv3plus import GeoSentinelDeepLabV3Plus
from src.models.losses import BCEDiceLoss, DiceLoss, FocalLoss
from src.utils.logger import logger


# =============================================================================
# Model Registry
# =============================================================================


class ModelType(str, Enum):
    """
    Available segmentation model types.
    """

    UNET = "unet"
    DEEPLABV3PLUS = "deeplabv3plus"


class LossType(str, Enum):
    """
    Available loss function types.
    """

    DICE = "dice"
    BCE_DICE = "dice_bce"
    FOCAL = "focal"


# =============================================================================
# Model Factory
# =============================================================================


class ModelFactory:
    """
    Factory for creating segmentation models and loss functions.

    Usage
    -----
    >>> factory = ModelFactory()
    >>> model = factory.create_model("unet", in_channels=12, num_classes=3)
    >>> loss = factory.create_loss("dice_bce")
    """

    # ------------------------------------------------------------------
    # Model Creation
    # ------------------------------------------------------------------

    def create_model(
        self,
        model_type: str | ModelType,
        in_channels: int = 12,
        num_classes: int = 3,
        encoder_name: str = "resnet34",
        encoder_weights: str | None = "imagenet",
    ) -> nn.Module:
        """
        Create a segmentation model.

        Parameters
        ----------
        model_type : str | ModelType
            One of 'unet', 'deeplabv3plus'.
        in_channels : int
            Number of input channels.
        num_classes : int
            Number of output classes.
        encoder_name : str
            Encoder backbone name.
        encoder_weights : str | None
            Pretrained weights identifier.

        Returns
        -------
        nn.Module

        Raises
        ------
        ValueError
            If model_type is not recognized.
        """

        model_type = ModelType(model_type)

        if model_type == ModelType.UNET:
            model = GeoSentinelUNet(
                in_channels=in_channels,
                num_classes=num_classes,
                encoder_name=encoder_name,
                encoder_weights=encoder_weights,
            )

        elif model_type == ModelType.DEEPLABV3PLUS:
            model = GeoSentinelDeepLabV3Plus(
                in_channels=in_channels,
                num_classes=num_classes,
                encoder_name=encoder_name,
                encoder_weights=encoder_weights,
            )

        else:
            raise ValueError(
                f"Unknown model type: {model_type!r}. "
                f"Available: {[m.value for m in ModelType]}"
            )

        logger.info(f"Created model: {model}")

        return model

    # ------------------------------------------------------------------
    # Loss Creation
    # ------------------------------------------------------------------

    def create_loss(
        self,
        loss_type: str | LossType,
        alpha: float = 0.5,
        gamma: float = 2.0,
        smooth: float = 1.0,
        ignore_index: int | None = None,
    ) -> nn.Module:
        """
        Create a loss function.

        Parameters
        ----------
        loss_type : str | LossType
            One of 'dice', 'dice_bce', 'focal'.
        alpha : float
            BCE weight for dice_bce; class weight for focal.
        gamma : float
            Focusing parameter for focal loss.
        smooth : float
            Smoothing for Dice loss.
        ignore_index : int | None
            Class index to ignore.

        Returns
        -------
        nn.Module
        """

        loss_type = LossType(loss_type)

        if loss_type == LossType.DICE:
            return DiceLoss(
                smooth=smooth,
                ignore_index=ignore_index,
            )

        elif loss_type == LossType.BCE_DICE:
            return BCEDiceLoss(
                alpha=alpha,
                smooth=smooth,
                ignore_index=ignore_index,
            )

        elif loss_type == LossType.FOCAL:
            return FocalLoss(
                gamma=gamma,
                ignore_index=ignore_index,
            )

        else:
            raise ValueError(
                f"Unknown loss type: {loss_type!r}. "
                f"Available: {[l.value for l in LossType]}"
            )

    # ------------------------------------------------------------------
    # From Config
    # ------------------------------------------------------------------

    def from_config(
        self,
        config: dict,
    ) -> tuple[nn.Module, nn.Module]:
        """
        Create model and loss from a configuration dictionary.

        Parameters
        ----------
        config : dict
            Configuration loaded from configs/model.yaml.
            Expected keys: model.name, encoder.backbone,
            input.channels, output.classes, training.loss.

        Returns
        -------
        tuple[nn.Module, nn.Module]
            (model, loss_function)
        """

        model_name = config.get("model", {}).get("name", "unet")
        encoder = config.get("encoder", {}).get("backbone", "resnet34")
        pretrained = config.get("encoder", {}).get("pretrained", True)
        in_channels = config.get("input", {}).get("channels", 12)
        num_classes = config.get("output", {}).get("classes", 3)
        loss_name = config.get("training", {}).get("loss", "dice_bce")

        model = self.create_model(
            model_type=model_name,
            in_channels=in_channels,
            num_classes=num_classes,
            encoder_name=encoder,
            encoder_weights="imagenet" if pretrained else None,
        )

        loss = self.create_loss(loss_type=loss_name)

        return model, loss

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return "ModelFactory()"
