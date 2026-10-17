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

By leveraging **Sentinel-2 12-channel multispectral data**, advanced spatial alignment algorithms, and cutting-edge deep learning segmentation networks, GeoSentinel AI transforms raw satellite data into actionable geographic insights.

---

## 🌊 How It Works: The Project Data Flow

GeoSentinel AI handles the entire lifecycle of geospatial analysis automatically. When a user requests an analysis through the interface, the following highly-optimized pipeline is triggered:

1. **User Request Initialization:** The user draws an Area of Interest (AOI) on the interactive React map and selects two distinct timeframes (T1 and T2).
2. **Intelligent STAC Retrieval:** The FastAPI backend pings the Sentinel Hub / Planetary Computer STAC API to find the absolute best images. Crucially, it doesn't rely on global scene cloud metrics; it downloads the Scene Classification (`SCL`) band, calculates the exact cloud percentage *strictly within the user's AOI*, and streams the optimal 12-channel multispectral data.
3. **Preprocessing & Spatial Alignment:** The pipeline masks clouds, resamples 20m/60m bands (like SWIR) to 10m spatial resolution, normalizes values, and uses **Phase Cross-Correlation** (`scikit-image`) to spatially align the T2 image perfectly over the T1 image at the sub-pixel level to prevent false-positive change detection.
4. **Tiled Inference Processing:** The massive geographic arrays are tiled seamlessly and fed into the deep neural networks using sliding-window inference with spatial overlapping to prevent edge artifacts.
5. **Deep Learning Segmentation:**
   - **DeepLabV3+** analyzes the imagery to classify the land cover (Urban, Water, Vegetation, Barren).
   - **Siamese U-Net** analyzes both the T1 and T2 images simultaneously to detect structural ground changes.
6. **Post-Processing & Analytics:** Agriculture classifications are merged with Vegetation, changes are intersected with the land-cover masks to determine *what* changed, and spatial statistics (like square kilometers of urban sprawl) are computed.
7. **Actionable Insights:** The deterministic Recommendation Engine parses the statistics into human-readable alerts and generates a comprehensive PDF report, visual PNG overlays, and raw TIFF rasters available for instant download in the dashboard.

---

## 🧠 Deep Learning Architecture & Empirical Metrics

GeoSentinel AI does not rely on simple image differencing (which often fails due to seasonal lighting changes). It utilizes two specialized deep neural networks trained through a rigorous 7-iteration optimization cycle.

### 1. Land Cover Segmentation: DeepLabV3+
* **Architecture:** DeepLabV3+ with a massive **ResNet50** encoder.
* **Why?** DeepLabV3+ uses Atrous Spatial Pyramid Pooling (ASPP) to capture multi-scale contextual information, which is critical for satellite imagery where objects (like sprawling buildings vs. dense forests) vary wildly in scale.
* **Production Validation Metrics:** 
  * 💧 Water IoU: **93.45%** (Perfect segmentation of rivers and lakes)
  * 🏙️ Urban IoU: **83.89%** (Highly accurate identification of concrete structures)
  * 🌲 Vegetation IoU: **66.13%**

### 2. Change Detection: Semantically-Anchored Linear Attention Siamese U-Net
* **Architecture:** Siamese U-Net with a shared **ResNet34** encoder, plus the DeepLabV3+/ResNet50 land-cover network as a *semantic anchor* (fine-tuned at a 10× lower learning rate) whose features are fused at every scale and mixed by cross-temporal **linear attention** (memory O(d²) instead of O(N²)).
* **Why?** A Siamese network processes the T1 and T2 images through identical twin encoders sharing the same weights, and the anchor tells it what each surface *is*, so seasonal change over stable land cover can be discounted.
* **Training:** Focal Tversky loss (α 0.3, β 0.7, γ 4/3, class weights [0.15, 0.85]) for the change/no-change imbalance; the decision threshold τ is configurable (0.5 balanced, 0.75 higher precision).

#### OSCD benchmark results
Full extent of the ten OSCD test cities (256 px sliding window, stride 128, pooled confusion matrix), τ = 0.5, mean ± s.d. over three training seeds. Checkpoints were selected on three held-out training cities (Beirut, Bordeaux, Cupertino); the test cities were used only for evaluation.

| Model | Precision | Recall | F1 | IoU |
|---|---|---|---|---|
| Baseline (same architecture, ImageNet-initialised anchor branch) | 58.47 ± 4.09 | 48.16 ± 8.06 | 52.33 ± 3.26 | 35.48 ± 2.97 |
| **Proposed (land-cover anchor)** | **66.55 ± 4.01** | **50.58 ± 3.54** | **57.36 ± 2.24** | **40.23 ± 2.21** |

