import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.pricer import forward_price, bs_price
from core.greeks import delta, delta_repo_sensitivity
from core.implied_repo import implied_repo, rho_classification
from core.pnl_attribution import hedge_pnl_error
from core.forward import repo_curve
from core.dynamics import delta_adjusted, delta_static_curve
from data.fetcher import get_spot, get_options_chain, get_expiries, get_dividend_yield
from datetime import datetime

st.set_page_config(page_title="RepoDashboard", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        font-weight: 600;
        padding: 12px 24px;
        color: #666;
    }
    .stTabs [aria-selected="true"] {
        color: #1F3864;
        border-bottom: 3px solid #1F3864;
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Delta & Forward", "Implied Repo", "Repo Spike", "Repo Dynamics"])

with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parameters")
        S     = st.slider("Spot price S", 50.0, 200.0, 100.0)
        K     = st.slider("Strike K", 50.0, 200.0, 100.0)
        T     = st.slider("Maturity T (years)", 0.1, 3.0, 1.0)
        r     = st.slider("Risk-free rate r", 0.0, 0.10, 0.05)
        q     = st.slider("Dividend yield q", 0.0, 0.10, 0.02)
        sigma = st.slider("Volatility σ", 0.05, 1.0, 0.20)
        rho   = st.slider("Repo rate ρ", 0.0, 0.50, 0.03)

        F   = forward_price(S, r, q, rho, T)
        d   = delta(S, K, r, q, rho, T, sigma)
        ddr = delta_repo_sensitivity(S, K, r, q, rho, T, sigma)
        shares_per_100bps = abs(ddr / 100 * 0.01 * 10000)

    with col2:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Forward price", f"{F:.2f}")
        m2.metric("Delta (call)", f"{d:.4f}")
        m3.metric("∂Δ/∂ρ per 100bps", f"{ddr/100:.4f}")
        m4.metric("Shares to re-hedge (10k)", f"{shares_per_100bps:.0f}")

        S_range       = np.linspace(50, 200, 200)
        rho_range     = np.linspace(0, 0.50, 200)
        deltas        = delta(S_range, K, r, q, rho, T, sigma)
        sensitivities = delta_repo_sensitivity(S, K, r, q, rho_range, T, sigma)

        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=("Delta vs Spot price",
                                            "Delta sensitivity to repo rate ∂Δ/∂ρ"))

        fig.add_trace(go.Scatter(x=S_range, y=deltas,
                                 line=dict(color="#2E75B6"), name="Delta"), row=1, col=1)
        fig.add_shape(type="line", x0=S, x1=S, y0=0, y1=1,
                      yref="y domain", line=dict(color="red", dash="dash"), row=1, col=1)

        fig.add_trace(go.Scatter(x=rho_range * 100, y=sensitivities,
                                 line=dict(color="#C49A00"), name="∂Δ/∂ρ"), row=2, col=1)
        fig.add_shape(type="line", x0=rho * 100, x1=rho * 100, y0=0, y1=1,
                      yref="y2 domain", line=dict(color="red", dash="dash"), row=2, col=1)

        fig.update_layout(height=700)
        fig.update_xaxes(title_text="Spot price S", row=1, col=1)
        fig.update_xaxes(title_text="Repo rate ρ (%)", row=2, col=1)
        fig.update_yaxes(title_text="Delta", row=1, col=1)
        fig.update_yaxes(title_text="∂Δ/∂ρ", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col3, col4 = st.columns([1, 2])

    with col3:
        ticker = st.text_input("Ticker", value="SMMT")

        if ticker:
            expiries = get_expiries(ticker)
            expiry   = st.selectbox("Expiry", expiries)
            r_input  = st.slider("Risk-free rate r", 0.0, 0.10, 0.05, key="r_tab2")
            gc_rate  = st.slider("GC rate", 0.0, 0.10, 0.05, key="gc_tab2")

            spot = get_spot(ticker)
            q2   = get_dividend_yield(ticker)
            st.metric("Spot price", f"{spot:.2f}")

    with col4:
        if ticker and expiry:
            calls, puts = get_options_chain(ticker, expiry)

            calls['mid'] = (calls['bid'] + calls['ask']) / 2
            puts['mid']  = (puts['bid']  + puts['ask'])  / 2

            merged = calls[['strike', 'mid']].merge(
                puts[['strike', 'mid']], on='strike', suffixes=('_call', '_put'))

            T2 = (datetime.strptime(expiry, "%Y-%m-%d") - datetime.today()).days / 365

            merged['rho_implied'] = merged.apply(
                lambda row: implied_repo(row['mid_call'], row['mid_put'],
                                         spot, row['strike'], r_input, q2, T2), axis=1)

            merged['classification'] = merged['rho_implied'].apply(
                lambda x: rho_classification(x) if x is not None else None)

            merged = merged[merged['rho_implied'].notna() & (merged['rho_implied'] > 0)]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=merged['strike'], y=merged['rho_implied'] * 100,
                                     mode='markers', name='Implied repo',
                                     marker=dict(color="#2E75B6", size=8)))
            fig.add_hline(y=gc_rate * 100, line_dash="dash", line_color="red",
                          annotation_text=f"GC rate {gc_rate*100:.1f}%")
            fig.update_layout(height=450, xaxis_title="Strike",
                              yaxis_title="Implied repo (%)",
                              title=f"Implied repo by strike")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(merged[['strike', 'rho_implied', 'classification']])

