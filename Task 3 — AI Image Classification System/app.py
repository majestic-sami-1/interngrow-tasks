"""Streamlit application for Task 3: AI Image Classification System."""

from __future__ import annotations

import os
from pathlib import Path
from PIL import Image
import streamlit as st

from src.classifier import get_classifier
from src.utils import (
    add_to_history,
    clear_history,
    create_confidence_chart,
    init_session_state,
)

# Page configuration
st.set_page_config(
    page_title="AI Vision Classifier | InternGrow Task 3",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich, polished visual styling
st.markdown(
    """
    <style>
    /* Main container styling */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    
    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 1.8rem 2.2rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #ffffff;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #c7d2fe;
        margin-top: 0.5rem;
        margin-bottom: 0;
        font-weight: 400;
    }

    /* Top Prediction Banner */
    .prediction-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95));
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.3);
    }
    .prediction-badge {
        display: inline-block;
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        margin-bottom: 0.6rem;
    }
    .prediction-name {
        font-size: 1.85rem;
        font-weight: 800;
        color: #f8fafc;
        margin: 0;
        line-height: 1.2;
    }
    .prediction-conf {
        font-size: 1.2rem;
        font-weight: 600;
        color: #38bdf8;
        margin-top: 0.3rem;
    }

    /* Stat Pills */
    .metric-pill {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        text-align: center;
    }
    .metric-val {
        font-size: 1.15rem;
        font-weight: 700;
        color: #a5b4fc;
    }
    .metric-lbl {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* History Cards */
    .history-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 0.6rem;
        transition: all 0.2s ease;
    }
    .history-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        background: rgba(30, 41, 59, 0.85);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def load_cached_classifier():
    """Load and cache the PyTorch MobileNetV2 classification model."""
    return get_classifier()


def main():
    init_session_state()

    # Hero Header Banner
    st.markdown(
        """
        <div class="hero-container">
            <h1 class="hero-title">
                <span>⚡</span> AI Image Classification System
            </h1>
            <p class="hero-subtitle">
                Production-grade computer vision powered by <b>PyTorch MobileNetV2</b> &bull; Real-time inference across 1,000 ImageNet categories
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar: Model Config & Session History
    with st.sidebar:
        st.subheader("⚙️ Model Configuration")
        top_k = st.slider(
            "Top-K Predictions",
            min_value=3,
            max_value=5,
            value=5,
            help="Select how many highest-probability classes to display (3 to 5).",
        )

        st.markdown("---")
        st.subheader("📊 System Specs")
        classifier = load_cached_classifier()
        st.markdown(
            f"""
            - **Model**: `MobileNetV2`
            - **Framework**: `PyTorch`
            - **Dataset**: `ImageNet-1k`
            - **Device**: `{str(classifier.device).upper()}`
            - **Classes**: `1,000`
            """
        )

        st.markdown("---")
        # Session History Section
        st.subheader("🕒 Session History")
        history = st.session_state["history"]

        col_hist_count, col_hist_btn = st.columns([1, 1])
        with col_hist_count:
            st.caption(f"**{len(history)}** scanned item(s)")
        with col_hist_btn:
            if history:
                if st.button("Clear History", use_container_width=True):
                    clear_history()
                    st.rerun()

        if history:
            for item in history:
                with st.expander(
                    f"#{item['id']} • {item['top_label']} ({item['top_pct']})",
                    expanded=False,
                ):
                    col_th, col_meta = st.columns([1, 1.8])
                    with col_th:
                        st.image(item["thumbnail"], use_container_width=True)
                    with col_meta:
                        st.caption(f"**Time:** {item['timestamp']}")
                        st.caption(f"**Source:** {item['source']}")
                        st.caption(f"**Latency:** {item['latency_ms']:.1f} ms")
                        st.markdown("**Top Predictions:**")
                        for p in item["predictions"][:3]:
                            st.caption(f"- {p['label']}: `{p['percentage']}`")
        else:
            st.info("No images classified yet in this session. Upload or snap a photo to begin.")

    # Main Area: Input Selection Tabs
    tab_upload, tab_camera, tab_samples = st.tabs(
        ["📁 Upload Image", "📷 Live Camera Input", "🖼️ Sample Gallery"]
    )

    image_to_classify: Image.Image | None = None
    input_source = "Upload"

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Choose an image file (PNG, JPG, JPEG, WEBP)",
            type=["png", "jpg", "jpeg", "webp"],
            help="Upload an image from your computer to run classification.",
        )
        if uploaded_file is not None:
            try:
                image_to_classify = Image.open(uploaded_file)
                input_source = "Upload"
            except Exception as e:
                st.error(f"Error opening image: {e}")

    with tab_camera:
        st.markdown(
            "Capture a photo using your webcam to test real-time classification:"
        )
        camera_file = st.camera_input("Take a snapshot")
        if camera_file is not None:
            try:
                image_to_classify = Image.open(camera_file)
                input_source = "Live Camera"
            except Exception as e:
                st.error(f"Error processing camera snapshot: {e}")

    with tab_samples:
        st.markdown("Select a ready-to-test sample image to immediately evaluate the system:")
        sample_dir = Path(__file__).parent / "assets" / "samples"
        sample_options = {}
        if sample_dir.exists():
            for sample_file in sample_dir.glob("*.jpg"):
                sample_options[sample_file.stem.replace("_", " ").title()] = sample_file

        if sample_options:
            selected_sample_name = st.selectbox(
                "Pick a preloaded sample:",
                options=list(sample_options.keys()),
            )
            if st.button("Analyze Selected Sample", use_container_width=True):
                selected_sample_path = sample_options[selected_sample_name]
                image_to_classify = Image.open(selected_sample_path)
                input_source = f"Sample: {selected_sample_name}"
        else:
            st.caption("No preloaded sample images found in assets/samples.")

    # Side-by-Side Classification Display
    if image_to_classify is not None:
        st.markdown("---")

        with st.spinner("Running MobileNetV2 neural network inference..."):
            predictions, latency_ms = classifier.predict(
                image_to_classify, top_k=top_k
            )

        # Track in history if different from last entry
        history = st.session_state["history"]
        is_new_image = True
        if history:
            last = history[0]
            if (
                last["source"] == input_source
                and last["top_label"] == predictions[0].label
                and abs(last["latency_ms"] - latency_ms) < 0.001
            ):
                is_new_image = False

        if is_new_image:
            add_to_history(
                image_to_classify,
                predictions,
                source=input_source,
                latency_ms=latency_ms,
            )

        col_left, col_right = st.columns([1, 1.2], gap="large")

        with col_left:
            st.subheader("🖼️ Input Image")
            st.image(
                image_to_classify,
                caption=f"Source: {input_source} | Dimensions: {image_to_classify.size[0]}x{image_to_classify.size[1]}px",
                use_container_width=True,
            )

            # Image metadata pills
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    f"""
                    <div class="metric-pill">
                        <div class="metric-val">{image_to_classify.format or 'RAW'}</div>
                        <div class="metric-lbl">Format</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"""
                    <div class="metric-pill">
                        <div class="metric-val">{image_to_classify.mode}</div>
                        <div class="metric-lbl">Color Mode</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f"""
                    <div class="metric-pill">
                        <div class="metric-val">{latency_ms:.1f}ms</div>
                        <div class="metric-lbl">Latency</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_right:
            st.subheader("🎯 Classification Results")

            # Top 1 Prediction Banner
            top_pred = predictions[0]
            st.markdown(
                f"""
                <div class="prediction-card">
                    <span class="prediction-badge">Primary Prediction (Rank #1)</span>
                    <h2 class="prediction-name">{top_pred.label}</h2>
                    <div class="prediction-conf">Confidence: {top_pred.percentage}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Interactive Plotly horizontal bar chart
            fig = create_confidence_chart(predictions)
            st.plotly_chart(fig, use_container_width=True)

            # Detailed table breakdown
            with st.expander("📋 View Detailed Class Breakdown", expanded=False):
                table_data = [
                    {
                        "Rank": p.rank,
                        "Category Name": p.label,
                        "ImageNet Identifier": p.raw_label,
                        "Probability Score": f"{p.confidence:.5f}",
                        "Confidence": p.percentage,
                    }
                    for p in predictions
                ]
                st.dataframe(
                    table_data,
                    use_container_width=True,
                    hide_index=True,
                )


if __name__ == "__main__":
    main()
