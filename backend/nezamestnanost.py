# nezamestnanost.py
from fastapi import APIRouter
import pandas as pd
from store import data_cache

# Místo 'app' vytvoříme 'router'
router = APIRouter()

@router.get("/nezamestnanost")
def get_nezamestnanost():
    # Zkontrolujeme, jestli se data už načetla do cache z main.py
    if "nezamestnanost" not in data_cache:
        return {"error": "Data is loading..."}
        
    df = data_cache["nezamestnanost"].copy()
    
    if "kraj" in df.columns:
        df = df[df["kraj"] == "Ústecký kraj"]

    df["year"] = pd.to_datetime(df["rozhodne_datum"]).dt.year
    df = df.rename(columns={"okres": "orp", "uchazec_pohlavi": "gender"})
    
    grouped = df.groupby(["year", "orp", "gender"]).agg(
        total_uchazeci=("pocet_uchazeci_dosazitelni", "sum"),
        total_obyvatel=("pocet_obyvatel_vek_15_64", "sum")
    ).reset_index()
    
    grouped["value"] = (grouped["total_uchazeci"] / grouped["total_obyvatel"]) * 100
    grouped["value"] = grouped["value"].round(2)

    final_df = grouped[["year", "orp", "gender", "value"]] 

    return final_df.to_dict(orient="records")