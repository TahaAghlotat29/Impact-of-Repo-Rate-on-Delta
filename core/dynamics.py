import numpy as np
from .greeks import delta
from .forward import repo_curve


def delta_adjusted(S, K, T, r, q, rho, rho_obs, sigma, option_type='call'):
    
    F_mark = S * np.exp((r- rho_obs - q)* T)
    S_adj = F_mark * np.exp( - (r - rho - q) * T)

    return delta(S_adj, K, r, q, rho, T, sigma, option_type)


def delta_static_curve(S, K, T, r, q, sigma, tenors, rates, option_type='call'):

    rho_curve = repo_curve(T, tenors, rates)
    return delta_adjusted(S, K, T, r, q, rho_curve, rho_curve, sigma, option_type)

def repo_sensitivity(S_serie, repo_serie):

    beta, alpha = np.polyfit(S_serie, repo_serie, 1)
    return alpha, beta

def delta_dynamic(S, K, T, r, q, sigma, option_type, alpha, beta):

    rho = alpha + S * beta  
    delta_dyn = delta(S, K, r, q, rho, T, sigma, option_type)
    return delta_dyn