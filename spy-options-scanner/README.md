# Write Put Edge Scanner

A free, open-source Streamlit app to find potentially overpriced puts to **WRITE (sell)** using Monte Carlo simulations + market comparison.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## How It Works

1. **Market Pricing**: Uses Black-Scholes implied vol to estimate what the market thinks
2. **Model Pricing**: Runs 3 simulations (GBM, Bootstrap, Jump Diffusion) to estimate real risk
3. **Edge Detection**: Finds puts where market overestimates risk relative to your model
4. **EV Estimation**: Estimates expected value per contract written

## Features

- 📊 Real-time SPY options data (via yfinance)
- 🎯 3 preset risk profiles (Conservative / Balanced / Aggressive)
- 🧪 Monte Carlo + Bootstrap + Jump Diffusion models
- 💰 EV and edge calculations
- 📈 Touch probability estimates
- 🔧 Fully customizable filters

## Disclaimer

This is educational software. Not financial advice. Trade at your own risk.
