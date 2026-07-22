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

class EfficientLinearAttentionBlock(nn.Module):
    """
    SOTA 2024-style Efficient Linear Attention Fusion.
    Uses O(N) complexity linear attention to mathematically model long-range 
    spatial dependencies without the O(N^2) memory crash of standard Transformers.
    """
    def __init__(self, in_channels: int):
        super().__init__()
        self.in_channels = in_channels
        self.embed_dim = in_channels
        
        # Q, K, V projections
        self.q_proj = nn.Conv2d(in_channels, in_channels, 1, bias=False)
        self.k_proj = nn.Conv2d(in_channels, in_channels, 1, bias=False)
        self.v_proj = nn.Conv2d(in_channels, in_channels, 1, bias=False)
        
        self.norm1 = nn.LayerNorm(self.embed_dim)
        self.norm2 = nn.LayerNorm(self.embed_dim)
        
        self.mlp = nn.Sequential(
            nn.Linear(self.embed_dim, self.embed_dim * 2),
            nn.GELU(),
            nn.Linear(self.embed_dim * 2, self.embed_dim)
        )
        
        # Final fusion combines transformer output with explicit absolute difference
        self.fusion_conv = nn.Sequential(
            nn.Conv2d(in_channels * 2, in_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True)
        )
        
    def forward(self, feat1: torch.Tensor, feat2: torch.Tensor) -> torch.Tensor:
        b, c, h, w = feat1.size()
        hw = h * w
        
        # Project
        q = self.q_proj(feat1).view(b, c, hw).permute(0, 2, 1) # B, HW, C
        k = self.k_proj(feat2).view(b, c, hw).permute(0, 2, 1) # B, HW, C
        v = self.v_proj(feat2).view(b, c, hw).permute(0, 2, 1) # B, HW, C
        
        # Linear Attention Kernel: phi(x) = elu(x) + 1
        q = F.elu(q) + 1.0
        k = F.elu(k) + 1.0
        
        # O(N) Linear Attention: Q @ (K^T @ V)
        # K^T @ V -> B, C, C
        kv = torch.bmm(k.permute(0, 2, 1), v) 
        
        # Q @ KV -> B, HW, C
        attn_out = torch.bmm(q, kv)
        
        # Normalize by denominator
        denom = torch.bmm(q, k.sum(dim=1).unsqueeze(-1)) # B, HW, 1
        attn_out = attn_out / (denom + 1e-6)
        
        # Add & Norm
        seq1 = feat1.view(b, c, hw).permute(0, 2, 1)
        out = self.norm1(seq1 + attn_out)
        
        # FFN
        mlp_out = self.mlp(out)
        out = self.norm2(out + mlp_out)
        
        # Reshape back to image: [B, HW, C] -> [B, C, H, W]
        cross_feat = out.permute(0, 2, 1).contiguous().view(b, c, h, w)
        
        # Combine with absolute difference
        abs_diff = torch.abs(feat1 - feat2)
        fused = torch.cat([cross_feat, abs_diff], dim=1)
        
        return self.fusion_conv(fused)
