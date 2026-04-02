import numpy as np

def implied_repo(C, P, S, K, r, q, T):
    """
    Calculate the implied repo rate from the price call and put options observed on the market 
    via put-call parity.

    Parameters:
    C (float): The price of the call option.
    P (float): The price of the put option.
    S (float): The spot price of the underlying asset.
    K (float): The strike price of the options.
    r (float): The risk-free interest rate.
    q (float): The continuous dividend yield of the underlying asset.
    T (float): The time to maturity of the options.

    Returns:
    float: The implied repo rate.
    """
    F_implied = (C - P) * np.exp( r * T) + K 

    if F_implied <=0 or T ==0:
        return None 
    else:
        return r - q - (np.log(F_implied/ S)/T) 
    

def rho_classification(rho):
    """
    Classify the implied repo rate into categories based on its value.

    Parameters:
    rho (float): The implied repo rate to classify.


    Returns:
    str: The classification of the implied repo rate.
    
    - "GC": If rho < 0.005
    - "Special": If 0.005 <= rho < 0.03
    - "Hard to borrow": If 0.03 <= rho < 0.2
    - "Short squeeze": If rho >= 0.2

    """

    if rho < 0.005:
        return "GC"
    elif rho < 0.03:
        return "Special"
    elif rho < 0.2:
        return "Hard to borrow"
    elif rho >= 0.2:
        return "Short squeeze"
