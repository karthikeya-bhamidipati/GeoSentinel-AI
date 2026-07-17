<div align="center">
  <h1>🌍 GeoSentinel AI</h1>
  <p><b>Advanced Satellite Imagery Analysis & Change Detection Platform</b></p>
  
  [![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](#)
  [![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?logo=pytorch&logoColor=white)](#)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](#)
  [![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white)](#)
</div>

---

GeoSentinel AI is an end-to-end, state-of-the-art web platform engineered to ingest high-resolution, multi-spectral satellite imagery and autonomously detect environmental changes, urban expansion, and land cover evolution over time. 

By leveraging **Sentinel-2 12-channel multispectral data**, spatial alignment algorithms, and cutting-edge deep learning segmentation networks, GeoSentinel AI transforms raw satellite data into actionable, pixel-perfect geographic insights.

## ✨ Core Capabilities

- **Intelligent STAC Retrieval:** Dynamically queries the Sentinel Hub STAC API to find the absolute best images for an Area of Interest (AOI), using a custom *local* cloud-cover algorithm rather than global scene metrics.
- **Multispectral Feature Engineering:** Automatically processes 12 spectral bands (including SWIR and NIR), aligns them spatially via phase cross-correlation, and calculates critical indices (NDVI, NDWI, NDBI).
- **Deep Land Cover Classification:** Segments regions into Urban, Water, Vegetation, and Barren land using a heavy ResNet50-backed DeepLabV3+ architecture.
- **Siamese Change Detection:** Detects structural changes between two time periods (T1 and T2) using a sophisticated Siamese U-Net.

---

## 🧠 Deep Learning Architecture & Inspirations

GeoSentinel AI does not rely on simple image differencing. It utilizes two specialized deep neural networks trained through a grueling 7-iteration optimization journey.

### 1. Land Cover Segmentation: DeepLabV3+
* **Architecture:** DeepLabV3+ with a **ResNet50** encoder.
* **Why?** DeepLabV3+ uses Atrous Spatial Pyramid Pooling (ASPP) to capture multi-scale contextual information, which is critical for satellite imagery where objects (like buildings vs. forests) vary wildly in scale.
* **Performance:** 
  * 💧 Water IoU: **93.45%**
  * 🏙️ Urban IoU: **83.89%**
  * 🌲 Vegetation IoU: **66.13%**

### 2. Change Detection: Siamese U-Net
* **Architecture:** Siamese U-Net with a shared **ResNet34** encoder.
* **Why?** Inspired by the foundational OSCD (Onera Satellite Change Detection) papers, a Siamese network processes T1 and T2 images through identical twin encoders sharing the same weights. This allows the network to learn the *difference in feature representations* rather than just color differences.
* **The Optimization:** To combat severe class imbalance (where 95% of a map doesn't change), we engineered a **CombinedLoss function** (Dice Loss + Focal Loss). This heavily penalized false negatives. We then dynamically raised the inference confidence threshold to `0.75` to eliminate false positives, resulting in surgical change detection.

### 📚 Core Academic References
1. **Chen, L. C., et al. (2018).** *"Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation."* (DeepLabV3+)
2. **Daudt, R. C., et al. (2018).** *"Fully Convolutional Siamese Networks for Change Detection."* (Inspiration for the Siamese U-Net architecture on OSCD datasets).
3. **TorchGeo Framework:** Utilizing structural patterns from Microsoft's TorchGeo for geospatial machine learning.

---

## 🛠️ Technology Stack

**AI & Machine Learning:**
* `PyTorch` & `torchvision` (Core Deep Learning)
* `segmentation_models_pytorch` (Model Architectures)
* `scikit-image` (Sub-pixel Spatial Alignment)

**Geospatial & Backend:**
* `FastAPI` (High-performance Async Python API)
* `pystac-client` & `planetary-computer` (Satellite Data Streaming)
* `rasterio` & `geopandas` (Raster/Vector manipulation)
* `numpy` & `cv2` (Matrix Operations)

**Frontend:**
* `React` & `Next.js 14` (UI Framework)
* `TailwindCSS` (Styling)
* `React-Leaflet` (Interactive Mapping)

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.12+
- Node.js 18+
- Sentinel Hub / CDSE credentials (set in `.env`)

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/karthikeya-bhamidipati/GeoSentinel-AI.git
cd GeoSentinel-AI

# Activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI Server
uvicorn backend.app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install Node modules
npm install

# Start the Next.js development server
npm run dev
```

The platform will be available at `http://localhost:3000`.

---

## 🔮 Future Scope (Frontend 2.0 & Beyond)

Version 1 establishes a rock-solid, mathematically verified deep learning and data processing pipeline. Looking forward, the next immediate phases of development include:

1. **Frontend 2.0 (UX Overhaul):** 
   - Transitioning from a utilitarian light theme to a premium, dark-mode, glassmorphic UI.
   - Introducing dynamic "Split-Screen Swipe Sliders" to visually drag and compare T1 and T2 images effortlessly.
   - Adding Framer Motion micro-animations for a fluid, reactive user experience.
2. **Interface Speed Optimizations:** 
   - Implementing `next/dynamic` lazy-loading for heavy WebGL mapping components.
   - Introducing `SWR` or React Query for robust API caching to eliminate redundant loading times when viewing historical jobs.
3. **Temporal Analytics Dashboard:** Adding interactive graphs showing vegetation decline or urban sprawl over 5-year multi-temporal stacks.

---
*Developed with passion for Earth Observation and Artificial Intelligence.*
