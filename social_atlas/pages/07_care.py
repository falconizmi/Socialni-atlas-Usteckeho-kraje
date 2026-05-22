import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from data.mock_data import ORPS, get_care

ORP_COLORS = {
    "Most": "#E24B4A", "Chomutov": "#EF9F27", "Ústí nad Labem": "#378ADD",
    "Teplice": "#7F77DD", "Děčín": "#1D9E75", "Litoměřice": "#639922", "Louny": "#888780",
}
RATING_ICON = {"OK": "✅", "Sufficient": "🟡", "Deficit": "🔴"}
RATING_BG = {"OK": "#d4edda", "Sufficient": "#fff3cd", "Deficit": "#ffd7d7"}

st.set_page_config(layout="wide")
st.title("🏥 Social & Healthcare Care")
st.caption("Availability of GPs, psychiatrists, social workers, and shelters by ORP municipality.")


@st.cache_data
def load():
    return get_care()


df = load()
selected_orps = st.session_state.get("filter_orp", ORPS)
df = df[df["orp"].isin(selected_orps)]

# ── Styled availability table ─────────────────────────────────────────────────
st.subheader("Care Availability Summary")
display = df.copy()
display["rating"] = display["rating"].map(lambda r: f"{RATING_ICON.get(r, '')} {r}")

def row_style(row):
    raw = row["rating"].split(" ", 1)[-1].strip()
    bg = RATING_BG.get(raw, "white")
    return [f"background-color: {bg}"] * len(row)

col_labels = {
    "orp": "ORP", "gp_per_1000": "GPs/1000",
    "psychiatrists_per_1000": "Psychiatrists/1000",
    "social_workers": "Social Workers", "shelters": "Shelters", "rating": "Rating",
}
display = display.rename(columns=col_labels)
st.dataframe(
    display.style.apply(row_style, axis=1),
    use_container_width=True, hide_index=True,
)

# ── Radar chart ───────────────────────────────────────────────────────────────
st.subheader("Care Radar — All ORP Dimensions")

categories = ["GPs/1000", "Psychiatrists/1000", "Social Workers", "Shelters"]
max_vals = {
    "gp_per_1000": 1.0, "psychiatrists_per_1000": 0.15,
    "social_workers": 35.0, "shelters": 6.0,
}

fig_radar = go.Figure()
for _, row in df.iterrows():
    vals_norm = [
        row["gp_per_1000"] / max_vals["gp_per_1000"],
        row["psychiatrists_per_1000"] / max_vals["psychiatrists_per_1000"],
        row["social_workers"] / max_vals["social_workers"],
        row["shelters"] / max_vals["shelters"],
    ]
    vals_norm += [vals_norm[0]]
    cats = categories + [categories[0]]
    fig_radar.add_trace(go.Scatterpolar(
        r=vals_norm, theta=cats,
        fill="toself", name=row["orp"],
        line=dict(color=ORP_COLORS.get(row["orp"], "#888")),
        opacity=0.7,
    ))

fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
    showlegend=True,
    height=480,
    legend=dict(orientation="h", y=-0.1),
    title="Care Dimensions (normalized 0–1)",
)
st.plotly_chart(fig_radar, use_container_width=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.download_button("⬇ Download CSV", df.to_csv(index=False).encode("utf-8"),
                   "care.csv", "text/csv")
