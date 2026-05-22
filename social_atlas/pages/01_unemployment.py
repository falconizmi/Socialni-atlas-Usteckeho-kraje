import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from data.mock_data import ORPS, YEARS, get_unemployment
from components.export import export_csv

ORP_COLORS = {
    "Most": "#E24B4A", "Chomutov": "#EF9F27", "Ústí nad Labem": "#378ADD",
    "Teplice": "#7F77DD", "Děčín": "#1D9E75", "Litoměřice": "#639922", "Louny": "#888780",
}

st.set_page_config(layout="wide")
st.title("📉 Unemployment")
st.caption("Share of unemployed persons out of the economically active population by ORP municipality.")


def filter_data(df):
    orps = st.session_state.get("filter_orp", ORPS)
    y_min, y_max = st.session_state.get("filter_years", (2015, 2024))
    return df[df["orp"].isin(orps) & (df["year"] >= y_min) & (df["year"] <= y_max)]


@st.cache_data
def load():
    return get_unemployment()


df = filter_data(load())

# ── Line chart ────────────────────────────────────────────────────────────────
st.subheader("Trend 2015–2024 by ORP")
fig_line = go.Figure()
for orp in df["orp"].unique():
    sub = df[df["orp"] == orp].sort_values("year")
    fig_line.add_trace(go.Scatter(
        x=sub["year"], y=sub["value"],
        name=orp,
        mode="lines+markers",
        line=dict(color=ORP_COLORS.get(orp, "#888"), width=2),
    ))
fig_line.update_layout(
    yaxis_title="Unemployment (%)", xaxis_title="Year",
    height=380, plot_bgcolor="white",
    legend=dict(orientation="h", y=-0.2),
)
st.plotly_chart(fig_line, use_container_width=True)

# ── Heatmap ───────────────────────────────────────────────────────────────────
st.subheader("Heatmap: ORP × Year")
pivot = df.pivot_table(index="orp", columns="year", values="value")
fig_heat = px.imshow(
    pivot,
    color_continuous_scale="RdYlGn_r",
    labels={"color": "Unemployment (%)"},
    aspect="auto",
    text_auto=".1f",
)
fig_heat.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig_heat, use_container_width=True)

# ── Table + export ────────────────────────────────────────────────────────────
st.subheader("Data Table")
st.dataframe(df.sort_values(["year", "orp"]), use_container_width=True, hide_index=True)
st.download_button(
    "⬇ Download CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="unemployment.csv",
    mime="text/csv",
)
