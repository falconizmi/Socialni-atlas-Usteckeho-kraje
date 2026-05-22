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


def unemployment_bar(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("value", ascending=True)
    colors = [
        "#E24B4A" if v > 10 else ("#EF9F27" if v >= 6 else "#1D9E75")
        for v in df["value"]
    ]
    fig = go.Figure(go.Bar(
        x=df["value"], y=df["orp"],
        orientation="h",
        marker_color=colors,
        text=df["value"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    fig.update_layout(
        title="Unemployment by ORP (%)",
        xaxis_title="Unemployment (%)",
        yaxis_title="",
        height=320,
        margin=dict(l=10, r=40, t=40, b=10),
        plot_bgcolor="white",
    )
    return fig
