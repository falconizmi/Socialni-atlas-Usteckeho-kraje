import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from data.mock_data import ORPS, get_debt_enforcement, get_unemployment, get_demographics

ORP_COLORS = {
    "Most": "#E24B4A", "Chomutov": "#EF9F27", "Ústí nad Labem": "#378ADD",
    "Teplice": "#7F77DD", "Děčín": "#1D9E75", "Litoměřice": "#639922", "Louny": "#888780",
}

st.set_page_config(layout="wide")
st.title("⚖️ Debt Enforcement")
st.caption("Share of residents subject to debt enforcement proceedings (exekuce) by ORP municipality.")


def filter_data(df):
    orps = st.session_state.get("filter_orp", ORPS)
    y_min, y_max = st.session_state.get("filter_years", (2015, 2024))
    result = df.copy()
    if "orp" in result.columns:
        result = result[result["orp"].isin(orps)]
    if "year" in result.columns:
        result = result[(result["year"] >= y_min) & (result["year"] <= y_max)]
    return result


@st.cache_data
def load():
    return get_debt_enforcement(), get_unemployment(), get_demographics()


debt, unemp, demo = load()
debt_f = filter_data(debt)
unemp_f = filter_data(unemp)

# ── Line chart ────────────────────────────────────────────────────────────────
st.subheader("Trend 2015–2024 by ORP")
fig_line = go.Figure()
for orp in debt_f["orp"].unique():
    sub = debt_f[debt_f["orp"] == orp].sort_values("year")
    fig_line.add_trace(go.Scatter(
        x=sub["year"], y=sub["share_of_population"],
        name=orp, mode="lines+markers",
        line=dict(color=ORP_COLORS.get(orp, "#888"), width=2),
    ))
fig_line.update_layout(
    yaxis_title="Debt Enforcement (%)", xaxis_title="Year",
    height=360, plot_bgcolor="white",
    legend=dict(orientation="h", y=-0.2),
)
st.plotly_chart(fig_line, use_container_width=True)

# ── Heatmap ───────────────────────────────────────────────────────────────────
st.subheader("Heatmap: ORP × Year")
pivot = debt_f.pivot_table(index="orp", columns="year", values="share_of_population")
fig_heat = px.imshow(pivot, color_continuous_scale="Reds", aspect="auto",
                     labels={"color": "Debt Enforcement (%)"}, text_auto=".1f")
fig_heat.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig_heat, use_container_width=True)

# ── Scatter: debt vs unemployment ─────────────────────────────────────────────
st.subheader("Correlation: Debt Enforcement vs. Unemployment")
_, y_max = st.session_state.get("filter_years", (2020, 2024))
debt_yr = debt_f[debt_f["year"] == y_max][["orp", "share_of_population"]]
unemp_yr = unemp_f[unemp_f["year"] == y_max][["orp", "value"]]
demo_yr = filter_data(demo)
demo_yr = demo_yr[demo_yr["year"] == y_max][["orp", "population"]]
merged = debt_yr.merge(unemp_yr, on="orp").merge(demo_yr, on="orp", how="left")

fig_scatter = px.scatter(
    merged, x="value", y="share_of_population",
    size="population", color="orp",
    color_discrete_map=ORP_COLORS,
    hover_name="orp",
    labels={"value": "Unemployment (%)", "share_of_population": "Debt Enforcement (%)"},
    size_max=50,
    title=f"Debt vs. Unemployment ({y_max}) — bubble size = population",
)
fig_scatter.update_layout(height=400, plot_bgcolor="white")
st.plotly_chart(fig_scatter, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("Data Table")
st.dataframe(debt_f.sort_values(["year", "orp"]), use_container_width=True, hide_index=True)
st.download_button("⬇ Download CSV", debt_f.to_csv(index=False).encode("utf-8"),
                   "debt_enforcement.csv", "text/csv")
