import plotly.graph_objects as go
import pandas as pd

ORP_COLORS = {
    "Most":             "#E24B4A",
    "Chomutov":         "#EF9F27",
    "Ústí nad Labem":   "#378ADD",
    "Teplice":          "#7F77DD",
    "Děčín":            "#1D9E75",
    "Litoměřice":       "#639922",
    "Louny":            "#888780",
}


def dual_trend(unemp_df: pd.DataFrame, debt_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    for orp in unemp_df["orp"].unique():
        sub = unemp_df[unemp_df["orp"] == orp]
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["value"],
            name=f"{orp} — Unemployment",
            line=dict(color=ORP_COLORS.get(orp, "#888"), width=2),
            yaxis="y1",
        ))

    for orp in debt_df["orp"].unique():
        sub = debt_df[debt_df["orp"] == orp]
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["share_of_population"],
            name=f"{orp} — Debt",
            line=dict(color=ORP_COLORS.get(orp, "#888"), width=2, dash="dot"),
            yaxis="y2",
        ))

    fig.update_layout(
        title="Unemployment (solid) vs. Debt Enforcement (dotted) Trends",
        yaxis=dict(title="Unemployment (%)", side="left"),
        yaxis2=dict(title="Debt Enforcement (%)", side="right", overlaying="y"),
        height=380,
        legend=dict(orientation="h", y=-0.25),
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="white",
    )
    return fig
