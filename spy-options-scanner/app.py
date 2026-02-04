import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.data import get_price, get_expirations, get_option_chain, get_returns
from src.edge_engine import scan_write_put_edges, compute_time_to_expiry
from src.market_pricing import expected_move_one_sigma


st.set_page_config(page_title="MarketEdge", layout="wide")

st.title("MarketEdge")
st.caption("Find potentially overpriced puts to WRITE (sell) by comparing market-implied risk vs simulation-based risk.")


# ------------------ PRESETS ------------------
PRESETS = {
    "Conservative 🟢": {
        "min_edge": 0.05,
        "max_spread_pct": 0.10,
        "min_premium": 0.20,
        "min_volume": 200,
        "min_oi": 500,
        "otm_only": True,
        "n_sims": 20000,
        "steps": 80,
    },
    "Balanced 🟡": {
        "min_edge": 0.03,
        "max_spread_pct": 0.15,
        "min_premium": 0.15,
        "min_volume": 50,
        "min_oi": 200,
        "otm_only": True,
        "n_sims": 15000,
        "steps": 60,
    },
    "Aggressive 🔴": {
        "min_edge": 0.015,
        "max_spread_pct": 0.25,
        "min_premium": 0.10,
        "min_volume": 10,
        "min_oi": 50,
        "otm_only": True,
        "n_sims": 12000,
        "steps": 50,
    },
}


with st.sidebar:
    st.header("⚙️ Scan Settings")

    ticker = st.text_input("Ticker", value="SPY").upper()
    
    # Get underlying price FIRST so we can use it in the filters below
    S = get_price(ticker)
    
    expirations = get_expirations(ticker)
    expiry = st.selectbox("Expiration Date", expirations)

    st.divider()
    preset_name = st.selectbox("Preset", list(PRESETS.keys()), index=1)
    preset = PRESETS[preset_name]

    st.caption("Presets auto-fill recommended settings. You can still tweak them below.")

    st.divider()
    st.subheader("Simulation Controls")

    n_sims = st.slider(
        "Number of simulations (more = smoother but slower)",
        min_value=5000, max_value=60000, value=int(preset["n_sims"]), step=5000
    )

    steps = st.slider(
        "Steps per simulation path (more = more realistic path)",
        min_value=20, max_value=200, value=int(preset["steps"]), step=10
    )

    st.divider()
    st.subheader("Trade Filters")

    otm_only = st.checkbox("Only show OTM puts (strike < price)", value=bool(preset["otm_only"]))

    st.subheader("Far OTM / Near OTM Filter")
    far_otm_min = st.number_input(
        "Minimum OTM distance (in $) from current price",
        min_value=1,
        max_value=50,
        value=1,
        step=1
    )
    far_otm_max = st.number_input(
        "Maximum OTM strike (in $) to consider",
        min_value=int(S+1),
        max_value=int(S+100),
        value=int(S+60),
        step=1
    )

    min_edge = st.slider(
        "Minimum Edge % (market ITM prob - model ITM prob)",
        min_value=0.0, max_value=0.20, value=float(preset["min_edge"]), step=0.005
    )

    max_spread_pct = st.slider(
        "Max spread % (tight spreads = better fills)",
        min_value=0.01, max_value=0.50, value=float(preset["max_spread_pct"]), step=0.01
    )

    min_premium = st.slider(
        "Min premium (mid price)",
        min_value=0.01, max_value=2.00, value=float(preset["min_premium"]), step=0.01
    )

    min_volume = st.number_input("Min volume", value=int(preset["min_volume"]), step=10)
    min_oi = st.number_input("Min open interest", value=int(preset["min_oi"]), step=50)

    refresh = st.button("🔄 Refresh Scan")
    
    st.divider()
    st.subheader("Portfolio Settings (for EV % & sizing)")
    portfolio_value = st.number_input("Portfolio value ($)", min_value=1000, value=100000, step=1000)
    allocation_pct = st.slider("Allocation per trade (% of portfolio)", min_value=0.5, max_value=10.0, value=1.0, step=0.5)

if refresh:
    st.rerun()


# ------------------ DATA ------------------
returns = get_returns(ticker)
calls, puts = get_option_chain(ticker, expiry)
T = compute_time_to_expiry(expiry)


st.subheader("📌 Underlying Snapshot")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Ticker", ticker)

with col2:
    st.metric("Price", f"${S:.2f}")

with col3:
    st.metric("Expiry", expiry)

with col4:
    st.metric("Time (years)", f"{T:.3f}")


