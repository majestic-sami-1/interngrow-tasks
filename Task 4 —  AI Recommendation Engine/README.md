# CineMatch AI — Intelligent Recommendation Engine

A production-grade, full-stack AI Recommendation Engine modeled after **Netflix** and **Amazon**, featuring a decoupled REST API backend, dedicated isolated Python virtual environment, comprehensive security controls, pure NumPy & SciPy Machine Learning models, and a sleek modern entertainment streaming interface.

---

## Architecture Overview

The system is cleanly separated into an isolated backend REST API and a decoupled frontend client:

```
task 4/
├── backend/                        # Dedicated Backend REST API
│   ├── venv/                       # Isolated Virtual Environment (Python 3.14)
│   ├── app.py                      # Flask REST API Server with Blueprints & CORS
│   ├── config.py                   # App Configuration, Security & Model Weights
│   ├── requirements.txt            # Dependencies (flask, flask-cors, numpy, scipy)
│   ├── security/                   # Security Middleware & Authentication
│   │   ├── auth.py                 # API Key Authentication (X-API-Key / Bearer / Query)
│   │   ├── rate_limiter.py         # Sliding-window Rate Limiter (120 req / min)
│   │   ├── headers.py              # Security Headers (CSP, X-Frame-Options, etc.)
│   │   └── validation.py           # Input Sanitization & Range Validation
│   ├── models/                     # Machine Learning Recommendation Engines
│   │   ├── content_based.py        # TF-IDF Vectorizer & Multi-attribute Cosine Similarity
│   │   ├── collaborative.py        # Matrix Factorization via SVD & User-Item CF
│   │   └── hybrid.py               # Dynamic α-Weighted Blending & Cold-Start Adaptation
│   ├── services/
│   │   └── data_service.py         # Thread-safe Persistence & Profile Analysis
│   ├── data/
│   │   ├── catalog.json            # 32 Curated Movies & Series with Detailed Metadata
│   │   ├── users.json              # 5 User Personas & Rating Matrices
│   │   └── history.json            # Recommendation Logs & Audit Trail
│   └── tests/
│       ├── test_recommender.py     # 10 Automated Unit & Security Tests
│       └── verify_e2e.py           # 12-Step Complete User Journey Simulation
├── frontend/                       # Decoupled Web Application
│   ├── index.html                  # Netflix / Amazon Style Streaming Layout
│   ├── css/
│   │   └── style.css               # Dark Glassmorphism, Responsive Styles & Micro-animations
│   └── js/
│       ├── api.js                  # Decoupled API Client with Security Headers
│       └── app.js                  # Frontend Controller, Sliders, Modals & Profile Views
├── run.py                          # Unified One-Click Launcher
└── README.md                       # Documentation & API Specifications
```

---

## Core Features & ML Algorithms

### 1. User Profile Analysis
- **Genre Affinity Radar**: Computes percentage weights and average ratings across user-rated genres.
- **Taste Diversity Index**: Calculates Shannon entropy across rating distributions ($H = -\sum p_i \ln p_i / \ln N$), classifying users as *Specialized*, *Balanced*, or *Eclectic & Diverse*.
- **Novelty Index**: Measures user willingness to explore niche or non-mainstream titles based on catalog popularity inverses.
- **Rating Habits**: Tracks total rated, 5-star ratings, average score, and recent activity timeline.

### 2. Product / Movie Recommendation Rails
- **Hero Spotlight**: Dynamic featured title with highest affinity match percentage.
- **"Top Picks For You"**: Real-time suggestions customized by the active ML model.
- **"Because You Loved..."**: Dynamic anchor-based recommendation rail seeded by the user's highest rated title.
- **"Trending & Critically Acclaimed"**: Global popularity and IMDb rating consensus.

### 3. Similar Item Detection ("More Like This")
- Real-time cosine similarity distance across multi-attribute TF-IDF vectors (genre, director, cast, plot synopsis, and tags).
- Transparent match percentage and reason tags (e.g. *“Directed by Christopher Nolan”*, *“Shared genres: Sci-Fi, Adventure”*).

### 4. Recommendation History & Audit Logging
- Logs every recommendation served with timestamp, model type, confidence score, and status.
- Tracks real-time user reactions (rated, watched, added to watchlist).

---

## Machine Learning Models (NumPy & SciPy)

