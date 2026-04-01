# simulation/loader.py

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union, Dict, List

import pandas as pd

PathLike = Union[str, Path]

# --- ISO3 -> ISO2 mapping (extend as needed) ---
ISO3_TO_ISO2 = {
    "DEU": "DE",
    "DNK": "DK",
    "SWE": "SE",
    "NOR": "NO",
    "FIN": "FI",
    "FRA": "FR",
    "ESP": "ES",
    "ITA": "IT",
    "NLD": "NL",
    "BEL": "BE",
    "POL": "PL",
    "AUT": "AT",
    "CHE": "CH",
    "GBR": "GB",
    "IRL": "IE",
    "PRT": "PT",
    "CZE": "CZ",
    "HUN": "HU",
    "ROU": "RO",
    "BGR": "BG",
    "GRC": "GR",
}

def normalize_country(code: str) -> str:
    """Normalize ISO3->ISO2, keep ISO2, else uppercase string."""
    if code is None:
        return "UNKNOWN"
    s = str(code).strip().upper()
    if len(s) == 3 and s in ISO3_TO_ISO2:
        return ISO3_TO_ISO2[s]
    if len(s) == 2:
        return s
    return s


def _to_utc(ts: pd.Series) -> pd.Series:
    """
    Convert timestamps to tz-aware UTC.
    Column is 'Datetime (UTC)' so values are UTC but likely tz-naive. 
    """
    dt = pd.to_datetime(ts, errors="coerce")
    if getattr(dt.dt, "tz", None) is None:
        return dt.dt.tz_localize("UTC")
    return dt.dt.tz_convert("UTC")


# ----------------------------
# Read raw prices (multi-country)
# ----------------------------
def read_prices_raw(csv_path: PathLike) -> pd.DataFrame:
    """
    Reads the multi-country prices file with robust delimiter detection (tabs/commas).
    Expects header like:
      Country, ISO3 Code, Datetime (UTC), Datetime (Local), Price (EUR/MWhe)
    """
    csv_path = Path(csv_path)

    # auto-detect separator (tab-separated in your case)
    df = pd.read_csv(csv_path, sep=None, engine="python")

    required_cols = {"ISO3 Code", "Datetime (UTC)", "Price (EUR/MWhe)"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns {missing} in {csv_path}. Found: {list(df.columns)}")

    return df


# ----------------------------
# Country labels for Streamlit dropdown
# ----------------------------
def country_labels_from_prices(csv_path: PathLike) -> Dict[str, str]:
    """
    Returns ISO2 -> 'Country (ISO2)' using Country + ISO3 Code columns.
    """
    df = pd.read_csv(Path(csv_path), sep=None, engine="python", usecols=["Country", "ISO3 Code"])
    df["iso2"] = df["ISO3 Code"].astype(str).map(normalize_country)

    name_map = (
        df.dropna(subset=["iso2", "Country"])
          .groupby("iso2")["Country"]
          .first()
          .to_dict()
    )
    # If some iso2 has no country name, fall back to iso2
    labels = {iso2: f"{name} ({iso2})" for iso2, name in name_map.items()}
    for iso2 in sorted(set(df["iso2"].dropna())):
        labels.setdefault(iso2, iso2)
    return dict(sorted(labels.items()))


def list_available_countries_from_prices(csv_path: PathLike) -> List[str]:
    """Returns sorted list of ISO2 country codes present in file."""
    df = pd.read_csv(Path(csv_path), sep=None, engine="python", usecols=["ISO3 Code"])
    iso2 = df["ISO3 Code"].dropna().astype(str).map(normalize_country)
    return sorted(set(iso2))


# ----------------------------
# Public API: canonical prices loader (prices only)
# ----------------------------
def load_prices(
    csv_path: PathLike,
    country_iso2: str,
    start: Optional[Union[str, pd.Timestamp]] = None,
    end: Optional[Union[str, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """
    Returns canonical prices DataFrame with columns:
      timestamp_utc, country, price_DA_eur_mwh
    Filtered to one ISO2 country code.

    start: inclusive, end: exclusive
    """
    df = read_prices_raw(csv_path)

    df["country"] = df["ISO3 Code"].astype(str).map(normalize_country)
    cc = normalize_country(country_iso2)
    df = df[df["country"] == cc].copy()

    df["timestamp_utc"] = _to_utc(df["Datetime (UTC)"])
    df["price_DA_eur_mwh"] = pd.to_numeric(df["Price (EUR/MWhe)"], errors="coerce")

    out = df[["timestamp_utc", "country", "price_DA_eur_mwh"]].dropna()
    out = out.sort_values("timestamp_utc")

    if start is not None:
        s = pd.to_datetime(start)
        s = s.tz_localize("UTC") if s.tzinfo is None else s.tz_convert("UTC")
        out = out[out["timestamp_utc"] >= s]
    if end is not None:
        e = pd.to_datetime(end)
        e = e.tz_localize("UTC") if e.tzinfo is None else e.tz_convert("UTC")
        out = out[out["timestamp_utc"] < e]

    # Deduplicate same hour just in case
    out = (
        out.groupby(["timestamp_utc", "country"], as_index=False)["price_DA_eur_mwh"]
           .mean()
           .sort_values("timestamp_utc")
           .reset_index(drop=True)
    )

    return out