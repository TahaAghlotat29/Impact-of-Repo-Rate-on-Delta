import numpy as np
from scipy.stats import norm
from .pricer import forward_price, bs_price

def delta(S, K, r, q, rho, T, sigma, option_type='call'):
    
    F = forward_price(S, r, q, rho, T)
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))

    if option_type == 'call':
        delta = np.exp(-(q+ rho) * T) * norm.cdf(d1)
    else:
        delta = -np.exp(-(q+ rho) * T) * norm.cdf(-d1)

    return delta

def repo_greek(S, K, r, q, rho, T, sigma, option_type='call'):

    if T == 0:
        return 0.0

    F = forward_price(S, r, q, rho, T)
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
    
    if option_type == 'call':
        rho_value = -T * np.exp(-r * T) * F * norm.cdf(d1) 
    else:
        rho_value = T * np.exp(-r * T) * F * norm.cdf(-d1)

    return rho_value

def gamma(S, K, r, q, rho, T, sigma):

    F = forward_price(S, r, q, rho, T)
    d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))

    gamma = np.exp(-(q+ rho) * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
    return gamma

def delta_repo_sensitivity(S, K, r, q, rho, T, sigma, option_type='call'):

    bps = 0.0001

    delta_up = delta(S, K, r, q, rho + bps, T, sigma, option_type)
    delta_down = delta(S, K, r, q, rho - bps, T, sigma, option_type)

    return (delta_up - delta_down) / (2 * bps)