# ------------------ EXPLANATION ------------------
with st.expander("📘 What this scanner is doing (math + meaning)", expanded=True):
    st.markdown(
        """
### ✅ What "writing puts" means
When you **write (sell) a put**, you collect premium now.
- If price stays above strike → you keep premium
- If price falls below strike → you can be assigned (buy 100 shares)

---

## 🔥 Edge (Mispricing)
We define the main edge like this:

**Edge_ITM = MarketProb(ITM) − ModelProb(ITM)**

If **Edge_ITM is positive**, it means:
- Market is pricing the put like assignment risk is higher
- Your simulations estimate lower risk
→ premium may be overpriced → candidate to SELL

---

## 📌 Market Probability (Black–Scholes)
Using implied volatility (IV):

**P(put expires ITM) = N(-d2)**

Where:

**d2 = [ ln(S/K) + (r − 0.5·IV²)·T ] / (IV·√T)**

---

## 👆 Probability of TOUCH
Touch means the price hits the strike **at any time** before expiry.

**Market Touch Approximation:**
A common trader estimate is:

**P(touch) ≈ 2 × P(expire ITM)** (capped at 100%)

**Model Touch:**
From simulations we check if:

**min(path) ≤ strike**

---

## 🧪 Your Model Probability (Simulations)
We use 3 models and average them:

1) **GBM Monte Carlo** (fast baseline)
2) **Bootstrap** (uses real historical returns)
3) **Jump Diffusion** (adds crash risk)

**ModelProb = mean(GBM, Bootstrap, JumpDiffusion)**

---

## 💰 EV Estimate (Expected Value per contract)
We estimate:

**EV/share ≈ Premium − ModelProbITM × AvgShortfallGivenITM**

Then:

**EV/contract = EV/share × 100**

This gives a practical idea of whether premium compensates for modeled downside.

---

## 💧 Max Spread %
Spread = Ask − Bid  
Spread% = (Ask − Bid) / Mid

Lower spreads = better fills and more real profit.
"""
    )


# ------------------ SCAN ------------------
results = scan_write_put_edges(
    puts_df=puts,
    S=S,
    expiry=expiry,
    returns=returns,
    n_sims=n_sims,
    steps=steps,
    min_edge=min_edge,
    max_spread_pct=max_spread_pct,
    otm_only=otm_only,
    far_otm_min=far_otm_min,
    far_otm_max=far_otm_max,
    min_volume=min_volume,
    min_oi=min_oi,
    min_premium=min_premium
)

# Keep only positive expected-value trades
results = results[results["ev_per_contract"] > 0].copy()

st.subheader("🏆 Mispriced WRITE PUT Candidates (Positive EV Only)")

if results.empty:
    st.warning("No +EV mispriced sell puts found with your filters. Try lowering Min Edge, increasing premium tolerances, or loosening liquidity filters.")
