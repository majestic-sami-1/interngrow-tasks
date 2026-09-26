# AI Image Classification System (Task 3)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-MobileNetV2-orange.svg)](https://pytorch.org/)
[![Plotly](https://img.shields.io/badge/Visualization-Plotly-purple.svg)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-ready, interactive web application for real-time deep learning image classification built for the **InternGrow AI Track (Task 3)**.

The system utilizes **PyTorch MobileNetV2** pre-trained on ImageNet-1k, featuring instant dual-input support (file upload & live camera snapshot), interactive Plotly confidence distributions, image inspection metrics, and in-session history tracking.

---

## 📸 Key Features

- **⚡ High-Speed MobileNetV2 Engine**: Pre-trained on 1,000 ImageNet categories, optimized for sub-100ms CPU inference.
- **📁 Multi-Format File Upload**: Accepts standard image files (`.png`, `.jpg`, `.jpeg`, `.webp`) with automatic alpha-channel handling and RGB normalization.
- **📷 Live Webcam Snapshot**: Real-time camera capture using Streamlit's native `st.camera_input` component.
- **🖼️ Preloaded Sample Gallery**: Instant 1-click testing with curated sample images (e.g., Dog, Sports Car, Coffee).
- **📊 Interactive Confidence Bar Chart**: Plotly horizontal bar chart displaying top 3 to 5 predicted classes with percentage tooltips.
- **🕒 Session History Drawer**: In-memory visual history drawer with thumbnails, timestamps, latency metrics, and top class predictions.
- **🎛️ Dynamic Top-K Selection**: Real-time slider to toggle between top 3 and top 5 predictions on the fly.
- **🎨 Modern Responsive UI**: Glassmorphic styling, responsive side-by-side view, latency pills, and detailed prediction tables.

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Streamlit Web UI                     │
│  ┌───────────────────────┐   ┌──────────────────────┐  │
│  │  File / Camera Input  │   │ Top-K Slider & Specs │  │
│  └──────────┬────────────┘   └──────────┬───────────┘  │
└─────────────┼───────────────────────────┼──────────────┘
              │                           │
              ▼                           ▼
┌────────────────────────────────────────────────────────┐
│                   ImageClassifier                      │
│             (src/classifier.py: PyTorch)               │
│                                                        │
│  1. Preprocessing:                                     │
│     PIL Image ─► RGB ─► Resize(256) ─► CenterCrop(224) │
│     ─► ToTensor ─► ImageNet Normalization              │
│                                                        │
│  2. Neural Network Forward Pass:                       │
│     Normalized Tensor [1, 3, 224, 224]                 │
│     ─► MobileNetV2 Backbone ─► Logits (1000)           │
│     ─► Softmax ─► Top-K Probabilities                  │
└─────────────────────────────┬──────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│     Plotly Confidence     │   │   Session History State   │
│         Chart             │   │    (Thumbnails & Logs)    │
│      (src/utils.py)       │   │      (src/utils.py)       │
└───────────────────────────┘   └───────────────────────────┘
```

---

## 📁 Project Structure

```
Task 3 — AI Image Classification System/
├── app.py                      # Main Streamlit dashboard application
├── requirements.txt            # Project dependencies
├── README.md                   # System documentation & setup guide
├── .gitignore                  # Git ignore rules
├── assets/
│   └── samples/                # Sample test images (Golden Retriever, Sports Car, Espresso)
├── src/
│   ├── __init__.py             # Source package initializer
│   ├── classifier.py           # MobileNetV2 inference and preprocessing pipeline
│   └── utils.py                # Plotly confidence chart & session history tracking
├── scripts/
│   └── setup_samples.py        # Utility to download or generate sample gallery images
└── tests/
    └── test_classifier.py      # Automated unit and integration tests
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- Web browser (Chrome, Edge, Firefox, Safari)
- Webcam (optional, for live camera input)

### 2. Clone or Navigate to Project
```bash
cd "Task 3 — AI Image Classification System"
```

### 3. Create & Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup Sample Gallery Images (Optional)
```bash
python scripts/setup_samples.py
```

### 6. Launch the Application
```bash
streamlit run app.py
```
The application will automatically open in your browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:
```bash
pytest tests/test_classifier.py -v
```

The test suite validates:
1. Label text formatting (snake_case to clean title text).
2. Model loading & ImageNet 1,000 classes metadata verification.
3. Preprocessing of RGB, RGBA, and Grayscale images to canonical `[1, 3, 224, 224]` tensors.
4. Top-$K$ inference ordering, probability bounds ($0.0 \le p \le 1.0$), and execution latency.
5. Plotly chart construction.

---

## 🔬 Model & Preprocessing Details

- **Architecture**: `MobileNetV2` (Inverted Residuals & Linear Bottlenecks)
- **Parameters**: ~3.5 Million (efficient for edge devices and fast CPU execution)
- **Pre-trained Weights**: `MobileNet_V2_Weights.DEFAULT` (ImageNet-1k)
- **Input Resolution**: `224 x 224` pixels (Center Cropped from `256 x 256`)
- **Normalization Values**:
  - `Mean`: `[0.485, 0.456, 0.406]`
  - `Std`: `[0.229, 0.224, 0.225]`
- **Output**: 1,000-dimensional softmax probability distribution filtered to Top-$K$ (configurable between 3 and 5).

---

## 💡 Usage Guide

1. **Upload Tab**:
   - Drag and drop any image file.
   - The system immediately displays image dimensions, color mode, format, and inference speed.
   - The right column presents the Top #1 category badge and an interactive Plotly confidence chart.
2. **Live Camera Tab**:
   - Grant camera permissions in your browser.
   - Click **Take Photo** to test classification on everyday objects around you.
3. **Sample Gallery Tab**:
   - Select an image from the dropdown menu and click **Analyze Selected Sample** for a 1-click demonstration.
4. **Session History**:
   - View previously classified images in the left sidebar drawer.
   - Expand any item to inspect its thumbnail, timestamp, latency, and top 3 predictions.
   - Click **Clear History** anytime to reset.

---

## 👨‍💻 Author & Submission
- **Internship**: InternGrow AI Track
- **Task**: Task 3 — AI Image Classification System