### 1. Content-Based Filtering
- Builds a custom smoothed **TF-IDF Matrix** with term weighting across multi-attribute item metadata.
- Computes $N \times N$ item-item cosine similarity matrix.
- Generates user profile feature vectors $\vec{u} = \sum w_i \vec{v}_i$ where $w_i = r_i - 2.5$.

### 2. Collaborative Filtering
- Constructs a dense User-Item rating matrix $R$.
- Performs **Matrix Factorization via Truncated Singular Value Decomposition (SVD)**:
  $$R_{\text{norm}} \approx U \cdot \Sigma \cdot V^T$$
- Predicts unobserved user-item ratings $\hat{r}_{u,i} = \mu_u + (U \Sigma V^T)_{u,i}$.
- Computes Item-Item collaborative neighborhood similarity on co-rating vectors.

### 3. Hybrid Recommendation Model
- Blends normalized Content-Based and Collaborative Filtering scores using tunable weight $\alpha$:
  $$\text{Score}_{\text{hybrid}} = \alpha \cdot \text{Score}_{\text{content}} + (1 - \alpha) \cdot \text{Score}_{\text{cf}}$$
- **Dynamic Cold-Start Handling**: Automatically detects users with fewer than 3 ratings and shifts weight towards content features and popularity consensus ($\alpha \ge 0.85$).
- **Granular Explainability**: Provides transparent percentage attribution (e.g. *“80% Content Weight, 20% Collaborative Weight”*).

---

## Security & Protection Controls

1. **API Key Authentication**:
   - Protected endpoints require `X-API-Key: cine-rec-secret-key-2026-secure` (or `Authorization: Bearer ...` or `?api_key=...`).
   - Unauthorized requests are rejected with HTTP 401.
2. **Sliding-Window Rate Limiting**:
   - Limits clients to 120 requests per 60 seconds. Exceeded clients receive HTTP 429 with `Retry-After` header.
3. **Defensive HTTP Security Headers**:
   - Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, and Content Security Policy (CSP).
4. **Input Validation & Sanitization**:
   - HTML stripping, length constraints, and numeric boundary checks for ratings ($[0.5, 5.0]$) and $\alpha$ ($[0.0, 1.0]$).

---

## How to Run

### Option 1: Unified Launcher (Recommended)
```bash
python run.py
```
This automatically starts the backend API on `http://127.0.0.1:5000` using the isolated `backend/venv` and opens the frontend interface in your default browser.

### Option 2: Running Standalone Components
**Start Backend API:**
```bash
backend\venv\Scripts\python.exe backend/app.py
```
*(Runs on `http://127.0.0.1:5000` with API key `cine-rec-secret-key-2026-secure`)*

**Start Frontend Server:**
```bash
backend\venv\Scripts\python.exe -m http.server 8080 --directory frontend
```
*(Open `http://127.0.0.1:8080` in any web browser)*

---

## Automated Tests

Run the unit and integration test suite:
```bash
backend\venv\Scripts\python.exe -m unittest backend/tests/test_recommender.py
```
*(10 tests covering Authentication, Rate Limiting, TF-IDF Cosine similarity, SVD Factorization, Hybrid blending, Cold Start, and Profile Analysis)*

Run the complete 12-step end-to-end user simulation:
```bash
backend\venv\Scripts\python.exe backend/tests/verify_e2e.py
```

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and catalog counts |
| `GET` | `/api/items` | List items (filters: `genre`, `type`, `search`, `featured`) |
| `GET` | `/api/items/<id>` | Full metadata for a specific title |
| `GET` | `/api/items/<id>/similar` | Similar Item Detection ("More Like This") |
| `GET` | `/api/users` | List user personas |
| `GET` | `/api/users/<id>/profile` | Deep User Profile Analysis & Taste Diversity |
| `POST` | `/api/users/<id>/rate` | Submit rating (1-5 ★) with real-time model retraining |
| `POST` | `/api/users/<id>/watchlist` | Toggle item in watchlist |
| `GET` | `/api/recommendations` | Personalized suggestions (`user_id`, `model`, `alpha`) |
| `GET` | `/api/recommendations/curated`| Netflix-style curated rails (Top Picks, Because You Loved, Trending) |
| `GET` | `/api/history` | Recommendation audit trail and interaction history |
| `POST` | `/api/history/interaction` | Log user action on recommendation |
| `GET` | `/api/analytics/model-comparison` | Side-by-side comparison of Content vs Collaborative vs Hybrid |
