"""Utility functions for visualization and session history management."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, List, Optional
from PIL import Image
import plotly.graph_objects as go
import streamlit as st


def create_confidence_chart(
    predictions: List[Any],
    theme: str = "plotly_dark",
) -> go.Figure:
    """Create an interactive horizontal bar chart for top predictions using Plotly.

    Args:
        predictions: List of PredictionResult objects or dictionaries.
        theme: Base plotly template name.

    Returns:
        Plotly Figure object.
    """
    labels = []
    confs = []
    text_labels = []

    for pred in predictions:
        if hasattr(pred, "label"):
            lbl = pred.label
            conf = pred.confidence
            pct = pred.percentage
        else:
            lbl = pred["label"]
            conf = pred["confidence"]
            pct = pred.get("percentage", f"{conf * 100:.2f}%")

        labels.append(lbl)
        confs.append(conf * 100.0)
        text_labels.append(f"<b>{pct}</b>")

    # Reverse lists so the highest prediction appears at the top of the horizontal chart
    labels_rev = list(reversed(labels))
    confs_rev = list(reversed(confs))
    text_labels_rev = list(reversed(text_labels))

    # Color gradient mapping from top prediction to lower predictions
    # Higher values get a vibrant gradient
    num_bars = len(labels_rev)
    colors = []
    for i in range(num_bars):
        # The highest prediction is at index num_bars - 1
        ratio = (i + 1) / max(num_bars, 1)
        # Interpolate between a pleasant indigo/teal to bright violet
        r = int(59 + ratio * (99 - 59))
        g = int(130 + ratio * (102 - 130))
        b = int(246 + ratio * (241 - 246))
        colors.append(f"rgb({r}, {g}, {b})")

    fig = go.Figure(
        go.Bar(
            x=confs_rev,
            y=labels_rev,
            orientation="h",
            text=text_labels_rev,
            textposition="outside",
            marker=dict(
                color=colors,
                line=dict(color="rgba(255, 255, 255, 0.2)", width=1),
            ),
            hovertemplate="<b>%{y}</b><br>Confidence: %{x:.2f}%<extra></extra>",
        )
    )

    max_x = max(confs_rev) if confs_rev else 100.0
    upper_bound = min(105.0, max_x + (15.0 if max_x < 90 else 10.0))

    fig.update_layout(
        title=dict(
            text="<b>Prediction Confidence Distribution</b>",
            x=0.0,
            font=dict(size=16),
        ),
        xaxis=dict(
            title="Confidence (%)",
            range=[0, upper_bound],
            showgrid=True,
            gridcolor="rgba(128, 128, 128, 0.15)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=False,
            autorange=True,
            tickfont=dict(size=13, family="sans-serif"),
        ),
        margin=dict(l=10, r=30, t=40, b=30),
        height=300 + (len(predictions) - 3) * 35,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def create_thumbnail(image: Image.Image, size: tuple[int, int] = (120, 120)) -> Image.Image:
    """Create a high-quality square thumbnail from a PIL image.

    Args:
        image: Original PIL Image.
        size: Target thumbnail dimensions.

    Returns:
        Thumbnail PIL Image.
    """
    thumb = image.copy()
    thumb.thumbnail(size, Image.Resampling.LANCZOS)
    return thumb


def init_session_state() -> None:
    """Initialize Streamlit session state keys if not already present."""
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "total_inferences" not in st.session_state:
        st.session_state["total_inferences"] = 0


def add_to_history(
    image: Image.Image,
    predictions: List[Any],
    source: str = "Upload",
    latency_ms: float = 0.0,
) -> None:
    """Add a classification record to the session history.

    Args:
        image: Original PIL Image analyzed.
        predictions: Top predictions list.
        source: Source type ('Upload', 'Camera', 'Sample').
        latency_ms: Inference execution time in milliseconds.
    """
    init_session_state()
    top_pred = predictions[0] if predictions else None
    top_label = (
        top_pred.label if hasattr(top_pred, "label") else top_pred.get("label", "Unknown")
        if top_pred
        else "Unknown"
    )
    top_pct = (
        top_pred.percentage
        if hasattr(top_pred, "percentage")
        else top_pred.get("percentage", "0.00%")
        if top_pred
        else "0.00%"
    )

    record = {
        "id": len(st.session_state["history"]) + 1,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "thumbnail": create_thumbnail(image),
        "source": source,
        "top_label": top_label,
        "top_pct": top_pct,
        "latency_ms": latency_ms,
        "predictions": [p.to_dict() if hasattr(p, "to_dict") else p for p in predictions],
    }

    st.session_state["history"].insert(0, record)
    st.session_state["total_inferences"] += 1


def clear_history() -> None:
    """Clear all session analysis history."""
    st.session_state["history"] = []
