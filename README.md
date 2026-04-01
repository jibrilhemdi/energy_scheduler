# Energy Scheduling & Trading Simulator


A Streamlit-based simulator for electricity market scheduling and risk analysis under forecast uncertainty, using real European wholesale electricity prices and Monte Carlo simulation.

The project focuses on decision-making under uncertainty (not asset-level engineering), and is designed to be realistic, transparent, and reproducible using public European energy data.

----------------

## Project Overview

This simulator models a fixed-MW electricity portfolio trading in the day-ahead market, with:

- Forecast uncertainty
- Imbalance exposure
- Risk metrics such as VaR and CVaR

### Key characteristics:

- Real historical price data (multi-country)
- Monte Carlo simulation of forecast errors
- Risk-aware scheduling decisions
- Interactive Streamlit dashboard

--------------------

## Modeling Assumptions

- Positive MW = consumption (retail-style portfolio)
- Negative MW = generation (producer-style portfolio)
- Portfolio size is fixed in MW (price-taker)
- Forecast uncertainty is modeled statistically (no perfect foresight)
- Intraday / imbalance prices are approximated via stochastic spreads

This mirrors how public-data-based energy trading research is typically done.

---------------------------------------------

## 📊 Data Sources

Due to size and licensing considerations, raw data files are not committed.

You must download them manually from the official sources below.

### 🔹 Electricity Prices (Day-Ahead)
**Ember – European Wholesale Electricity Price Data**
https://ember-energy.org/data/european-wholesale-electricity-price-data/

Used file structure:
- Multi-country
- Hourly resolution
- Columns include: all_countries.csv

Place the file at:
```data/all_countries.csv```

### 🔹 Electricity Load (Contextual, optional)
**ENTSO‑E Transparency Platform – Monthly Hourly Load Values**
https://www.entsoe.eu/data/power-stats/

Files are published per year.

Expected local paths:
```
data/monthly_hourly_load_values_2019.csv
data/monthly_hourly_load_values_2020.csv
...
data/monthly_hourly_load_values_2025.csv
```
> ⚠️ Note: Load data is currently not used in P&L calculations, but is included for
> future extensions such as regime detection or stress testing.

-----------------

## 🗂 Project Structure
```
energy_scheduler/
│
├── app/
│   └── streamlit_app.py        # Streamlit UI
│
├── simulation/
│   ├── loader.py               # Data loading & normalization
│   ├── forecast.py             # Forecast error modeling
│   ├── strategy.py             # Scheduling strategies
│   ├── profit.py               # Profit & imbalance calculation
│   └── __init__.py
│
├── data/                        # (ignored by git)
│
├── notebooks/                  # optional exploration
│
├── requirements.txt
├── .gitignore
└── README.md
```

----------

## ▶️ How to Run

1. Create environment & install dependencies
<br>
   ```pip install -r requirements.txt```

2. Download data
<br>
   Place `all_countries.csv` into `data/`
   
   (Optional) Place ENTSO‑E yearly load CSVs into `data/`

3. Start Streamlit
<br>
   ```streamlit run app/streamlit_app.py```

-------

## 📈 Outputs

The app provides:

- Hourly price visualization
- Monte Carlo profit distribution
- Risk metrics:
  - Mean profit
  - Standard deviation
  - Value at Risk (VaR)
  - Conditional Value at Risk (CVaR)