import numpy as np
from scipy.stats import norm


def prob_put_expire_itm_black_scholes(S: float, K: float, T: float, iv: float, r: float = 0.0) -> float:
    """
    Market-Implied Probability of Put expiring ITM:
        P(S_T < K) = N(-d2)

    where:
        d2 = [ ln(S/K) + (r - 0.5*iv^2)*T ] / (iv*sqrt(T))
    """
    if T <= 0 or iv <= 0 or S <= 0 or K <= 0:
        return np.nan

    d2 = (np.log(S / K) + (r - 0.5 * iv**2) * T) / (iv * np.sqrt(T))
    return float(norm.cdf(-d2))


def market_prob_touch_from_itm(prob_itm: float) -> float:
    """
    Approx market touch probability using a common trader approximation:

        P(touch) ≈ 2 * P(expire ITM)

    capped at 1.0 (100%)

    This is not perfect but is widely used as a quick estimate.
    """
    if prob_itm is None or np.isnan(prob_itm):
        return np.nan
    return float(min(1.0, 2.0 * prob_itm))


def expected_move_one_sigma(S: float, iv: float, T: float) -> float:
    """
    Rough 1-sigma expected move:
        EM ≈ S * iv * sqrt(T)
    """
    if T <= 0 or iv <= 0:
        return np.nan
    return float(S * iv * np.sqrt(T))
