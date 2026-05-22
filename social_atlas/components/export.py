import io
import streamlit as st
import pandas as pd


def export_csv(df: pd.DataFrame, filename: str):
    st.sidebar.download_button(
        label=f"⬇ CSV — {filename}",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{filename}.csv",
        mime="text/csv",
    )


def export_excel(dfs: dict, filename: str):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    st.sidebar.download_button(
        label="⬇ Excel (all data)",
        data=buffer.getvalue(),
        file_name=f"{filename}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