else:
    results["market_itm_%"] = results["market_prob_itm"] * 100
    results["model_itm_%"] = results["model_prob_itm"] * 100
    results["edge_itm_%"] = results["edge_itm"] * 100

    results["market_touch_%"] = results["market_prob_touch"] * 100
    results["model_touch_%"] = results["model_prob_touch"] * 100
    results["edge_touch_%"] = results["edge_touch"] * 100

    results["spread_%"] = results["spread_pct"] * 100

    # EV as percent of capital at risk (strike * 100 shares)
    results["ev_pct_of_risk"] = (results["ev_per_contract"] / (results["strike"] * 100)) * 100

    # Recommended contracts based on portfolio allocation
    allocation_amount = float(portfolio_value) * (float(allocation_pct) / 100.0)
    # avoid division by zero
    results["recommended_contracts"] = np.floor(allocation_amount / (results["strike"] * 100)).astype(int).clip(lower=0)

    st.dataframe(
        results[[
            "strike", "mid", "bid", "ask",
            "market_itm_%", "model_itm_%", "edge_itm_%",
            "market_touch_%", "model_touch_%", "edge_touch_%",
            "imbalance_itm_ratio",
            "ev_per_contract", "ev_pct_of_risk", "recommended_contracts",
            "spread_%", "volume", "openInterest"
        ]].style.format({
            "mid": "{:.2f}",
            "bid": "{:.2f}",
            "ask": "{:.2f}",

            "market_itm_%": "{:.2f}%",
            "model_itm_%": "{:.2f}%",
            "edge_itm_%": "{:.2f}%",

            "market_touch_%": "{:.2f}%",
            "model_touch_%": "{:.2f}%",
            "edge_touch_%": "{:.2f}%",

            "imbalance_itm_ratio": "{:.2f}x",
            "ev_per_contract": "${:,.2f}",
            "ev_pct_of_risk": "{:.4f}%",
            "spread_%": "{:.2f}%",
        }),
        use_container_width=True,
        height=650
    )

    st.success("Only showing puts with positive mispricing edge (Edge_ITM ≥ your minimum). Potential write-put sells.")

    # Filter slider for edge
    st.sidebar.header("📊 Results Filters")
    min_edge_filter = st.sidebar.slider("Minimum Edge (%) to display", min_value=0.0, max_value=50.0, value=0.0, step=0.1)
    filtered_results = results[results["edge_itm"] >= (min_edge_filter / 100)]
    
    st.subheader(f"📈 Filtered Results ({len(filtered_results)} opportunities)")
    if not filtered_results.empty:
        # Chart 1: Edge vs Strike - Shows which strikes have the best edge
        fig1 = px.bar(
            filtered_results,
            x="strike",
            y="edge_itm",
            color="edge_itm",
            title="<b>Edge (%) by Strike Price</b><br><sub>Higher edge = market is overpricing risk. Sell these puts.</sub>",
            labels={"strike": "Strike Price ($)", "edge_itm": "Edge (%)"},
            height=450,
            color_continuous_scale="RdYlGn",
            hover_data={"strike": ":.2f", "edge_itm": ":.2%"}
        )
        fig1.update_layout(hovermode="x unified", font=dict(size=12), title_font_size=14, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

        # Chart 2: Expected Value Analysis - Dollar profit potential
        fig2 = px.scatter(
            filtered_results,
            x="strike",
            y="ev_per_contract",
            color="market_itm_%",
            title="<b>Expected Value per Contract</b><br><sub>Dollar profit if your edge model is correct.</sub>",
            labels={"strike": "Strike Price ($)", "ev_per_contract": "EV per Contract ($)", "market_itm_%": "Market ITM %"},
            height=450,
            color_continuous_scale="Blues",
            hover_data={"strike": ":.2f", "ev_per_contract": "$:.2f", "bid": ":.2f", "ask": ":.2f", "volume": ":d"}
        )
        fig2.update_layout(hovermode="closest", font=dict(size=12), title_font_size=14)
        fig2.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Breakeven", annotation_position="right")
        st.plotly_chart(fig2, use_container_width=True)

        # Chart 3: Market vs Model Probability - Mispricing visualization
        fig3 = px.scatter(
            filtered_results,
            x="market_prob_itm",
            y="model_prob_itm",
            color="edge_itm",
            title="<b>Market-Implied vs Simulated Probability (ITM)</b><br><sub>Points above diagonal = overpriced (SELL). Points below = underpriced (AVOID).</sub>",
            labels={"market_prob_itm": "Market Probability", "model_prob_itm": "Model Probability", "edge_itm": "Edge"},
            height=450,
            color_continuous_scale="RdYlGn",
            hover_data={"strike": True, "ev_per_contract": "$:.2f", "volume": True}
        )
        fig3.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(dash="dash", color="gray", width=2))
        fig3.add_annotation(x=0.7, y=0.65, text="<b>Fair Pricing</b><br>(diagonal)", showarrow=False, bgcolor="rgba(200,200,200,0.3)", bordercolor="gray", borderwidth=1)
        fig3.update_layout(hovermode="closest", font=dict(size=12), title_font_size=14, xaxis_range=[0, 1], yaxis_range=[0, 1])
        st.plotly_chart(fig3, use_container_width=True)

        # Summary stats
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Best Edge", f"{filtered_results['edge_itm'].max():.2%}", "Highest mispricing")
        with col2:
            st.metric("Avg Edge", f"{filtered_results['edge_itm'].mean():.2%}", "Average opportunity")
        with col3:
            st.metric("Best EV", f"${filtered_results['ev_per_contract'].max():.2f}", "Max expected profit")
        with col4:
            st.metric("Avg EV", f"${filtered_results['ev_per_contract'].mean():.2f}", "Avg expected profit")


# Edge Explanation Section
st.header("📊 How MarketEdge is Calculated")

st.markdown("""
The **edge** for each put option is calculated as:

**Edge (%) = (Market Implied Probability − Simulated Probability) × 100**

Where:

- **Market Implied Probability** is derived from the option's price using the Black-Scholes model:

$$P_{market} = N(d_2)$$

- **Simulated Probability** is calculated using Monte Carlo simulations of the underlying price:

$$S_T = S_0 \\times e^{(r - 0.5\\sigma^2)T + \\sigma \\sqrt{T} Z}$$

- **Expected Value (EV) per contract**:

$$EV = Premium \\times (Simulated\\ Probability\\ of\\ Profit) - (Strike - Spot) \\times (1 - Simulated\\ Probability\\ of\\ Profit)$$

- **Probability of Touch**: likelihood that the underlying touches the strike price before expiration.

---

### What This Means:
- **Positive Edge** = Market is overpricing risk (put is too expensive) → Sell opportunity
- **Negative Edge** = Market is underpricing risk (put is too cheap) → Avoid selling
- **Touch Probability** = Chance the stock touches your strike (more aggressive than ITM)
""")


# ------------------ QUICK RISK INTUITION ------------------
st.subheader("📊 Quick Risk Intuition")
st.caption("1σ expected move is a volatility-based estimate (not a guarantee).")

if not results.empty:
    top_iv = float(results.iloc[0]["iv"])
    em = expected_move_one_sigma(S, top_iv, T)
    st.write(f"Top candidate IV: **{top_iv:.2%}**")
    st.write(f"1σ expected move estimate: **±${em:.2f}** (rough)")
