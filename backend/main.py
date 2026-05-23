# main.py
from fastapi import FastAPI
import requests
import pandas as pd
import os

# Načteme prázdnou paměť a soubor s routou pro nezaměstnanost
from store import data_cache
import nezamestnanost 

app = FastAPI()

# 1. Tímto propojíme endpoint z nezamestnanost.py s hlavní aplikací
app.include_router(nezamestnanost.router)

# 2. Zde si definujete všechny URL adresy, které se mají stáhnout při startu
DATA_SOURCES = {
    "nezamestnanost": "nezamestnanost.json",
    # sem si kolega přidá další:
    # "exekuce": "https://url-na-data-o-exekucich.cz",
}

@app.on_event("startup")
def load_data_on_startup():
    """Spustí se JEN JEDNOU při startu backendu.

    Projede slovník DATA_SOURCES, načte lokální JSONy a uloží je do data_cache.
    """
    print("Loading local datasets... this might take a moment.")

    for name, file_path in DATA_SOURCES.items():
        try:
            # Kontrola, zda soubor vůbec existuje, aby kód nespadl s chybou
            if not os.path.exists(file_path):
                print(
                    f"CRITICAL ERROR: Soubor '{file_path}' nebyl nalezen ve složce projektu!"
                )
                continue

            # Načtení JSONu přímo do Pandas DataFrame
            # MPSV struktura má data vnořená pod klíčem "value", proto použijeme orient="records" přes json soubor
            df_raw = pd.read_json(file_path)

            # Ošetření struktury MPSV (data bývají pod klíčem 'value')
            if "value" in df_raw.columns or (
                isinstance(df_raw, pd.DataFrame) and "value" in df_raw.index
            ):
                # Pokud se JSON načetl jako objekt, kde 'value' je sloupec/klíč
                import json

                with open(file_path, "r", encoding="utf-8") as f:
                    data_json = json.load(f)
                records = data_json.get("value", data_json)
                data_cache[name] = pd.DataFrame(records)
            else:
                # Pokud je v JSONu rovnou čistý seznam
                data_cache[name] = df_raw

            print(
                f"Successfully loaded '{name}' from LOCAL FILE: {len(data_cache[name])} rows into memory!"
            )

        except Exception as e:
            print(f"CRITICAL ERROR loading data for '{name}' from file: {e}")