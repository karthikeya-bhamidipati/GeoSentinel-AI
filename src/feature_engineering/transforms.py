import torch
from torch import nn

class AppendIndicesTransform(nn.Module):
    """
    TorchGeo Transform to dynamically calculate and append spectral indices.
    
    Expects input sample to have an 'image' key with a float tensor of shape (C, H, W).
    Assumes the first 5 channels of the tensor are:
      0: Blue (B02)
      1: Green (B03)
      2: Red (B04)
      3: NIR (B08)
      4: SWIR 1 (B11)
      
    It calculates 7 indices (NDVI, NDBI, NDWI, SAVI, EVI, MNDWI, BSI) and appends
    them to the channel dimension, resulting in a 12-channel tensor.
    """
    def __init__(self, eps: float = 1e-8):
        super().__init__()
        self.eps = eps

    def forward(self, sample: dict) -> dict:
        if "image" not in sample:
            return sample
            
        img = sample["image"]
        
        # Ensure we have at least the 5 required bands (channel dim is -3)
        if img.shape[-3] < 5:
            raise ValueError(f"AppendIndicesTransform requires at least 5 bands, got {img.shape[-3]}")
            
        b_blue  = img[..., 0, :, :]
        b_green = img[..., 1, :, :]
        b_red   = img[..., 2, :, :]
        b_nir   = img[..., 3, :, :]
        b_swir1 = img[..., 4, :, :]
        
        # 1. NDVI = (NIR - Red) / (NIR + Red)
        ndvi = (b_nir - b_red) / (b_nir + b_red + self.eps)
        
        # 2. NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)
        ndbi = (b_swir1 - b_nir) / (b_swir1 + b_nir + self.eps)
        
        # 3. NDWI = (Green - NIR) / (Green + NIR)
        ndwi = (b_green - b_nir) / (b_green + b_nir + self.eps)
        
        # 4. SAVI = 1.5 * (NIR - Red) / (NIR + Red + 0.5)
        savi = 1.5 * (b_nir - b_red) / (b_nir + b_red + 0.5)
        
        # 5. EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1.0)
        evi = 2.5 * (b_nir - b_red) / (b_nir + 6.0 * b_red - 7.5 * b_blue + 1.0 + self.eps)
        
        # 6. MNDWI = (Green - SWIR1) / (Green + SWIR1)
        mndwi = (b_green - b_swir1) / (b_green + b_swir1 + self.eps)
        
        # 7. BSI = ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
        bsi_num = (b_swir1 + b_red) - (b_nir + b_blue)
        bsi_den = (b_swir1 + b_red) + (b_nir + b_blue)
        bsi = bsi_num / (bsi_den + self.eps)
        
        # Stack indices and concatenate to the original bands along the channel dim (-3)
        indices = torch.stack([ndvi, ndbi, ndwi, savi, evi, mndwi, bsi], dim=-3)
        
        # Note: We only take the first 5 bands. If SCL was channel 5, it is discarded.
        # But we already discarded SCL in ApplyCloudMask anyway!
        sample["image"] = torch.cat([img[..., :5, :, :], indices], dim=-3)
        
        # Convert any NaNs or Infs that might have crept in due to division by zero to 0.0
        sample["image"] = torch.nan_to_num(sample["image"], nan=0.0, posinf=0.0, neginf=0.0)
        
        return sample
