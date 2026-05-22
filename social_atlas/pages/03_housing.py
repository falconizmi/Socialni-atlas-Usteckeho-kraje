import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from data.mock_data import ORPS, get_housing_benefits

ORP_COLORS = {
    "Most": "#E24B4A", "Chomutov": "#EF9F27", "Ústí nad Labem": "#378ADD",
    "Teplice": "#7F77DD", "Děčín": "#1D9E75", "Litoměřice": "#639922", "Louny": "#888780",
}

st.set_page_config(layout="wide")
st.title("🏠 Housing Benefits")
st.caption("Number of housing benefit (příspěvek na bydlení) recipients and their share of households by ORP.")


def filter_data(df):
    orps = st.session_state.get("filter_orp", ORPS)
    y_min, y_max = st.session_state.get("filter_years", (2015, 2024))
    return df[df["orp"].isin(orps) & (df["year"] >= y_min) & (df["year"] <= y_max)]


@st.cache_data
def load():
    return get_housing_benefits()


df = filter_data(load())

view = st.radio("View", ["Number of Recipients", "Share of Households (%)"], horizontal=True)
col_y = "num_recipients" if "Recipients" in view else "share_of_households"
y_label = "Recipients" if "Recipients" in view else "Share of Households (%)"

# ── Stacked bar ───────────────────────────────────────────────────────────────
st.subheader(f"Housing Benefits by ORP and Year — {view}")
orps_present = df["orp"].unique()
years_present = sorted(df["year"].unique())
fig = go.Figure()
for orp in orps_present:
    sub = df[df["orp"] == orp].sort_values("year")
    fig.add_trace(go.Bar(
        x=sub["year"], y=sub[col_y],
        name=orp,
        marker_color=ORP_COLORS.get(orp, "#888"),
    ))
fig.update_layout(
    barmode="stack",
    xaxis_title="Year", yaxis_title=y_label,
    height=400, plot_bgcolor="white",
    legend=dict(orientation="h", y=-0.2),
)
st.plotly_chart(fig, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Data Table")
st.dataframe(df.sort_values(["year", "orp"]), use_container_width=True, hide_index=True)
st.download_button("⬇ Download CSV", df.to_csv(index=False).encode("utf-8"),
                   "housing_benefits.csv", "text/csv")
