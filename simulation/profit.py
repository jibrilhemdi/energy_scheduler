# simulation/profit.py

import pandas as pd


def compute_imbalance(df):
    """
    Compute imbalance = net_actual - q_DA.
    Adds 'imbalance' column.
    """
    if "net_actual" not in df.columns or "q_DA" not in df.columns:
        raise ValueError("DataFrame must contain 'net_actual' and 'q_DA' columns.")

    df = df.copy()
    df["imbalance"] = df["net_actual"] - df["q_DA"]
    return df


def compute_profit(df):
    """
    Compute hourly profit:
      profit_DA = q_DA * price_DA
      profit_ID = imbalance * price_ID
      profit_total = profit_DA + profit_ID

    Returns updated DataFrame and total_profit (scalar).
    """
    required_cols = ["q_DA", "price_DA", "imbalance", "price_ID"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")

    df = df.copy()
    df["profit_DA"] = df["q_DA"] * df["price_DA"]
    df["profit_ID"] = df["imbalance"] * df["price_ID"]
    df["profit_total"] = df["profit_DA"] + df["profit_ID"]

    total_profit = df["profit_total"].sum()
    return df, total_profit