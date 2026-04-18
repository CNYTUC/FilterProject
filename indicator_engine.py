import ta

def compute_rsi(df, window):
    df["RSI"] = ta.momentum.rsi(df["Close"], window=window)
    return df

def compute_bollinger(df, window, std):
    bb = ta.volatility.BollingerBands(df["Close"], window=window, window_dev=std)
    df["BB_LOW"] = bb.bollinger_lband()
    df["BB_HIGH"] = bb.bollinger_hband()
    return df
