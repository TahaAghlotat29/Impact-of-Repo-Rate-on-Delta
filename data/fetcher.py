import yfinance as yf

def get_spot(ticker):
    stock = yf.Ticker(ticker)
    return stock.info['currentPrice']

def get_options_chain(ticker, expiry):
    stock = yf.Ticker(ticker)
    chain = stock.option_chain(expiry)
    return chain.calls, chain.puts

def get_dividend_yield(ticker):
    stock = yf.Ticker(ticker)
    return stock.info.get('dividendYield', 0.0)

def get_expiries(ticker):
    stock = yf.Ticker(ticker)
    return stock.options