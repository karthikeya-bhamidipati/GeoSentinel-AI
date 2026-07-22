"""
GeoSentinel AI - Siamese U-Net for Change Detection
"""

import torch
import torch.nn as nn
import segmentation_models_pytorch as smp
from src.models.deeplabv3plus import GeoSentinelDeepLabV3Plus

class ChannelReducer(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        
    def forward(self, x):
        return self.relu(self.bn(self.conv(x)))

class GeoSentinelSiameseUNet(nn.Module):
    """
    Siamese U-Net that fuses ResNet50 (DeepLab) and ResNet34 (U-Net) features.
    """
    def __init__(
        self, 
        deeplab_ckpt_path: str,
        num_classes: int = 2,
        ablation_mode: bool = False,
    ):
        super().__init__()
        self.ablation_mode = ablation_mode
        
        # 1. Load DeepLabV3+ Encoder
        self.deeplab = GeoSentinelDeepLabV3Plus(in_channels=12, num_classes=5, encoder_name="resnet50")
        
        if not self.ablation_mode:
            print(f"Loading frozen Semantic DeepLabV3+ from {deeplab_ckpt_path}")
            checkpoint = torch.load(deeplab_ckpt_path, map_location="cpu", weights_only=True)
            state_dict = checkpoint.get("model_state_dict", checkpoint.get("state_dict", checkpoint))
            
            # Fix model prefix if necessary
            new_sd = {}
            for k, v in state_dict.items():
                if not k.startswith("model."):
                    new_sd[f"model.{k}"] = v
                else:
                    new_sd[k] = v
            self.deeplab.load_state_dict(new_sd, strict=False)
        else:
            print(f"ABLATION MODE: Ignoring semantic weights. Using raw ImageNet ResNet50.")
            # Note: SMP automatically downloads ImageNet weights on initialization if specified.
        
        # We allow DeepLab to be fine-tuned (protected), but we MUST keep it in eval mode 
        # so BatchNorm uses running stats and doesn't crash on batch_size=1
        for param in self.deeplab.parameters():
            param.requires_grad = True
        self.deeplab.eval()
        
        # 2. Trainable U-Net Encoder and Decoder
        self.unet = smp.Unet(
            encoder_name="resnet34",
            encoder_weights="imagenet",
            in_channels=12,
            classes=num_classes,
        )
        
        # ResNet34 (U-Net) channels: [3, 64, 64, 128, 256, 512]
        # ResNet50 (DeepLab) channels: [3, 64, 256, 512, 1024, 2048]
        # Concat channels: [6, 128, 320, 640, 1280, 2560]
        # Expected decoder input channels: [3, 64, 64, 128, 256, 512]
        
        self.reducers = nn.ModuleList([
            ChannelReducer(128, 64),
            ChannelReducer(320, 64),
            ChannelReducer(640, 128),
            ChannelReducer(1280, 256),
            ChannelReducer(2560, 512)
        ])
        
        from src.models.attention import EfficientLinearAttentionBlock
        
        # Transformer-based Cross-Attention modules for each scale
        # Scale 0 (Input): 12 channels
        # Scale 1: 64 channels
        # Scale 2: 64 channels
        # Scale 3: 128 channels
        # Scale 4: 256 channels
        # Scale 5: 512 channels
        self.cross_attentions = nn.ModuleList([
            EfficientLinearAttentionBlock(12),
            EfficientLinearAttentionBlock(64),
            EfficientLinearAttentionBlock(64),
            EfficientLinearAttentionBlock(128),
            EfficientLinearAttentionBlock(256),
            EfficientLinearAttentionBlock(512)
        ])
        
        # We also need to process the 5-class DeepLab logits into the bottleneck
        self.bottleneck_fusion = nn.Sequential(
            nn.Conv2d(512 + 5, 512, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True)
        )
        
    def train(self, mode=True):
        super().train(mode)
        # DeepLab must always remain in eval mode so BatchNorm doesn't crash on batch_size=1
        self.deeplab.eval()
        return self

    def extract_deeplab(self, x):
        """Extract features and logits from DeepLab."""
        # Now that DeepLab is not frozen, we don't force torch.no_grad()
        features = self.deeplab.model.encoder(x)
        logits = self.deeplab(x)
        return features, logits

    def forward(self, t1, t2):
        # 1. Extract DeepLab features
        d_feat1, logits1 = self.extract_deeplab(t1)
        d_feat2, logits2 = self.extract_deeplab(t2)
        
        # 3. Extract U-Net features
        u_feat1 = self.unet.encoder(t1)
        u_feat2 = self.unet.encoder(t2)
        
        # 4. Feature Fusion with Cross-Attention
        fused_features = []
        
        # Scale 0 (Input)
        fused_features.append(self.cross_attentions[0](u_feat1[0], u_feat2[0]))
        
        # For scales 1 to 5
        for i in range(1, 6):
            if u_feat1[i].shape[2:] != d_feat1[i].shape[2:]:
                d1 = nn.functional.interpolate(d_feat1[i], size=u_feat1[i].shape[2:], mode='bilinear', align_corners=False)
                d2 = nn.functional.interpolate(d_feat2[i], size=u_feat2[i].shape[2:], mode='bilinear', align_corners=False)
            else:
                d1 = d_feat1[i]
                d2 = d_feat2[i]
                
            concat1 = torch.cat([u_feat1[i], d1], dim=1)
            concat2 = torch.cat([u_feat2[i], d2], dim=1)
            
            # Reduce
            reduced1 = self.reducers[i-1](concat1)
            reduced2 = self.reducers[i-1](concat2)
            
            # Cross Attention Fusion
            fused = self.cross_attentions[i](reduced1, reduced2)
            fused_features.append(fused)
            
        # 5. Inject DeepLab Logits at Bottleneck (fused_features[-1])
        B, C, H, W = fused_features[-1].shape
        pooled_logits1 = nn.functional.interpolate(logits1, size=(H, W), mode='bilinear', align_corners=False)
        pooled_logits2 = nn.functional.interpolate(logits2, size=(H, W), mode='bilinear', align_corners=False)
        logits_diff = torch.abs(pooled_logits1 - pooled_logits2) # [B, 6, H, W]
        
        # Fuse bottleneck
        fused_features[-1] = self.bottleneck_fusion(torch.cat([fused_features[-1], logits_diff], dim=1))
        
        # 6. Decode
        # UnetDecoder in SMP expects unpacked features: forward(self, *features)
        try:
            decoder_output = self.unet.decoder(*fused_features)
        except TypeError:
            decoder_output = self.unet.decoder(fused_features)
        
        # 7. Segmentation Head
        masks = self.unet.segmentation_head(decoder_output)
        
        return masks
