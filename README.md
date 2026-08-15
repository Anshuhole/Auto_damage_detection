# AutoInspect AI — Intelligent Vehicle Damage Detection & Repair Cost Estimation System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2.0-EE4C2C.svg?style=flat&logo=PyTorch&logoColor=white)](https://pytorch.org)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?style=flat&logo=React&logoColor=black)](https://reactjs.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.1-38B2AC.svg?style=flat&logo=TailwindCSS&logoColor=white)](https://tailwindcss.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**AutoInspect AI** is an end-to-end intelligent vehicle inspection and repair cost estimation system designed for automotive insurance claim adjustments, fleet management, and used-car appraisals. Powered by deep transfer learning on **ResNet50**, explainable AI (**Grad-CAM**), an actuarial rule-based repair cost engine, and automated **ReportLab PDF claim generation**.

---

## 📸 Key Features & Capabilities

- 🚗 **Real-Time Damage Classification**: Classifies vehicle condition into 5 distinct categories: `Surface Scratch`, `Panel Dent`, `Structural Crack`, `Shattered Glass`, or `Pristine (No Damage)`.
- ⚠️ **Severity Estimation**: Predicts damage severity tier (`Minor`, `Moderate`, `Severe`, `None`) to determine repair urgency and procedure.
- 🔬 **Grad-CAM Visual Explainability**: Backpropagates gradients to Layer 4 convolutional feature maps to produce localized heatmaps, eliminating black-box opacity and extracting contour bounding boxes.
- 💰 **Itemized Cost Estimation Engine**: Evaluates body shop labor hours ($95/hr), panel paint/refinishing costs, OEM hardware replacements, and insurance contingency buffers.
- 📄 **Certified PDF Inspection Report**: Automatically generates official, downloadable PDF inspection certificates with side-by-side original and Grad-CAM images, metadata, and cost breakdowns.
- 📷 **Multi-Modal Image Input**: Supports drag-and-drop file uploads, live mobile/desktop webcam capture with HUD crosshairs, and 1-click preset demo cars.
- 📊 **Telemetry & Historical Database**: SQLite database tracking all past appraisals with search, filtering, and aggregated analytics KPIs.
- 🐳 **Production Containerized**: Docker & Docker Compose setup ready for cloud or on-prem deployment.

---

## 🏗️ System Architecture

```
                                  +---------------------------------------+
                                  |         React 18 + Tailwind UI        |
                                  |  - Drag & Drop Dropzone               |
                                  |  - Live Webcam Capture HUD            |
                                  |  - Interactive Grad-CAM Opacity Slider|
                                  |  - Itemized Cost Breakdown Card       |
                                  |  - Inspection Claim History & Filters |
                                  +-------------------+-------------------+
                                                      | HTTP / REST
                                                      v
                                  +---------------------------------------+
                                  |            FastAPI Gateway            |
                                  |  - /api/predict & /api/predict/base64 |
                                  |  - /api/history & /api/history/{id}   |
                                  |  - /api/report/{id}/pdf               |
                                  |  - /api/stats (Analytics Engine)      |
                                  +---------+-------------------+---------+
                                            |                   |
                     +----------------------+                   +---------------------+
                     v                                                                v
   +-----------------------------------+                             +-----------------------------------+
   |        PyTorch AI Engine          |                             |     SQLite DB & ReportLab PDF     |
   | - Preprocessing & Normalization   |                             | - Inspection History Storage      |
   | - ResNet50 Transfer Learning      |                             | - Official PDF Claim Generator    |
   | - Grad-CAM Activation Heatmaps    |                             | - Aggregated Analytics Metrics    |
   | - Contour Bounding Box Extraction |                             +-----------------------------------+
   | - Actuarial Cost Lookup Matrix    |
   +-----------------------------------+
```

---

## 📂 Codebase Structure

