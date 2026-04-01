# simulation/forecast.py

import numpy as np
import pandas as pd


def apply_forecast_error(actual_series, forecast_error_level=0.15):
    """
    Create a forecast series from actual values by applying
    multiplicative noise controlled by forecast_error_level.
    
    forecast_error_level = 0.15 -> 15% std dev.
    """
    noise = np.random.normal(0, forecast_error_level, len(actual_series))
    forecast_values = actual_series.values * (1 + noise)
    return pd.Series(forecast_values, index=actual_series.index, name=actual_series.name + "_forecast")


def add_net_forecast_column(df, forecast_error_level=0.15):
    """
    Given a DataFrame with 'net_actual', create 'net_forecast'
    based on forecast_error_level and return updated DataFrame.
    """
    if "net_actual" not in df.columns:
        raise ValueError("DataFrame must contain 'net_actual' column.")

    net_forecast = apply_forecast_error(df["net_actual"], forecast_error_level=forecast_error_level)
    df = df.copy()
    df["net_forecast"] = net_forecast
    return df