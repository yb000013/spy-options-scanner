import numpy as np
import pandas as pd
from datetime import datetime

from .market_pricing import prob_put_expire_itm_black_scholes, market_prob_touch_from_itm
from .simulations import mc_gbm_probs, bootstrap_probs, jump_diffusion_probs


def _safe_int(val, default=0):
    """Safely convert to int, handling NaN and None."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return int(val) if val else default


def compute_time_to_expiry(expiry: str) -> float:
    exp_date = datetime.strptime(expiry, "%Y-%m-%d")
    now = datetime.utcnow()
    days = max((exp_date - now).days, 0)
    return days / 365.0


def scan_write_put_edges(
    puts_df: pd.DataFrame,
    S: float,
    expiry: str,
    returns,
    n_sims: int = 15000,
    steps: int = 60,
    min_edge: float = 0.03,
    max_spread_pct: float = 0.15,
    otm_only: bool = True,
    far_otm_min: float = 1.0,
    far_otm_max: float = None,
    min_volume: int = 50,
    min_oi: int = 200,
    min_premium: float = 0.15
) -> pd.DataFrame:
    """
    Only returns mispriced WRITE PUT candidates.

    EDGE:
        edge_itm = MarketProbITM - ModelProbITM

    EV (per contract):
        EV ≈ premium*100 - ModelProbITM * (AvgShortfallGivenITM*100)

    Touch probability:
        - MarketTouch ≈ 2*MarketITM (capped)
        - ModelTouch from simulations (path min <= strike)
    """
    T = compute_time_to_expiry(expiry)

    df = puts_df.copy()
    df = df[df["bid"] > 0].copy()

    df["mid"] = (df["bid"] + df["ask"]) / 2
    df["spread_pct"] = (df["ask"] - df["bid"]) / df["mid"]

    if otm_only:
        df = df[df["strike"] < S]

    # Apply far OTM / near OTM filter
    if far_otm_max is None:
        far_otm_max = S + 100
    
    strike_lower = S - far_otm_max
    strike_upper = S - far_otm_min
    
    df = df[(df["strike"] >= strike_lower) & (df["strike"] <= strike_upper)].copy()

    df = df[
        (df["spread_pct"] <= max_spread_pct) &
        (df["mid"] >= min_premium)
    ].copy()

    out = []
    for _, row in df.iterrows():
        K = float(row["strike"])
        iv = float(row.get("impliedVolatility", np.nan))
        if np.isnan(iv) or iv <= 0:
            continue

        # ---- Market probabilities (IV-based) ----
        market_prob_itm = prob_put_expire_itm_black_scholes(S, K, T, iv)
        market_prob_touch = market_prob_touch_from_itm(market_prob_itm)

        # ---- Model probabilities (simulation-based) ----
        gbm_itm, gbm_touch, gbm_shortfall = mc_gbm_probs(S, K, T, iv, n_sims=n_sims, steps=steps)
        boot_itm, boot_touch, boot_shortfall = bootstrap_probs(S, K, T, returns, n_sims=n_sims, steps=steps)
        jump_itm, jump_touch, jump_shortfall = jump_diffusion_probs(S, K, T, iv, n_sims=n_sims, steps=steps)

        model_prob_itm = float(np.nanmean([gbm_itm, boot_itm, jump_itm]))
        model_prob_touch = float(np.nanmean([gbm_touch, boot_touch, jump_touch]))
        model_shortfall = float(np.nanmean([gbm_shortfall, boot_shortfall, jump_shortfall]))

        # ---- Edges ----
        edge_itm = market_prob_itm - model_prob_itm
        edge_touch = market_prob_touch - model_prob_touch

        imbalance_itm = market_prob_itm / model_prob_itm if model_prob_itm > 0 else np.nan

        # ---- EV estimate ----
        premium_per_share = float(row["mid"])
        ev_per_share = premium_per_share - (model_prob_itm * model_shortfall)
        ev_per_contract = ev_per_share * 100

        out.append({
            "expiry": expiry,
            "strike": K,
            "bid": float(row["bid"]),
            "ask": float(row["ask"]),
            "mid": premium_per_share,
            "iv": iv,

            "market_prob_itm": market_prob_itm,
            "market_prob_touch": market_prob_touch,

            "model_prob_itm": model_prob_itm,
            "model_prob_touch": model_prob_touch,

            "edge_itm": edge_itm,
            "edge_touch": edge_touch,
            "imbalance_itm_ratio": imbalance_itm,

            "gbm_itm": gbm_itm,
            "boot_itm": boot_itm,
            "jump_itm": jump_itm,

            "gbm_touch": gbm_touch,
            "boot_touch": boot_touch,
            "jump_touch": jump_touch,

            "avg_shortfall_given_itm": model_shortfall,

            "ev_per_share": ev_per_share,
            "ev_per_contract": ev_per_contract,

            "spread_pct": float(row["spread_pct"]),
            "volume": _safe_int(row.get("volume", 0)),
            "openInterest": _safe_int(row.get("openInterest", 0)),
        })

    res = pd.DataFrame(out)
    if res.empty:
        return res

    # Liquidity filters
    res = res[(res["volume"] >= min_volume) & (res["openInterest"] >= min_oi)].copy()

    # Mispriced SELL puts only
    res = res[res["edge_itm"] >= min_edge].copy()

    # Rank by best edge, then best EV
    res = res.sort_values(["edge_itm", "ev_per_contract"], ascending=False).reset_index(drop=True)

    return res
