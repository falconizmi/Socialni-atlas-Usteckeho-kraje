from fastapi import FastAPI
import requests
import pandas as pd

app = FastAPI()

# ---------------------------------------------------------
# 1. THE CACHE: Store the 100MB data in memory
# ---------------------------------------------------------
data_cache = {}

@app.on_event("startup")
def load_data_on_startup():
    """
    This runs exactly ONCE when the backend server boots up.
    It downloads the massive JSON so the API routes are lightning fast.
    """
    print("Fetching MPSV dataset... this might take a moment.")
    url = "https://data.mpsv.cz/portal/api/reports/by-table/evid_pno_up_agr_frz_odata_vp/data/json"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Load the JSON into Pandas and store it in our global cache
        data_cache["nezamestnanost"] = pd.DataFrame(response.json())
        print(f"Successfully loaded {len(data_cache['nezamestnanost'])} rows into memory!")
        
    except Exception as e:
        print(f"CRITICAL ERROR loading data: {e}")


# ---------------------------------------------------------
# 2. THE ENDPOINT: Fast serving and Data Bridging
# ---------------------------------------------------------
@app.get("/nezamestnanost")
def get_nezamestnanost():
    # Check if data actually loaded
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

# TEMPLATE for others
"""
@app.get("/template")
def get_template():
    ...
"""

# TEMPLATE for others
"""
@app.get("/template")
def get_data():
    url = "odkaz na json"

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data)

    ustecky = df[df["kraj"] == "Ústecký kraj"] # zobrazit jen kde v jsonu je kraj: Ústecký kraj

    return ustecky.to_dict(orient="records")
"""