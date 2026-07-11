"""
===============================================================================
GeoSentinel AI

Module:
    ensemble.py

Description:
    Dual-Model Soft Voting Ensemble.
    Combines the predictions of multiple segmentation models (e.g., U-Net 
    and DeepLabV3+) by mathematically averaging their output probabilities.

Author:
    Karthikeya Bhamidipati
===============================================================================
"""

from __future__ import annotations

import torch
import torch.nn as nn

from src.utils.logger import logger


class SoftVotingEnsemble(nn.Module):
    """
    Combines multiple PyTorch segmentation models into a single meta-model.
    
    Averages the softmax probabilities of all constituent models to produce
    a highly robust, generalized prediction.
    """

    def __init__(self, models: list[nn.Module]) -> None:
        super().__init__()
        self.models = nn.ModuleList(models)
        
        for i, model in enumerate(self.models):
            model.eval()
            
        logger.info(f"Initialized SoftVotingEnsemble with {len(models)} models.")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Runs the input through all models, computes their probabilities,
        averages them, and returns log-probabilities (which acts identically 
        to logits for downstream argmax operations).
        """
        # Collect logits from all models
        logits_list = [model(x) for model in self.models]
        
        # Convert to probabilities
        probs_list = [torch.softmax(logits, dim=1) for logits in logits_list]
        
        # Average the probabilities (Soft Voting)
        avg_probs = torch.stack(probs_list, dim=0).mean(dim=0)
        
        # Convert back to log-space so downstream CrossEntropy or argmax works
        return torch.log(avg_probs + 1e-8)
