import numpy as np
from .greeks import delta

def hedge_pnl_error(S, K, r, q, rho_true, rho_wrong, T, sigma, option_type):
    """Calculate the PnL error from hedging with the wrong repo.

    Parameters:
    S: Spot price of the underlying
    K: Strike price of the option
    r: Risk-free rate
    q: Dividend yield
    rho_true: True repo used for hedging
    rho_wrong: Wrong repo used for hedging
    T: Time to maturity
    sigma: Volatility of the underlying
    option_type: 'call' or 'put'

    Returns:
    pnl_error: The PnL error from hedging with the wrong repo
    
    """

    delta_true = delta(S, K, r, q, rho_true, T, sigma, option_type)
    delta_wrong = delta(S, K, r, q, rho_wrong, T, sigma, option_type)

    pnl_error = (delta_wrong - delta_true) * S 

    return pnl_error