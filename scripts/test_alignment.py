import numpy as np
from skimage.registration import phase_cross_correlation
import scipy.ndimage as ndimage

# Create a 2D reference array with a square feature at [10:20, 10:20]
ref_img = np.zeros((50, 50))
ref_img[10:20, 10:20] = 1.0

# Create a target array where the square is shifted to [15:25, 12:22]
# So target is shifted by +5 in y, +2 in x compared to reference
tgt_img = np.zeros((50, 50))
tgt_img[15:25, 12:22] = 1.0

# Calculate shift needed to align target to reference
# (i.e. we expect shift of -5, -2 to move the target back to [10:20, 10:20])
shift, error, diffphase = phase_cross_correlation(ref_img, tgt_img, upsample_factor=10)

print(f"Calculated shift: {shift}")

# Apply the shift to the target image
aligned_tgt = ndimage.shift(tgt_img, shift, order=3, mode='reflect')

# Verify the aligned target now matches the reference
max_diff = np.max(np.abs(ref_img - aligned_tgt))
print(f"Max difference after alignment: {max_diff:.4f}")

# Just to be absolutely sure, check the center of the square
print(f"Ref center (15, 15): {ref_img[15, 15]}")
print(f"Aligned Tgt center (15, 15): {aligned_tgt[15, 15]:.2f}")
