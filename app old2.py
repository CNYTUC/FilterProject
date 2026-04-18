import streamlit as st
import pandas as pd
import yfinance as yf
from indicators import INDICATORS
from analiz_dynamic import apply_indicators, check_conditions

st.title("Dynamic Indicator Scanner")

config = {}

st.sidebar.title("Indicators")

for key, meta in INDICATORS.items():
    enabled = st.sidebar.checkbox(meta["label"], value=meta["enabled"])
    params = {}
    for p, v in meta["params"].items():
        params[p] = st.sidebar.number_input(f"{meta['label']} - {p}", value=v)
    config[key] = {"enabled": enabled, "params": params}

ticker = st.text_input("Ticker", "THYAO.IS")

if st.button("Scan"):
    df = yf.download(ticker, period="6mo", interval="1d")
    df = apply_indicators(df, config)
    result = check_conditions(df, config)

    st.write("Result:", "PASS" if result else "FAIL")
