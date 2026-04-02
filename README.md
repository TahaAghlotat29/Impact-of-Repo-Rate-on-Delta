# Repo Rate & Delta 

The repo rate is the cost of borrowing a stock. It sounds like a back-office parameter 
but it sits at the heart of every delta hedge on a single stock option. When a stock 
becomes hard to borrow, the forward price compresses, the delta shifts, and a position 
that was perfectly hedged the night before is suddenly exposed before the market even 
opens.

The effect is negligible on short-dated options and liquid names. It becomes critical on 
long-dated options, during short squeezes where borrow rates can jump from 2% to 80% 
overnight, or on any name where the float is restricted and short sellers are competing 
for a shrinking pool of lendable shares. In those situations, ignoring the repo rate becomes a 
mispricing that compounds through every daily rebalancing.

This project builds the repo rate into the pricing and hedging framework from the ground 
up, and quantifies exactly what it costs to get it wrong.

A natural extension of the base model is to ask whether the repo itself moves when the 
spot moves. On a hard-to-borrow stock, the two are not independent. When the price falls, 
short sellers compete harder for a shrinking pool of lendable shares and the borrow rate 
rises. When the price recovers, shorts cover and the repo compresses.

To account for this, the project introduces two models that both keep the forward fixed 
when the repo changes, isolating the pure impact of the borrow rate on the delta.

Model 1 uses a static repo curve where the borrow rate depends only on maturity. 
Model 2 estimates the repo as a linear function of the spot via regression, rho = alpha + beta x S, 
and updates it at every rebalancing step.

A full P&L backtest shows that Model 2 outperforms Model 1 during periods of large spot 
dislocations, where the co-movement between the spot and the borrow rate is most significant.

## The Math

The forward price with explicit repo:

$$F = S \cdot e^{(r - q - \rho) \cdot T}$$

Delta with repo-adjusted forward:

$$\Delta_{call} = e^{-\rho T} \cdot N(d_1) \quad \text{where} \quad d_1 = \frac{\ln(F/K) + \frac{1}{2}\sigma^2 T}{\sigma \sqrt{T}}$$

Implied repo from put-call parity:

$$\rho_{implied} = r - q - \frac{\ln(F_{implied}/S)}{T} \quad \text{where} \quad F_{implied} = (C - P) \cdot e^{rT} + K$$

Forward-neutral delta adjustment keeping the forward constant when the repo changes:

$$S_{adj} = F_{ref} \cdot e^{(r - q - \rho) \cdot T} \quad \text{where} \quad F_{ref} = S \cdot e^{(r - q - \rho_{ref}) \cdot T}$$


Dynamic repo model where the borrow rate moves with the spot price:

$$\rho(S) = \alpha + \beta \cdot S$$

## Project Structure
```
Repo/
├── core/
│   ├── pricer.py          # BS pricing with explicit repo
│   ├── greeks.py          # Delta, gamma, repo sensitivity
│   ├── forward.py         # Repo curve interpolation
│   ├── implied_repo.py    # Implied repo from put-call parity
│   ├── pnl_attribution.py # Hedge error quantification
│   └── dynamics.py        # Iso-forward delta, repo regression, dynamic model
├── data/
│   ├── fetcher.py         
│   └── real_cases.py      
├── notebooks/             # Analysis and visualizations
├── app/
│   └── streamlit_app.py   
```

## Quick Start
```bash
uv pip install -e .
uv run streamlit run app/streamlit_app.py
```