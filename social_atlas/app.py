import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd

from data.mock_data import (
    ORPS, YEARS,
    get_unemployment, get_debt_enforcement, get_housing_benefits,
    get_demographics, get_excluded_localities, get_crime, get_care,
)
from components.bar_chart_orp import unemployment_bar
from components.trend_chart import dual_trend
from components.export import export_csv, export_excel

st.set_page_config(layout="wide", page_title="Social Atlas — Ústecký Region")

st.markdown("""
<style>
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
    }
    .stDataFrame { font-size: 13px; }
    [data-testid="stSidebar"] { background-color: #f1f3f5; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.title("Filters")
st.sidebar.multiselect("Municipality (ORP)", ORPS, default=ORPS, key="filter_orp")
st.sidebar.slider("Time range", 2015, 2024, (2020, 2024), key="filter_years")

st.sidebar.markdown("---")
st.sidebar.markdown("### Export")


def filter_data(df: pd.DataFrame) -> pd.DataFrame:
    orps = st.session_state.get("filter_orp", ORPS)
    y_min, y_max = st.session_state.get("filter_years", (2015, 2024))
    result = df.copy()
    if "orp" in result.columns:
        result = result[result["orp"].isin(orps)]
    if "year" in result.columns:
        result = result[(result["year"] >= y_min) & (result["year"] <= y_max)]
    return result


@st.cache_data
def load_all():
    return {
        "unemployment": get_unemployment(),
        "debt": get_debt_enforcement(),
        "housing": get_housing_benefits(),
        "demographics": get_demographics(),
        "localities": get_excluded_localities(),
        "crime": get_crime(),
        "care": get_care(),
    }


data = load_all()

# Export buttons
export_csv(filter_data(data["unemployment"]), "unemployment")
export_excel({
    "Unemployment": filter_data(data["unemployment"]),
    "Debt Enforcement": filter_data(data["debt"]),
    "Housing Benefits": filter_data(data["housing"]),
    "Demographics": filter_data(data["demographics"]),
    "Crime": filter_data(data["crime"]),
    "Care": data["care"],
}, "social_atlas")

# ── Overview page ─────────────────────────────────────────────────────────────
st.title("Social Atlas of the Ústecký Region")
st.caption("Overview dashboard — use the sidebar to filter by ORP and time range.")

_, y_max = st.session_state.get("filter_years", (2020, 2024))
selected_orps = st.session_state.get("filter_orp", ORPS)

unemp = filter_data(data["unemployment"])
debt = filter_data(data["debt"])
housing = filter_data(data["housing"])
demo = filter_data(data["demographics"])
crime = filter_data(data["crime"])


def _region_avg(df, col, year):
    sub = df[df["year"] == year]
    return sub[col].mean() if not sub.empty else 0.0


def _delta(df, col, year):
    curr = _region_avg(df, col, year)
    prev = _region_avg(df, col, year - 1)
    return curr - prev


# ── Row 1 — KPI cards ─────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    v = _region_avg(unemp, "value", y_max)
    d = _delta(unemp, "value", y_max)
    st.metric("Unemployment", f"{v:.1f}%", f"{d:+.2f}pp", delta_color="inverse")

with c2:
    v = _region_avg(debt, "share_of_population", y_max)
    d = _delta(debt, "share_of_population", y_max)
    st.metric("Debt Enforcement", f"{v:.1f}%", f"{d:+.2f}pp", delta_color="inverse")

with c3:
    sub = housing[housing["year"] == y_max]
    v = int(sub["num_recipients"].sum()) if not sub.empty else 0
    sub_prev = housing[housing["year"] == y_max - 1]
    d = v - int(sub_prev["num_recipients"].sum()) if not sub_prev.empty else 0
    st.metric("Housing Benefit Recipients", f"{v:,}", f"{d:+,}", delta_color="inverse")

with c4:
    sub = demo[demo["year"] == y_max]
    v = sub["population"].sum() / 1000 if not sub.empty else 0
    sub_prev = demo[demo["year"] == y_max - 1]
    d = (v - sub_prev["population"].sum() / 1000) if not sub_prev.empty else 0
    st.metric("Population (thousands)", f"{v:,.1f}k", f"{d:+.1f}k", delta_color="inverse")

with c5:
    v = _region_avg(crime, "crimes_per_1000", y_max)
    d = _delta(crime, "crimes_per_1000", y_max)
    st.metric("Crime Rate (‰)", f"{v:.1f}", f"{d:+.2f}", delta_color="inverse")

# ── Row 2 ─────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    unemp_latest = unemp[unemp["year"] == y_max]
    if not unemp_latest.empty:
        st.plotly_chart(unemployment_bar(unemp_latest), use_container_width=True)

with col_right:
    st.subheader("Socially Excluded Localities")
    locs = data["localities"]
    if selected_orps:
        locs = locs[locs["orp"].isin(selected_orps)]

    severity_colors = {"Critical": "🔴", "Moderate": "🟠", "Monitored": "🟢"}
    display = locs[["name", "orp", "num_residents", "severity"]].copy()
    display["severity"] = display["severity"].map(lambda s: f"{severity_colors.get(s, '')} {s}")
    st.dataframe(display, use_container_width=True, hide_index=True)

# ── Row 3 ─────────────────────────────────────────────────────────────────────
col_trend, col_care = st.columns([13, 7])

with col_trend:
    st.plotly_chart(dual_trend(unemp, debt), use_container_width=True)

with col_care:
    st.subheader("Care Availability by ORP")
    care = data["care"]
    if selected_orps:
        care = care[care["orp"].isin(selected_orps)]
    rating_icon = {"OK": "✅", "Sufficient": "🟡", "Deficit": "🔴"}
    care_display = care.copy()
    care_display["rating"] = care_display["rating"].map(lambda r: f"{rating_icon.get(r, '')} {r}")
    st.dataframe(care_display, use_container_width=True, hide_index=True)
