# FarmSight — Digital Twin for Precision Agriculture

FarmSight is a real-time **digital twin platform** for smart farming that combines weather intelligence, crop growth simulation, NDVI satellite imagery, and AI-driven recommendations into a single interactive dashboard.

Built with Flask, Three.js, Plotly, and Facebook Prophet.

---

## Features

- Real-Time Weather Monitoring** — Live temperature, humidity, rainfall, and soil moisture tracking
- 3D Crop Digital Twin** — Interactive Three.js visualization of crop growth stages (seedling → maturity) with realistic stem, leaf, and grain head rendering
- **NDVI Satellite Imagery** — Aerial vegetation index analysis showing field-level crop health
- **NDVI Heatmap** — Plotly-powered grid visualization of vegetation density across the field
- **Soil Moisture Forecasting** — 7-day predictive forecast using Facebook Prophet time-series model
- **AI Recommendations** — Reinforcement learning agent (Q-learning) that suggests when to irrigate, fertilize, or wait
- **Manual Controls** — One-click irrigate and fertilize actions that update the digital twin state in real time
- **Dark Theme UI** — Premium glassmorphism design with smooth animations and responsive layout

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   Flask App                     │
│                   (app.py)                      │
├──────────┬──────────┬───────────┬───────────────┤
│  Data    │   Crop   │ Predictor │ Preprocessing │
│  Ingest  │  Model   │ (Prophet  │  (Cleaning &  │
│ (Weather)│ (Digital │  + RL     │   Extraction) │
│          │   Twin)  │  Agent)   │               │
├──────────┴──────────┴───────────┴───────────────┤
│              Frontend Dashboard                 │
│     Three.js · Plotly · Vanilla JS · CSS        │
└─────────────────────────────────────────────────┘
```

| Module              | Role                                                  |
|---------------------|-------------------------------------------------------|
| `app.py`            | Flask routes, caching, template rendering              |
| `data_ingest.py`    | Weather data fetching (API / mock)                     |
| `crop_model.py`     | Digital twin state machine — growth, health, stages    |
| `predictor.py`      | Prophet forecasting + Q-learning recommendation agent  |
| `preprocessing.py`  | Data cleaning and feature extraction                   |
| `config.py`         | Crop parameters, API keys, coordinates                 |

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repo
git clone https://github.com/ghitn/digitaltwin.git
cd digitaltwin

# Install dependencies
pip install -r requirements.txt

# You may also need Prophet separately
pip install prophet

# Run the app
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Screenshots

### Dashboard (Dark Theme)
The dashboard features a premium dark glassmorphism UI with real-time weather metrics, 3D crop visualization, NDVI analysis, soil moisture forecasts, and AI-powered farming recommendations.

---

## 🛠️ Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python, Flask                       |
| ML/AI     | Facebook Prophet, Q-Learning (RL)   |
| 3D Engine | Three.js                            |
| Charts    | Plotly.js                           |
| Frontend  | HTML5, CSS3, Vanilla JavaScript     |
| Styling   | Custom CSS with glassmorphism       |

---

## Project Structure

```
digitaltwin/
├── app.py                  # Main Flask application
├── crop_model.py           # Digital twin crop simulation
├── data_ingest.py          # Weather data ingestion
├── predictor.py            # Prophet forecasting + RL agent
├── preprocessing.py        # Data cleaning
├── config.py               # Configuration & API keys
├── requirements.txt        # Python dependencies
├── templates/
│   ├── dashboard.html      # Main dashboard template
│   └── admin.html          # Admin/debug panel
├── static/
│   ├── style.css           # Dark theme stylesheet
│   └── ndvi_satellite.png  # NDVI satellite field image
└── README.md
```


