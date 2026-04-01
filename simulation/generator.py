# simulation/generator.py

import numpy as np
import pandas as pd


def generate_time_index(hours=24, freq="H"):
    """
    Create a DatetimeIndex for a single day.
    """
    # Base date is arbitrary
    start = "2024-01-01 00:00:00"
    return pd.date_range(start=start, periods=hours, freq=freq)


def generate_wind_profile(index, base=30, amplitude=10, noise_std=3.0):
    """
    Generate a simple synthetic wind production profile (MWh).
    """
    hours = np.arange(len(index))
    wind = base + amplitude * np.sin(2 * np.pi * hours / 24 + 0.5)
    wind += np.random.normal(0, noise_std, len(index))
    wind = np.clip(wind, 0, None)
    return pd.Series(wind, index=index, name="wind")


def generate_solar_profile(index, peak=50):
    """
    Generate a simple synthetic solar production profile (MWh).
    Zero at night, peak around midday.
    """
    hours = index.hour
    solar = np.maximum(0, peak * np.exp(-0.5 * ((hours - 12) / 4) ** 2))
    return pd.Series(solar, index=index, name="solar")


def generate_demand_profile(index, base=60):
    """
    Generate a synthetic demand profile (MWh).
    Morning + evening peaks using sinusoidal patterns.
    """
    hours = index.hour
    demand = base + 10 * np.sin(2 * np.pi * (hours - 7) / 24)
    demand += 5 * np.sin(4 * np.pi * (hours - 17) / 24)
    return pd.Series(demand, index=index, name="demand")


def generate_price_profiles(index, base=40, da_amp=15, da_noise=2, id_noise=5):
    """
    Generate synthetic day-ahead and intraday prices (EUR/MWh).
    """
    hours = index.hour

    price_DA = base + da_amp * np.sin(2 * np.pi * (hours - 7) / 24)
    price_DA += np.random.normal(0, da_noise, len(index))

    price_ID = price_DA + np.random.normal(0, id_noise, len(index))

    series_DA = pd.Series(price_DA, index=index, name="price_DA")
    series_ID = pd.Series(price_ID, index=index, name="price_ID")

    return series_DA, series_ID


def generate_scenario(hours=24):
    """
    Convenience function:
    Generate a full scenario: wind, solar, demand, prices, and net actual.
    Returns a DataFrame.
    """
    idx = generate_time_index(hours=hours)

    wind = generate_wind_profile(idx)
    solar = generate_solar_profile(idx)
    demand = generate_demand_profile(idx)
    price_DA, price_ID = generate_price_profiles(idx)

    df = pd.concat([wind, solar, demand, price_DA, price_ID], axis=1)
    df["net_actual"] = df["wind"] + df["solar"] - df["demand"]

    return df