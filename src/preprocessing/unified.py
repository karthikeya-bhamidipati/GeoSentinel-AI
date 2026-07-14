import torch
from torch import nn

from src.preprocessing.cloudmask import ApplyCloudMask
from src.preprocessing.normalize import NormalizeSentinel2
from src.feature_engineering.transforms import AppendIndicesTransform

class GeoSentinelTransform(nn.Module):
    """
    Unified TorchGeo Transform Pipeline.
    
    This guarantees that the exact same mathematical operations are applied 
    during training, validation, and real-time inference.
    
    Expected input: dict with an "image" float tensor of shape (C, H, W)
    Channels expected (in order): B02, B03, B04, B08, B11, SCL
    """
    def __init__(self):
        super().__init__()
        
        # 1. Mask clouds and drop the SCL band
        self.cloud_mask = ApplyCloudMask(scl_index=5)
        
        # 2. Normalize DN to reflectance [0, 1]
        self.normalize = NormalizeSentinel2(scale_factor=10000.0)
        
        # 3. Append spectral indices to create the 12-channel FeatureStack
        self.feature_eng = AppendIndicesTransform()

    def forward(self, sample: dict) -> dict:
        sample = self.cloud_mask(sample)
        sample = self.normalize(sample)
        sample = self.feature_eng(sample)
        return sample
