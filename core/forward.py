import numpy as np
from numpy import interp
from .pricer import forward_price

def repo_curve(T, tenors, rates):
    """
    Interpolate the repo curve for a given tenor T.

    Parameters:
    T (float): The tenor for which to interpolate the repo rate.
    tenors (list of float): The list of tenors for which repo rates are known.
    rates (list of float): The list of repo rates corresponding to the tenors.

    Returns:
    float: The interpolated repo rate for tenor T.
    """
    return interp(T, tenors, rates)

def forward_with_curves(S, r,  q, tenors, rates, T):
    """
    Calculate the forward price of an asset using the repo curve.

    Parameters:
    S (float): The spot price of the asset.
    q (float): The continuous dividend yield of the asset.
    tenors (list of float): The list of tenors for which repo rates are known.
    rates (list of float): The list of repo rates corresponding to the tenors.
    T (float): The time to maturity of the forward contract.

    Returns:
    float: The forward price of the asset.
    """
    rho = repo_curve(T, tenors, rates)
    return forward_price(S, r, q, rho, T)