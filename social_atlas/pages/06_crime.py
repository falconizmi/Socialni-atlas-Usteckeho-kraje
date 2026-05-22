import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from data.mock_data import ORPS, get_crime

ORP_COLORS = {
    "Most": "#E24B4A", "Chomutov": "#EF9F27", "Ústí nad Labem": "#378ADD",
    "Teplice": "#7F77DD", "Děčín": "#1D9E75", "Litoměřice": "#639922", "Louny": "#888780",
}

st.set_page_config(layout="wide")
st.title("🚔 Crime")
st.caption("Registered crimes per 1,000 residents by ORP municipality, including crime type breakdown.")


def filter_data(df):
    orps = st.session_state.get("filter_orp", ORPS)
    y_min, y_max = st.session_state.get("filter_years", (2015, 2024))
    return df[df["orp"].isin(orps) & (df["year"] >= y_min) & (df["year"] <= y_max)]


@st.cache_data
def load():
    return get_crime()


df = filter_data(load())
_, y_max = st.session_state.get("filter_years", (2020, 2024))

# ── Horizontal bar: crimes per 1000 ──────────────────────────────────────────
st.subheader(f"Crimes per 1,000 Residents ({y_max})")
latest = df[df["year"] == y_max].sort_values("crimes_per_1000")
if not latest.empty:
    fig_bar = go.Figure(go.Bar(
        x=latest["crimes_per_1000"], y=latest["orp"],
        orientation="h",
        marker_color=[ORP_COLORS.get(o, "#888") for o in latest["orp"]],
        text=latest["crimes_per_1000"].apply(lambda v: f"{v:.1f}"),
        textposition="outside",
    ))
    fig_bar.update_layout(
        xaxis_title="Crimes per 1,000", yaxis_title="",
        height=320, plot_bgcolor="white",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Stacked bar: property vs violent ──────────────────────────────────────────
st.subheader("Crime Type Breakdown by ORP")
latest2 = df[df["year"] == y_max].sort_values("crimes_per_1000", ascending=False)
if not latest2.empty:
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(
        name="Property Crimes",
        x=latest2["orp"], y=latest2["property_crimes"],
        marker_color="#378ADD",
    ))
    fig_stack.add_trace(go.Bar(
        name="Violent Crimes",
        x=latest2["orp"], y=latest2["violent_crimes"],
        marker_color="#E24B4A",
    ))
    fig_stack.update_layout(
        barmode="stack",
        yaxis_title="Crimes per 1,000", height=360, plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# ── Trend line ────────────────────────────────────────────────────────────────
st.subheader("Crime Rate Trend by ORP")
fig_trend = go.Figure()
for orp in df["orp"].unique():
    sub = df[df["orp"] == orp].sort_values("year")
    fig_trend.add_trace(go.Scatter(
        x=sub["year"], y=sub["crimes_per_1000"],
        name=orp, mode="lines+markers",
        line=dict(color=ORP_COLORS.get(orp, "#888"), width=2),
    ))
fig_trend.update_layout(
    yaxis_title="Crimes per 1,000", xaxis_title="Year",
    height=360, plot_bgcolor="white",
    legend=dict(orientation="h", y=-0.2),
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Data Table")
st.dataframe(df.sort_values(["year", "orp"]), use_container_width=True, hide_index=True)
st.download_button("⬇ Download CSV", df.to_csv(index=False).encode("utf-8"),
                   "crime.csv", "text/csv")
