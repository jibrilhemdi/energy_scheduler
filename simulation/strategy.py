# simulation/strategy.py

import pandas as pd


def alpha_strategy(net_forecast_series, alpha=0.7):
    """
    Commit a fraction alpha of the forecast net position to the day-ahead market.
    
    q_DA_t = alpha * net_forecast_t
    """
    q_da = alpha * net_forecast_series
    return pd.Series(q_da, index=net_forecast_series.index, name="q_DA")


def add_commitment_column(df, alpha=0.7):
    """
    Given a DataFrame with 'net_forecast', add 'q_DA' column using alpha strategy.
    """
    if "net_forecast" not in df.columns:
        raise ValueError("DataFrame must contain 'net_forecast' column.")

    q_DA = alpha_strategy(df["net_forecast"], alpha=alpha)
    df = df.copy()
    df["q_DA"] = q_DA
    return df