```
Damage_detection/
├── backend/
│   ├── app/
│   │   ├── config.py             # Paths, model hyperparameters & cost lookup tables
│   │   ├── database.py           # SQLAlchemy database session & engine
│   │   ├── models.py             # SQLite InspectionRecord ORM schema
│   │   ├── schemas.py            # Pydantic request & response models
│   │   ├── main.py               # FastAPI application, CORS, static mounts
│   │   ├── routes/
│   │   │   ├── predict.py        # /api/predict (File upload & webcam base64)
│   │   │   ├── history.py        # /api/history (CRUD, search, pagination)
│   │   │   ├── report.py         # /api/report/{id}/pdf (ReportLab generation)
│   │   │   └── stats.py          # /api/stats (Dashboard KPI aggregates)
│   │   ├── ml/
│   │   │   ├── classifier.py     # ResNet50 DamageClassifierNet & VehicleDamagePredictor
│   │   │   ├── gradcam.py        # Grad-CAM forward/backward hooks & overlay blending
│   │   │   └── cost_estimator.py # Actuarial repair cost rule matrix
│   │   └── utils/
│   │       ├── image_utils.py    # Image encoding/decoding & static file management
│   │       └── pdf_generator.py  # Professional PDF report formatting
│   ├── static/                   # Uploaded photos, Grad-CAM overlays & generated PDFs
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Backend container definition
├── ml_training/
│   ├── train.py                  # PyTorch transfer learning training loop
│   ├── evaluate.py               # Confusion matrix & classification report generator
│   ├── dataset_loader.py         # Data augmentations & PyTorch DataLoaders
│   ├── generate_synthetic_data.py# Standalone synthetic dataset generator
│   ├── model_training.ipynb      # Step-by-step Jupyter Notebook
│   └── README.md                 # ML methodology and Kaggle dataset guide
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx            # Brand header, tab navigation & API status
│   │   │   ├── HeroSection.jsx       # Automotive intro with feature highlights
│   │   │   ├── ImageUploader.jsx     # Drag & drop upload + sample selector
│   │   │   ├── WebcamCapture.jsx     # Live camera HUD view with crosshairs
│   │   │   ├── SampleCarGallery.jsx  # 1-click test cards with presets
│   │   │   ├── AnalysisProgress.jsx  # Animated multi-stage radar scan UI
│   │   │   ├── ResultsCard.jsx       # Classification, confidence & quick actions
│   │   │   ├── GradCamViewer.jsx     # Interactive opacity slider & side-by-side view
│   │   │   ├── CostBreakdownCard.jsx # Itemized labor, parts & paint breakdown
│   │   │   ├── InspectionHistory.jsx # Past claims table with search & filters
│   │   │   ├── StatsDashboard.jsx    # Analytics charts & KPI cards
│   │   │   ├── InspectionModal.jsx   # Detailed claim history drilldown modal
│   │   │   └── ModelSpecsModal.jsx   # Technical architecture specs dialog
│   │   ├── services/api.js           # API client
│   │   ├── App.jsx                   # Main React app & state machine
│   │   └── index.css                 # Dark automotive theme & glassmorphism
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml            # Multi-container orchestration
├── README.md                     # Project documentation
└── PROJECT_SUMMARY.md            # Resume bullet points & interview cheat sheet
```

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Docker & Docker Compose

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open your browser at: `http://localhost:5173`

---

## 🐳 Docker Deployment

To launch the complete full-stack application with Docker Compose:
```bash
docker-compose up --build
```
- **Web App**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 🧠 Machine Learning & Explainability

### Mathematical Formulation of Grad-CAM
Grad-CAM calculates the gradient of the score for class $c$ ($y^c$) with respect to feature map activations $A^k$ of convolutional layer $k$:

$$\alpha_k^c = \frac{1}{Z} \sum_{i} \sum_{j} \frac{\partial y^c}{\partial A_{i,j}^k}$$

The visual localization map $L_{\text{Grad-CAM}}^c$ is computed as a weighted linear combination followed by a Rectified Linear Unit (ReLU) to filter out features that contribute negatively:

$$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$

---

## 📊 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/predict` | Multipart form image upload for damage classification |
| `POST` | `/api/predict/base64` | Base64 image payload (webcam capture) |
| `GET` | `/api/history` | List past inspections with search & severity filters |
| `GET` | `/api/history/{id}` | Full detail of an individual appraisal |
| `DELETE` | `/api/history/{id}` | Delete inspection record and associated images |
| `GET` | `/api/report/{id}/pdf` | Generates and downloads certified PDF inspection report |
| `GET` | `/api/stats` | Aggregated analytics KPIs & distribution breakdown |
| `GET` | `/api/health` | Service health check |

---

## 📜 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
