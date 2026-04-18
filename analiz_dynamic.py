from indicator_engine import compute_rsi, compute_bollinger

def apply_indicators(df, config):
    if config["rsi"]["enabled"]:
        df = compute_rsi(df, config["rsi"]["params"]["window"])
    if config["bollinger"]["enabled"]:
        df = compute_bollinger(df, config["bollinger"]["params"]["window"],
                               config["bollinger"]["params"]["std"])
    return df

def check_conditions(df, config):
    last = df.iloc[-1]
    results = {}

    if config["rsi"]["enabled"]:
        results["rsi"] = last["RSI"] < config["rsi"]["params"]["oversold"]

    if config["bollinger"]["enabled"]:
        results["bollinger"] = last["Close"] <= last["BB_LOW"]

    return all(results.values()) if results else False
