# main.py
from fastapi import FastAPI
import pandas as pd
import json
import os
from store import data_cache
import nezamestnanost
import vylouceni

app = FastAPI()
app.include_router(nezamestnanost.router)
app.include_router(vylouceni.router)

@app.on_event("startup")
def load_data_on_startup():
    print("STARTUP: Načítám předpřipravená data z lokálního disku...")

    # ── Nezaměstnanost (JSON) ────────────────────────────────────────────────
    nez_path = "ustecky_nezamestnanost.json"
    if not os.path.exists(nez_path):
        print(f"CRITICAL ERROR: Soubor '{nez_path}' nebyl nalezen!")
    else:
        try:
            with open(nez_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            if isinstance(records, dict) and "value" in records:
                records = records["value"]
            data_cache["nezamestnanost"] = pd.DataFrame(records)
            print(f"ÚSPĚCH: Načteno {len(data_cache['nezamestnanost'])} záznamů (nezaměstnanost).")
        except Exception as e:
            print(f"CRITICAL ERROR (nezaměstnanost): {e}")

    # ── Index sociálního vyloučení 2023 (XLSX) ───────────────────────────────
    vyl_path = "index_vylouceni.xlsx"
    if not os.path.exists(vyl_path):
        print(f"CRITICAL ERROR: Soubor '{vyl_path}' nebyl nalezen!")
    else:
        try:
            data_cache["vylouceni"] = pd.read_excel(
                vyl_path, sheet_name="Index soc. vyloučení 2023", header=0
            )
            print(f"ÚSPĚCH: Načteno {len(data_cache['vylouceni'])} záznamů (vyloučení).")
        except Exception as e:
            print(f"CRITICAL ERROR (vyloučení): {e}")
