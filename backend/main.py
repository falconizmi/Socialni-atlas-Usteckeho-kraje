from fastapi import FastAPI
import requests
import pandas as pd

app = FastAPI()



@app.get("/template")
def get_data():
    url = "odkaz na json"

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data)

    ustecky = df[df["kraj"] == "Ústecký kraj"] # zobrazit jen kde v jsonu je kraj: Ústecký kraj

    return ustecky.to_dict(orient="records")

@app.get("/nezamestnanost")
def get_data():
    url = "https://data.mpsv.cz/portal/api/reports/by-table/evid_pno_up_agr_frz_odata_vp/data/json"

    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data)

    ustecky = df[df["kraj"] == "Ústecký kraj"]

    return ustecky.to_dict(orient="records")