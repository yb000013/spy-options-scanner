import yfinance as yf
import pandas as pd


def get_price(ticker: str = "SPY") -> float:
    t = yf.Ticker(ticker)
    hist = t.history(period="1d", interval="1m")
    if hist.empty:
        hist = t.history(period="5d")
    return float(hist["Close"].iloc[-1])


def get_expirations(ticker: str = "SPY"):
    t = yf.Ticker(ticker)
    return list(t.options)


def get_option_chain(ticker: str, expiry: str):
    t = yf.Ticker(ticker)
    chain = t.option_chain(expiry)
    calls = chain.calls.copy()
    puts = chain.puts.copy()
    return calls, puts


def get_returns(ticker: str = "SPY", days: int = 252 * 2) -> pd.Series:
    t = yf.Ticker(ticker)
    hist = t.history(period=f"{days}d")
    hist["ret"] = hist["Close"].pct_change()
    return hist["ret"].dropna()