* Per-seed results, per-city scores and validation losses: [`outputs/oscd/summary.json`](outputs/oscd/summary.json).
* Released checkpoint `data/weights/change_unet_best.pt` = the anchored run with the lowest validation loss (seed 2, [`outputs/oscd/best_run.json`](outputs/oscd/best_run.json)); a local re-evaluation reproduces its scores exactly ([`outputs/oscd/local_reproduction_seed2.json`](outputs/oscd/local_reproduction_seed2.json), F1 59.91).
* Reproduce: run [`notebooks/kaggle_oscd_experiments.ipynb`](notebooks/kaggle_oscd_experiments.ipynb) (wraps `scripts/kaggle_job.py data | train | report`), or evaluate locally:
  ```bash
  python scripts/evaluate_change_fullscene.py --weights data/weights/change_unet_best.pt --oscd-root <path to OSCD>
  ```

---

## 📚 Foundational Papers & References

This architecture was heavily inspired by leading research in Earth Observation (EO) and Computer Vision:

1. **TorchGeo Framework:** Utilizing structural data-loading patterns from Microsoft's TorchGeo for robust geospatial machine learning. *(Stewart et al. - TorchGeo: Deep Learning with Geospatial Data)*
2. **Siamese Neural Networks:** Inspiration for the twin-encoder architecture designed for the Onera Satellite Change Detection (OSCD) dataset. *(Daudt, R. C., et al., 2018. "Fully Convolutional Siamese Networks for Change Detection")*
3. **DeepLabV3+:** The foundational model used for semantic pixel classification. *(Chen, L. C., et al., 2018. "Encoder-Decoder with Atrous Separable Convolution for Semantic Image Segmentation")*

---

## 🛠️ Technology Stack

**AI & Machine Learning:**
* `PyTorch` & `torchvision` (Core Deep Learning framework)
* `segmentation_models_pytorch` (Advanced Model Architectures)
* `scikit-image` (Sub-pixel Spatial Alignment algorithm)

**Geospatial & Backend API:**
* `FastAPI` (High-performance Async Python API)
* `pystac-client` & `planetary-computer` (Cloud-native Satellite Data Streaming)
* `rasterio` & `geopandas` (Raster/Vector geographic matrix manipulation)

**Frontend Application:**
* `React` & `Next.js 14` (UI Framework)
* `TailwindCSS` (Design System)
* `React-Leaflet` (Interactive Mapping)

---

## 🚀 Deployment (Docker Hub)

The fastest and most reliable way to run GeoSentinel AI on any machine is using our prebuilt Docker images. This ensures you do not need to install PyTorch, geospatial packages, or Node.js locally.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose installed.

### Start the Services
Simply run the following command in the project root directory (where `docker-compose.yml` is located):
```bash
# Pull the prebuilt images from Docker Hub
docker compose pull

# Start the services in detached mode
docker compose up -d
```

This will pull the compiled production images:
* **Frontend:** `karthikeyabh/geosentinel-frontend:latest`
* **Backend:** `karthikeyabh/geosentinel-backend:latest`

Once started:
- **Frontend Dashboard:** `http://localhost:3000`
- **FastAPI Backend API:** `http://localhost:8000`

> [!TIP]
> If you wish to build the images locally from the source files instead of pulling from Docker Hub, you can run:
> ```bash
> docker compose up --build -d
> ```

---

## 🚀 How to Run Locally (Without Docker)

### Prerequisites
- Python 3.12+ installed and added to PATH
- Node.js 18+ installed

### 1. Launch using the Automated Script (Windows)

Simply double-click the `start_local.bat` script in the root directory. 

What the script does automatically:
1. Creates a Python virtual environment (`venv`).
2. Installs all required backend PyTorch and geospatial dependencies.
3. Installs all frontend Node.js packages.
4. Starts the **FastAPI Backend** on Port `8000`.
5. Starts the **Next.js Frontend** on Port `3000`.

The platform will automatically be available at `http://localhost:3000`.

*(For Mac/Linux users, you can manually activate the `venv`, install `requirements.txt`, and run `npm run dev` in the frontend folder).*

---

## 🔮 Future Scope & Roadmap

Version 1 establishes a rock-solid, mathematically verified deep learning pipeline. The roadmap for future versions includes:

1. **Frontend 2.0 (UX Overhaul):** 
   - Transitioning from a utilitarian light theme to a premium, dark-mode, glassmorphic UI.
   - Introducing dynamic "Split-Screen Swipe Sliders" to visually drag and compare T1 and T2 images over the map.
2. **Interface Speed Optimizations:** 
   - Implementing `next/dynamic` lazy-loading for heavy WebGL mapping components.
   - Introducing React Query API caching to eliminate redundant loading times when viewing historical background jobs.
3. **Dockerization & Cloud Deployment:** 
   - Containerizing the entire microservice architecture (Frontend, API, and Celery/Redis workers) using Docker Compose for seamless cloud deployment to AWS/GCP.
4. **Temporal Analytics Dashboard:** Adding interactive graphs showing vegetation decline or urban sprawl over multi-year datasets.

---
*Developed with a passion for Earth Observation and Artificial Intelligence.*
