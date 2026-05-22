import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from data.mock_data import ORPS, get_demographics

ORP_COLORS = {
    "Most": "#E24B4A", "Chomutov": "#EF9F27", "Ústí nad Labem": "#378ADD",
    "Teplice": "#7F77DD", "Děčín": "#1D9E75", "Litoměřice": "#639922", "Louny": "#888780",
}

st.set_page_config(layout="wide")
st.title("👥 Demographics")
st.caption("Population trends, natural increase, and migration balance by ORP municipality.")


def filter_data(df):
    orps = st.session_state.get("filter_orp", ORPS)
    y_min, y_max = st.session_state.get("filter_years", (2015, 2024))
    return df[df["orp"].isin(orps) & (df["year"] >= y_min) & (df["year"] <= y_max)]


@st.cache_data
def load():
    return get_demographics()


df = filter_data(load())
y_min, y_max = st.session_state.get("filter_years", (2020, 2024))
selected_orps = st.session_state.get("filter_orp", ORPS)

# ── Population trend line chart ───────────────────────────────────────────────
st.subheader("Population Trend by ORP")
fig_pop = go.Figure()
for orp in df["orp"].unique():
    sub = df[df["orp"] == orp].sort_values("year")
    fig_pop.add_trace(go.Scatter(
        x=sub["year"], y=sub["population"],
        name=orp, mode="lines+markers",
        line=dict(color=ORP_COLORS.get(orp, "#888"), width=2),
    ))
fig_pop.update_layout(
    yaxis_title="Population", xaxis_title="Year",
    height=380, plot_bgcolor="white",
    legend=dict(orientation="h", y=-0.2),
)
st.plotly_chart(fig_pop, use_container_width=True)

# ── Waterfall chart ───────────────────────────────────────────────────────────
st.subheader(f"Population Change Components ({y_min}–{y_max})")
orp_sel = st.selectbox("Select ORP", [o for o in ORPS if o in selected_orps])
sub = df[df["orp"] == orp_sel]
if not sub.empty:
    natural = int(sub["births"].sum() - sub["deaths"].sum())
    migration = int(sub["immigrants"].sum() - sub["emigrants"].sum())
    total = natural + migration
    start_pop = int(df[(df["orp"] == orp_sel) & (df["year"] == y_min)]["population"].values[0]) if not df[(df["orp"] == orp_sel) & (df["year"] == y_min)].empty else 0

    fig_wf = go.Figure(go.Waterfall(
        name="Change",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Base Population", "Natural Increase", "Net Migration", "End Population"],
        y=[start_pop, natural, migration, 0],
        connector={"line": {"color": "gray"}},
        decreasing={"marker": {"color": "#E24B4A"}},
        increasing={"marker": {"color": "#1D9E75"}},
        totals={"marker": {"color": "#378ADD"}},
        text=[f"{start_pop:,}", f"{natural:+,}", f"{migration:+,}", f"{start_pop + total:,}"],
        textposition="outside",
    ))
    fig_wf.update_layout(height=380, plot_bgcolor="white",
                         title=f"Population Change in {orp_sel}")
    st.plotly_chart(fig_wf, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Data Table")
st.dataframe(df.sort_values(["year", "orp"]), use_container_width=True, hide_index=True)
st.download_button("⬇ Download CSV", df.to_csv(index=False).encode("utf-8"),
                   "demographics.csv", "text/csv")