with tab3:
    col5, col6 = st.columns([1, 2])

    with col5:
        st.subheader("Parameters")
        S3          = st.slider("Spot price S", 50.0, 200.0, 100.0, key="S_tab3")
        K3          = st.slider("Strike K", 50.0, 200.0, 100.0, key="K_tab3")
        T3          = st.slider("Maturity T (years)", 0.01, 3.0, 0.25, key="T_tab3")
        r3          = st.slider("Risk-free rate r", 0.0, 0.10, 0.05, key="r_tab3")
        q3          = st.slider("Dividend yield q", 0.0, 0.10, 0.02, key="q_tab3")
        sigma3      = st.slider("Volatility σ", 0.05, 1.0, 0.20, key="sigma_tab3")
        rho_before3 = st.slider("Repo before spike ρ", 0.0, 0.50, 0.02, key="rho_before")
        rho_after3  = st.slider("Repo after spike ρ", 0.0, 1.0, 0.15, key="rho_after")

        d_before = delta(S3, K3, r3, q3, rho_before3, T3, sigma3)
        d_after  = delta(S3, K3, r3, q3, rho_after3,  T3, sigma3)
        d_shift  = d_after - d_before
        shares   = d_shift * 10000
        action   = "BUY" if shares > 0 else "SELL"

    with col6:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Delta before", f"{d_before:.4f}")
        m2.metric("Delta after",  f"{d_after:.4f}")
        m3.metric("Delta shift",  f"{d_shift:.4f}")
        m4.metric(f"{action} at close", f"{abs(shares):.0f} shares")

        S_range3  = np.linspace(50, 200, 200)
        d_before3 = delta(S_range3, K3, r3, q3, rho_before3, T3, sigma3)
        d_after3  = delta(S_range3, K3, r3, q3, rho_after3,  T3, sigma3)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=S_range3, y=d_before3,
                                 name=f"Before spike (ρ={rho_before3*100:.0f}%)",
                                 line=dict(color="#2E75B6")))
        fig.add_trace(go.Scatter(x=S_range3, y=d_after3,
                                 name=f"After spike (ρ={rho_after3*100:.0f}%)",
                                 line=dict(color="#C0392B")))
        fig.add_vline(x=S3, line_dash="dash", line_color="grey",
                      annotation_text=f"S = {S3:.0f}")
        fig.update_layout(height=500, xaxis_title="Spot price S",
                          yaxis_title="Delta",
                          title="Delta ")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    col7, col8 = st.columns([1, 2])

    with col7:
        st.subheader("Parameters")
        S4     = st.slider("Spot price S", 50.0, 200.0, 100.0, key="S_tab4")
        K4     = st.slider("Strike K", 50.0, 200.0, 100.0, key="K_tab4")
        T4     = st.slider("Maturity T (years)", 0.1, 3.0, 1.0, key="T_tab4")
        r4     = st.slider("Risk-free rate r", 0.0, 0.10, 0.05, key="r_tab4")
        q4     = st.slider("Dividend yield q", 0.0, 0.10, 0.02, key="q_tab4")
        sigma4 = st.slider("Volatility σ", 0.05, 1.0, 0.15, key="sigma_tab4")
        beta4  = st.slider("Beta ∂ρ/∂S", -0.01, 0.0, -0.005, step=0.001, key="beta_tab4")
        alpha4 = st.slider("Alpha", 0.0, 1.0, 0.70, key="alpha_tab4")

        tenors = [0.083, 0.25, 0.5, 1.0, 2.0]
        rates  = [0.15,  0.12, 0.10, 0.08, 0.06]

        d_m1     = delta_static_curve(S4, K4, T4, r4, q4, sigma4, tenors, rates)
        rho_dyn4 = np.clip(alpha4 + beta4 * S4, 0, None)
        rho_ref4 = repo_curve(T4, tenors, rates)
        d_m2     = delta_adjusted(S4, K4, T4, r4, q4, rho_dyn4, rho_ref4, sigma4)

    with col8:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Delta Model 1", f"{d_m1:.4f}")
        m2.metric("Delta Model 2", f"{d_m2:.4f}")
        m3.metric("Dynamic repo", f"{rho_dyn4*100:.2f}%")
        m4.metric("Static repo ", f"{rho_ref4*100:.2f}%")

        np.random.seed(42)
        N4, dt4 = 252, 1/252
        S_path4 = np.zeros(N4)
        S_path4[0] = S4
        for t in range(1, N4):
            Z = np.random.normal()
            S_path4[t] = S_path4[t-1] * np.exp((r4 - q4 - 0.5*sigma4**2)*dt4 + sigma4*np.sqrt(dt4)*Z)

        pnl_m1, pnl_m2 = [0.0], [0.0]
        for t in range(1, N4):
            T_rem = (N4 - t) / 252
            move  = S_path4[t] - S_path4[t-1]
            dm1   = delta_static_curve(S_path4[t-1], K4, T_rem, r4, q4, sigma4, tenors, rates)
            rho_d = np.clip(alpha4 + beta4 * S_path4[t-1], 0, None)
            rho_r = repo_curve(T_rem, tenors, rates)
            dm2   = delta_adjusted(S_path4[t-1], K4, T_rem, r4, q4, rho_d, rho_r, sigma4)
            pnl_m1.append(pnl_m1[-1] + dm1 * move * 10000)
            pnl_m2.append(pnl_m2[-1] + dm2 * move * 10000)

        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=("Simulated spot path",
                                            "Cumulative P&L - Model 1 / Model 2"))

        fig.add_trace(go.Scatter(y=S_path4, line=dict(color="#2E75B6"),
                                 name="Spot"), row=1, col=1)
        fig.add_trace(go.Scatter(y=pnl_m1, name="Model 1 — Static curve",
                                 line=dict(color="#C49A00")), row=2, col=1)
        fig.add_trace(go.Scatter(y=pnl_m2, name="Model 2 — Dynamic ρ=f(S)",
                                 line=dict(color="#C0392B")), row=2, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=2, col=1)

        fig.update_layout(height=700)
        fig.update_xaxes(title_text="Days")
        fig.update_yaxes(title_text="Spot price", row=1, col=1)
        fig.update_yaxes(title_text="P&L (€)", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)