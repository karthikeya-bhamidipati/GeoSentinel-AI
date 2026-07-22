Write-Host "=================================================="
Write-Host "Starting Optimized Training for GeoSentinel AI"
Write-Host "Device VRAM Target: 4GB"
Write-Host "=================================================="

Write-Host "1. Training DeepLabV3+..."
# Reduced batch size to 2 to fit in 4GB VRAM.
python scripts/train.py --model deeplabv3plus --batch-size 2 --epochs 30 --num-workers 4

if ($LASTEXITCODE -eq 0) {
    Write-Host "DeepLabV3+ Training Completed Successfully."
    Write-Host "2. Training Siamese U-Net..."
    # Siamese U-Net is heavy (two encoders, one decoder). Batch size 1.
    python scripts/train_change.py --batch-size 1 --epochs 30 --num-workers 4
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Siamese U-Net Training Completed Successfully."
        Write-Host "All training complete! Magic has happened."
    } else {
        Write-Host "Siamese U-Net Training Failed with exit code $LASTEXITCODE"
    }
} else {
    Write-Host "DeepLabV3+ Training Failed with exit code $LASTEXITCODE. Aborting Siamese training."
}
