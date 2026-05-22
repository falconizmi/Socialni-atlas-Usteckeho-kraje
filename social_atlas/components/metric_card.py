import streamlit as st


def metric_card(label: str, value: str, delta: str | None = None, inverse: bool = False):
    delta_color = "inverse" if inverse else "normal"
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)
