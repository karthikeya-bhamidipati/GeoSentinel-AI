# GeoSentinel AI

GeoSentinel AI is a cloud-native geospatial analytics platform for urban expansion and vegetation dynamics monitoring in the Hyderabad Metropolitan Region (HMR) using Sentinel-2 imagery.

## Features

- **Automated Data Acquisition**: Integration with Copernicus Data Space Ecosystem (CDSE) for automated Sentinel-2 L2A STAC searches and downloads.
- **Robust Preprocessing**: Cloud masking (using SCL), atmospheric correction, sub-pixel alignment, and 10m resampling.
- **Advanced AI Segmentation**: ResNet-backed U-Net and DeepLabV3+ architectures for semantic land cover classification across 6 classes (Urban, Vegetation, Water, Barren, Agriculture, Background).
- **Temporal Analytics**: NDBI and NDVI change detection for monitoring urban expansion and vegetation health.
- **Rule-Based Recommendations**: Deterministic, explainable recommendation engine triggering actionable insights without LLM hallucinations.
- **Comprehensive Reporting**: Automatic generation of PDF reports, GeoJSON hotspots, GeoTIFF maps, and CSV statistics.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, PyTorch, Segmentation Models PyTorch, Rasterio, Shapely, ReportLab
- **Frontend**: Next.js 14, React 18, TypeScript, Leaflet, Recharts
- **Infrastructure**: Docker, Docker Compose, Nginx

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.11 (for local backend development)

### Environment Setup

1. Copy `.env.example` to `.env` and fill in your Copernicus Data Space Ecosystem (CDSE) credentials:
   ```bash
   cp .env.example .env
   ```

### Running with Docker

Use Docker Compose to spin up the entire stack (Backend, Frontend, and Nginx reverse proxy):

```bash
cd docker
docker-compose up --build
```

The application will be available at:
- Frontend: `http://localhost:3000` or `http://localhost`
- Backend API: `http://localhost/api/v1`
- API Documentation: `http://localhost/api/docs`

## Project Structure

- `backend/`: FastAPI application, API routes, and async job queues
- `frontend/`: Next.js React application and UI components
- `src/`: Core Python modules for earth observation, AI modeling, temporal analytics, and reporting
- `configs/`: YAML configuration files (rules, API settings, logging)
- `data/`: Storage for reference boundaries, cached scenes, and output reports
- `docker/`: Dockerfiles and docker-compose configurations
- `docs/`: Master spec and research papers

## License
MIT License
