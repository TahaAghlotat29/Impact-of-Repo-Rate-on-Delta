import numpy as np
from scipy.stats import norm

def forward_price(S, r, q, rho, T):
    return S * np.exp((r - q - rho) * T)

def bs_price(S, K, r, q, rho, T, sigma, option_type='call'):
    if T == 0:
        if option_type == 'call':
            return max(S - K, 0)
        else:
            return max(K - S, 0)

    F = forward_price(S, r, q, rho, T)

    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        price = np.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
    else:
        price = np.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))

    return price


