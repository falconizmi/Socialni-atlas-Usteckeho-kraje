# exekuce.py
from fastapi import APIRouter
import pandas as pd
from store import data_cache

router = APIRouter()

EXEKUCE_METADATA = {
    "nazev_obce": "Název obce",
    "kod_obce_zuj": "Kód obce ZÚJ",
    "obvod_orp": "Kód obvodu obce s rozšířenou působností",
    "okres": "Okres",
    "kraj": "Kraj",
    "pocet_osob": "Počet fyzických osob v exekuci",
    "pocet_exekuci": "Počet vedených exekucí",
}


def _load_filtered_df() -> pd.DataFrame:
    df = data_cache["exekuce_obce"].copy()
    if "kraj" in df.columns:
        df = df[df["kraj"] == "Ústecký kraj"]
    for col in ("pocet_osob", "pocet_exekuci"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0
    return df


@router.get("/exekuce/metadata")
def get_metadata():
    return EXEKUCE_METADATA


@router.get("/exekuce")
def get_exekuce():
    if "exekuce_obce" not in data_cache:
        return {"error": "Data is loading..."}

    df = _load_filtered_df()

    grouped = df.groupby("okres", dropna=False).agg(
        people_in_enforcement=("pocet_osob", "sum"),
        num_enforcements=("pocet_exekuci", "sum"),
        num_municipalities=("nazev_obce", "count"),
    ).reset_index().rename(columns={"okres": "orp"})

    grouped["enforcements_per_person"] = (
        grouped["num_enforcements"] / grouped["people_in_enforcement"]
    ).fillna(0).round(2)

    grouped[["people_in_enforcement", "num_enforcements", "num_municipalities"]] = grouped[
        ["people_in_enforcement", "num_enforcements", "num_municipalities"]
    ].astype(int)

    return grouped.to_dict(orient="records")


@router.get("/exekuce/obce")
def get_exekuce_obce():
    if "exekuce_obce" not in data_cache:
        return {"error": "Data is loading..."}

    df = _load_filtered_df()
    df = df.sort_values("pocet_osob", ascending=False)
    cols = ["nazev_obce", "okres", "obvod_orp", "pocet_osob", "pocet_exekuci"]
    return df[[c for c in cols if c in df.columns]].to_dict(orient="records")
