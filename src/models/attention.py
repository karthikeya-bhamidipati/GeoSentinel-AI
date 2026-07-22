"""
GeoSentinel AI - Attention Modules for Research Enhancements
============================================================
Provides advanced attention mechanisms for multi-spectral data and bi-temporal fusion.
1. SpectralAttentionGate: Channel attention tailored for 12-band Sentinel-2 imagery.
2. CrossAttentionFusion: Fuses feature maps from T1 and T2 to detect structural 
   changes while ignoring seasonal phenology.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class SpectralAttentionGate(nn.Module):
    """
    Squeeze-and-Excitation (SE) style channel attention module.
    Designed to dynamically re-weight the 12 spectral bands of Sentinel-2
    based on the scene's global context (e.g., boosting NIR for vegetation).
    """
    def __init__(self, in_channels: int = 12, reduction_ratio: int = 4):
        super().__init__()
        mid_channels = max(1, in_channels // reduction_ratio)
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        
        self.mlp = nn.Sequential(
            nn.Linear(in_channels, mid_channels, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(mid_channels, in_channels, bias=False),
            nn.Sigmoid()
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, _, _ = x.size()
        # Squeeze: Global Information Embedding
        y = self.global_pool(x).view(b, c)
        
        # Excitation: Adaptive Recalibration
        y = self.mlp(y).view(b, c, 1, 1)
        
        # Scale the input
        return x * y.expand_as(x)


class CrossAttentionFusion(nn.Module):
    """
    Bi-Temporal Cross-Attention Fusion Module.
    Replaces simple absolute difference for Change Detection.
    Learns correlation between T1 and T2 feature maps.
    """
    def __init__(self, in_channels: int):
        super().__init__()
        self.in_channels = in_channels
        
        # Final fusion layer combining the attention output with absolute difference
        self.fusion_conv = nn.Sequential(
            nn.Conv2d(in_channels * 2, in_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True)
        )
        
        self.gamma = nn.Parameter(torch.zeros(1))
        
    def forward(self, feat1: torch.Tensor, feat2: torch.Tensor) -> torch.Tensor:
        """
        feat1: Feature map from Time 1
        feat2: Feature map from Time 2
        """
        b, c, h, w = feat1.size()
        
        # Compute Channel Cross-Attention (feat1 attending to feat2 channels)
        # Query from T1, Key and Value from T2
        query = feat1.view(b, c, -1) # B x C x (HW)
        key = feat2.view(b, c, -1).permute(0, 2, 1) # B x (HW) x C
        
        # Attention map: C x C (correlation between each channel in T1 and T2)
        energy = torch.bmm(query, key) # B x C x C
        
        # Scale by sqrt(HW) to prevent gradient vanishing in softmax
        energy = energy / ((h * w) ** 0.5)
        attention = F.softmax(energy, dim=-1) # B x C x C
        
        value = feat2.view(b, c, -1) # B x C x (HW)
        
        # Apply attention to T2 features
        out = torch.bmm(attention, value) # B x C x (HW)
        out = out.view(b, c, h, w)
        
        # Residual connection scaled by gamma
        cross_feat = self.gamma * out + feat1
        
        # Combine cross-attended features with explicit difference for robust change detection
        abs_diff = torch.abs(feat1 - feat2)
        
        fused = torch.cat([cross_feat, abs_diff], dim=1)
        return self.fusion_conv(fused)
