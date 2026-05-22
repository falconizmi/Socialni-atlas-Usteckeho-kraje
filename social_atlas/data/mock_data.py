import numpy as np
import pandas as pd

ORPS = ["Most", "Chomutov", "Ústí nad Labem", "Teplice", "Děčín", "Litoměřice", "Louny"]
YEARS = list(range(2015, 2025))

rng = np.random.default_rng(42)


def _jitter(arr, scale=0.3):
    return arr + rng.normal(0, scale, size=arr.shape)


def get_unemployment() -> pd.DataFrame:
    base = {"Most": 14.0, "Chomutov": 11.5, "Ústí nad Labem": 10.0,
            "Teplice": 9.0, "Děčín": 8.5, "Litoměřice": 5.5, "Louny": 4.0}
    trend = np.array([-0.5, -0.6, -0.7, -0.8, -0.6, 1.8, -0.9, -0.6, -0.4, 0.3])
    rows = []
    for orp, b in base.items():
        vals = b + np.cumsum(trend) - np.cumsum(trend)[0]
        vals = _jitter(vals, 0.25)
        vals = np.clip(vals, 1.5, 20.0)
        for y, v in zip(YEARS, vals):
            rows.append({"year": y, "orp": orp, "value": round(float(v), 2)})
    return pd.DataFrame(rows)


def get_debt_enforcement() -> pd.DataFrame:
    base = {"Most": 20.0, "Chomutov": 17.5, "Ústí nad Labem": 15.0,
            "Teplice": 13.0, "Děčín": 11.0, "Litoměřice": 6.5, "Louny": 8.0}
    rows = []
    for orp, b in base.items():
        vals = np.linspace(b, b * 0.75, len(YEARS))
        vals = _jitter(vals, 0.2)
        vals = np.clip(vals, 1.0, 30.0)
        for y, v in zip(YEARS, vals):
            rows.append({"year": y, "orp": orp, "share_of_population": round(float(v), 2)})
    return pd.DataFrame(rows)


def get_housing_benefits() -> pd.DataFrame:
    base_recipients = {"Most": 4800, "Chomutov": 3900, "Ústí nad Labem": 3500,
                       "Teplice": 2800, "Děčín": 2200, "Litoměřice": 900, "Louny": 1100}
    base_share = {"Most": 12.5, "Chomutov": 10.8, "Ústí nad Labem": 9.2,
                  "Teplice": 8.1, "Děčín": 7.0, "Litoměřice": 3.2, "Louny": 4.1}
    rows = []
    for orp in ORPS:
        r_vals = np.linspace(base_recipients[orp], base_recipients[orp] * 0.85, len(YEARS))
        r_vals = np.round(_jitter(r_vals, 60)).astype(int)
        s_vals = np.linspace(base_share[orp], base_share[orp] * 0.85, len(YEARS))
        s_vals = np.round(_jitter(s_vals, 0.2), 2)
        for y, r, s in zip(YEARS, r_vals, s_vals):
            rows.append({"year": y, "orp": orp,
                         "num_recipients": int(r),
                         "share_of_households": round(float(s), 2)})
    return pd.DataFrame(rows)


def get_demographics() -> pd.DataFrame:
    pop0 = {"Most": 67000, "Chomutov": 49000, "Ústí nad Labem": 92000,
            "Teplice": 77000, "Děčín": 47000, "Litoměřice": 55000, "Louny": 42000}
    rows = []
    for orp in ORPS:
        pop = pop0[orp]
        is_lito = orp == "Litoměřice"
        for y in YEARS:
            births = int(rng.integers(320, 480) if not is_lito else rng.integers(350, 500))
            deaths = int(rng.integers(380, 520))
            immigrants = int(rng.integers(200, 450))
            emigrants = int(rng.integers(300, 600) if orp == "Most" else rng.integers(250, 500))
            change = births - deaths + immigrants - emigrants
            pop = max(pop + change, 20000)
            rows.append({"year": y, "orp": orp, "population": pop,
                         "births": births, "deaths": deaths,
                         "immigrants": immigrants, "emigrants": emigrants})
    return pd.DataFrame(rows)


def get_excluded_localities() -> pd.DataFrame:
    data = [
        ("Chanov", "Most", 1850, "Critical", 50.5423, 13.6391),
        ("Předlice", "Ústí nad Labem", 1200, "Critical", 50.6712, 14.0189),
        ("Písečná", "Děčín", 620, "Moderate", 50.7890, 14.2045),
        ("Janov", "Litoměřice", 480, "Moderate", 50.5234, 14.1234),
        ("Záluží", "Most", 390, "Moderate", 50.5012, 13.7012),
        ("Ervěnice", "Most", 310, "Moderate", 50.5145, 13.6890),
        ("Křimov", "Chomutov", 270, "Monitored", 50.5345, 13.4023),
        ("Celná", "Děčín", 230, "Monitored", 50.8234, 14.3456),
        ("Oldřichov", "Chomutov", 410, "Critical", 50.4923, 13.4512),
        ("Střimice", "Most", 560, "Moderate", 50.5278, 13.6745),
        ("Trmice", "Ústí nad Labem", 320, "Monitored", 50.6234, 14.0512),
        ("Soběsuky", "Chomutov", 180, "Monitored", 50.4512, 13.4890),
    ]
    return pd.DataFrame(data, columns=["name", "orp", "num_residents", "severity", "lat", "lon"])


def get_crime() -> pd.DataFrame:
    base_rate = {"Most": 28.0, "Chomutov": 24.0, "Ústí nad Labem": 30.0,
                 "Teplice": 22.0, "Děčín": 19.0, "Litoměřice": 14.0, "Louny": 12.0}
    rows = []
    for orp in ORPS:
        b = base_rate[orp]
        rates = np.linspace(b, b * 0.88, len(YEARS))
        rates = _jitter(rates, 0.5)
        for y, rate in zip(YEARS, rates):
            prop = rate * rng.uniform(0.65, 0.75)
            viol = rate * rng.uniform(0.12, 0.20)
            rows.append({"year": y, "orp": orp,
                         "crimes_per_1000": round(float(rate), 2),
                         "property_crimes": round(float(prop), 2),
                         "violent_crimes": round(float(viol), 2)})
    return pd.DataFrame(rows)


def get_care() -> pd.DataFrame:
    data = [
        ("Most",           0.52, 0.04, 18, 3, "Deficit"),
        ("Chomutov",       0.61, 0.05, 14, 2, "Deficit"),
        ("Ústí nad Labem", 0.78, 0.09, 31, 5, "Sufficient"),
        ("Teplice",        0.67, 0.06, 22, 3, "Sufficient"),
        ("Děčín",          0.55, 0.04, 12, 2, "Deficit"),
        ("Litoměřice",     0.82, 0.11, 19, 4, "OK"),
        ("Louny",          0.71, 0.07, 11, 2, "Sufficient"),
    ]
    return pd.DataFrame(data, columns=[
        "orp", "gp_per_1000", "psychiatrists_per_1000",
        "social_workers", "shelters", "rating"
    ])
