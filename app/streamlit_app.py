# app/streamlit_app.py

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from simulation.loader import (
    load_prices,
    country_labels_from_prices,
    normalize_country,
)

# -------------------------
# Cache
# -------------------------
@st.cache_data(show_spinner=False)
def cached_labels(prices_path: str) -> dict:
    return country_labels_from_prices(prices_path)

@st.cache_data(show_spinner=False)
def cached_country_prices(prices_path: str, iso2: str) -> pd.DataFrame:
    # Load full history for this country once; slice by date later in-memory
    return load_prices(prices_path, iso2)

# -------------------------
# Simulation
# -------------------------
def make_forecast(actual: np.ndarray, forecast_error_level: float) -> np.ndarray:
    noise = np.random.normal(0.0, forecast_error_level, size=len(actual))
    return actual * (1.0 + noise)

def run_one(prices_da: np.ndarray, portfolio_mw: float, alpha: float, forecast_error_level: float, id_noise_std: float) -> float:
    """
    Positive MW = consumption (buying)
    """
    T = len(prices_da)
    actual = np.full(T, portfolio_mw, dtype=float)
    forecast = make_forecast(actual, forecast_error_level)

    q_DA = alpha * forecast
    price_ID = prices_da + np.random.normal(0.0, id_noise_std, size=T)

    imbalance = actual - q_DA
    profit = q_DA * prices_da + imbalance * price_ID
    return float(profit.sum())

def run_mc(prices_da: np.ndarray, portfolio_mw: float, alpha: float, forecast_error_level: float, n_sims: int, id_noise_std: float) -> pd.DataFrame:
    profits = [run_one(prices_da, portfolio_mw, alpha, forecast_error_level, id_noise_std) for _ in range(n_sims)]
    return pd.DataFrame({"total_profit": profits})


def main():
    st.title("Scheduling & Trading Simulator (Multi-country Ember prices)")

    prices_path = str(ROOT_DIR / "data" / "all_countries.csv")

    st.sidebar.header("Market")
    labels = cached_labels(prices_path)
    if not labels:
        st.error("No countries detected. Check data/all_countries.csv has 'Country' and 'ISO3 Code'.")
        st.stop()

    countries = list(labels.keys())
    default_index = countries.index("DE") if "DE" in countries else 0

    country = st.sidebar.selectbox(
        "Country",
        options=countries,
        index=default_index,
        format_func=lambda x: labels.get(x, x),
    )
    country = normalize_country(country)

    df_all = cached_country_prices(prices_path, country)
    if df_all.empty:
        st.error(f"No data for {country}")
        st.stop()

    min_ts = df_all["timestamp_utc"].min()
    max_ts = df_all["timestamp_utc"].max()
    st.sidebar.caption(f"Available (UTC): {min_ts.date()} → {max_ts.date()}")

    start_date = st.sidebar.date_input("Start date", value=min_ts.date())
    end_date = st.sidebar.date_input("End date (exclusive)", value=(min_ts + pd.Timedelta(days=1)).date())

    start_ts = pd.Timestamp(start_date).tz_localize("UTC")
    end_ts = pd.Timestamp(end_date).tz_localize("UTC")

    df = df_all[(df_all["timestamp_utc"] >= start_ts) & (df_all["timestamp_utc"] < end_ts)].copy()
    if df.empty:
        st.warning("No rows for this date range.")
        st.stop()

    st.sidebar.header("Portfolio & Strategy")
    portfolio_mw = st.sidebar.slider("Portfolio MW (+ = consumption)", -500.0, 500.0, 100.0, 10.0)
    alpha = st.sidebar.slider("Risk appetite α", 0.0, 1.0, 0.7, 0.05)
    forecast_error_level = st.sidebar.slider("Forecast error (fraction)", 0.0, 0.5, 0.15, 0.01)

    st.sidebar.header("Monte Carlo")
    n_sims = st.sidebar.slider("Simulations", 50, 3000, 500, 50)
    id_noise_std = st.sidebar.slider("Intraday noise std (EUR/MWh)", 0.0, 30.0, 5.0, 0.5)

    if st.sidebar.button("Run"):
        st.subheader(f"Prices — {labels.get(country, country)}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["timestamp_utc"], y=df["price_DA_eur_mwh"], mode="lines", name="DA price"))
        fig.update_layout(xaxis_title="Time (UTC)", yaxis_title="EUR/MWh")
        st.plotly_chart(fig, use_container_width=True)

        prices_da = df["price_DA_eur_mwh"].to_numpy(dtype=float)
        mc = run_mc(prices_da, portfolio_mw, alpha, forecast_error_level, n_sims, id_noise_std)

        st.subheader("Profit distribution")
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=mc["total_profit"], nbinsx=40))
        fig2.update_layout(xaxis_title="Total profit (EUR)", yaxis_title="Frequency")
        st.plotly_chart(fig2, use_container_width=True)

        mean_profit = mc["total_profit"].mean()
        std_profit = mc["total_profit"].std()
        var95 = np.percentile(mc["total_profit"], 5)
        cvar95 = mc.loc[mc["total_profit"] <= var95, "total_profit"].mean()

        st.subheader("Risk metrics")
        st.write(f"**Mean profit:** {mean_profit:,.2f} EUR")
        st.write(f"**Std dev:** {std_profit:,.2f} EUR")
        st.write(f"**VaR (5% profit quantile):** {var95:,.2f} EUR")
        st.write(f"**CVaR (mean of worst 5%):** {cvar95:,.2f} EUR")

        with st.expander("Show filtered data"):
            st.dataframe(df)

    else:
        st.info("Choose country + date range, set parameters, then click **Run**.")


if __name__ == "__main__":
    main()