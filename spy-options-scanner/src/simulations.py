import numpy as np


def _simulate_gbm_paths(S: float, T: float, vol: float, n_sims: int, steps: int):
    dt = T / steps
    prices = np.full((n_sims, steps + 1), S, dtype=float)

    for t in range(1, steps + 1):
        z = np.random.normal(size=n_sims)
        prices[:, t] = prices[:, t - 1] * np.exp((-0.5 * vol**2) * dt + vol * np.sqrt(dt) * z)

    return prices


def mc_gbm_probs(S: float, K: float, T: float, vol: float, n_sims: int = 20000, steps: int = 60):
    """
    Returns:
      - prob_itm: P(S_T < K)
      - prob_touch: P(min_path <= K)
      - avg_itm_shortfall: E[(K - S_T)+ | ITM]  (per share)
    """
    if T <= 0 or vol <= 0:
        return np.nan, np.nan, np.nan

    paths = _simulate_gbm_paths(S, T, vol, n_sims, steps)
    final = paths[:, -1]
    touched = (paths.min(axis=1) <= K)

    itms = final < K
    shortfall = np.where(itms, K - final, 0.0)
    avg_shortfall_given_itm = float(shortfall[itms].mean()) if itms.any() else 0.0

    return float(itms.mean()), float(touched.mean()), avg_shortfall_given_itm


def bootstrap_probs(S: float, K: float, T: float, returns, n_sims: int = 20000, steps: int = 60):
    """
    Bootstrap simulation using real historical returns.
    Returns same outputs as mc_gbm_probs.
    """
    if T <= 0:
        return np.nan, np.nan, np.nan

    prices = np.full((n_sims, steps + 1), S, dtype=float)
    ret_arr = returns.values

    for t in range(1, steps + 1):
        sampled = np.random.choice(ret_arr, size=n_sims, replace=True)
        prices[:, t] = prices[:, t - 1] * (1 + sampled)

    final = prices[:, -1]
    touched = (prices.min(axis=1) <= K)

    itms = final < K
    shortfall = np.where(itms, K - final, 0.0)
    avg_shortfall_given_itm = float(shortfall[itms].mean()) if itms.any() else 0.0

    return float(itms.mean()), float(touched.mean()), avg_shortfall_given_itm


def jump_diffusion_probs(
    S: float,
    K: float,
    T: float,
    vol: float,
    jump_prob_annual: float = 0.35,
    jump_mean: float = -0.06,
    jump_std: float = 0.03,
    n_sims: int = 20000,
    steps: int = 60
):
    """
    Jump diffusion:
    - GBM + occasional downside jump
    Returns same outputs as mc_gbm_probs.
    """
    if T <= 0 or vol <= 0:
        return np.nan, np.nan, np.nan

    dt = T / steps
    prices = np.full((n_sims, steps + 1), S, dtype=float)

    p_step = 1 - (1 - jump_prob_annual) ** dt

    for t in range(1, steps + 1):
        z = np.random.normal(size=n_sims)
        gbm_move = np.exp((-0.5 * vol**2) * dt + vol * np.sqrt(dt) * z)

        jump_happens = np.random.rand(n_sims) < p_step
        jump_mult = np.ones(n_sims)
        jump_mult[jump_happens] = np.exp(np.random.normal(jump_mean, jump_std, size=np.sum(jump_happens)))

        prices[:, t] = prices[:, t - 1] * gbm_move * jump_mult

    final = prices[:, -1]
    touched = (prices.min(axis=1) <= K)

    itms = final < K
    shortfall = np.where(itms, K - final, 0.0)
    avg_shortfall_given_itm = float(shortfall[itms].mean()) if itms.any() else 0.0

    return float(itms.mean()), float(touched.mean()), avg_shortfall_given_itm
