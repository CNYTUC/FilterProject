import pandas as pd
import yfinance as yf
import ta

# ── Varsayılan filtre (tüm koşullar aktif, orijinal değerler) ─────────────────
VARSAYILAN_FILTRE = {
    "cb_ema_trend":   True,
    "cb_stoch":       True,
    "stoch_esik":     30,
    "cb_macd":        True,
    "macd_mum_esik":  5,
    "cb_fiyat_band":  True,
    "fiyat_tolerans": 2,
}


def veri_cek(ticker: str, periyot: str = "1y") -> pd.DataFrame | None:
    """
    Yahoo Finance'den günlük OHLCV verisi çeker.
    EMA200 için en az 1 yıllık veri gerekir.
    """
    try:
        df = yf.download(ticker, period=periyot, interval="1d",
                         progress=False, auto_adjust=True)
        if df is None or len(df) < 210:
            return None
        df.dropna(inplace=True)
        return df
    except Exception:
        return None


def ema_hesapla(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"].squeeze()
    df["EMA20"]  = ta.trend.ema_indicator(close, window=20)
    df["EMA50"]  = ta.trend.ema_indicator(close, window=50)
    df["EMA100"] = ta.trend.ema_indicator(close, window=100)
    df["EMA200"] = ta.trend.ema_indicator(close, window=200)
    return df


def stochastic_hesapla(df: pd.DataFrame) -> pd.DataFrame:
    high  = df["High"].squeeze()
    low   = df["Low"].squeeze()
    close = df["Close"].squeeze()
    stoch = ta.momentum.StochasticOscillator(
        high=high, low=low, close=close, window=5, smooth_window=3)
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()
    return df


def macd_hesapla(df: pd.DataFrame) -> pd.DataFrame:
    close = df["Close"].squeeze()
    macd_ind = ta.trend.MACD(
        close=close, window_slow=100, window_fast=50, window_sign=9)
    df["MACD"]        = macd_ind.macd()
    df["MACD_SIGNAL"] = macd_ind.macd_signal()
    df["MACD_HIST"]   = macd_ind.macd_diff()
    return df


def kosul_kontrol(df: pd.DataFrame, filtre: dict) -> dict:
    """
    Son muma göre aktif koşulları kontrol eder.
    filtre dict'indeki cb_* anahtarları hangi koşulların aktif olduğunu belirler.
    Devre dışı koşullar otomatik olarak True sayılır (engel olmaz).
    """
    son  = df.iloc[-1]
    prev = df.iloc[-2]

    sonuc = {
        "gecti":   False,
        "kosullar": {},
        "fiyat":   round(float(son["Close"]), 2),
        "detay":   {}
    }

    ema20  = float(son["EMA20"])
    ema50  = float(son["EMA50"])
    ema100 = float(son["EMA100"])
    ema200 = float(son["EMA200"])
    fiyat  = float(son["Close"])

    sonuc["detay"].update({
        "EMA20": round(ema20, 2), "EMA50": round(ema50, 2),
        "EMA100": round(ema100, 2), "EMA200": round(ema200, 2),
    })

    # ── 1. EMA Trend ─────────────────────────────────────────────────────────
    if filtre.get("cb_ema_trend", True):
        sonuc["kosullar"]["yukseli_trendi"] = (ema20 > ema50 > ema100 > ema200)
    else:
        sonuc["kosullar"]["yukseli_trendi"] = True  # devre dışı → geç

    # ── 2. Fiyat-EMA Bandı ────────────────────────────────────────────────────
    tolerans = filtre.get("fiyat_tolerans", 2) / 100
    if filtre.get("cb_fiyat_band", True):
        alt = ema50  * (1 - tolerans)
        ust = ema20  * (1 + tolerans)
        sonuc["kosullar"]["fiyat_ema_band"] = (alt <= fiyat <= ust)
        sonuc["detay"]["fiyat_band_alt"] = round(alt, 2)
        sonuc["detay"]["fiyat_band_ust"] = round(ust, 2)
    else:
        sonuc["kosullar"]["fiyat_ema_band"] = True

    # ── 3. Stochastic ────────────────────────────────────────────────────────
    k_son  = float(son["STOCH_K"])
    d_son  = float(son["STOCH_D"])
    k_prev = float(prev["STOCH_K"])
    d_prev = float(prev["STOCH_D"])
    sonuc["detay"].update({"STOCH_K": round(k_son, 2), "STOCH_D": round(d_son, 2)})

    if filtre.get("cb_stoch", True):
        esik = filtre.get("stoch_esik", 30)
        asiri_satim   = (k_son < esik and d_son < esik)
        donus_sinyali = (k_son > d_son and k_prev <= d_prev)
        sonuc["kosullar"]["stochastic"] = asiri_satim or (k_son < esik and donus_sinyali)
    else:
        sonuc["kosullar"]["stochastic"] = True

    # ── 4. MACD ───────────────────────────────────────────────────────────────
    macd_son   = float(son["MACD"])
    signal_son = float(son["MACD_SIGNAL"])
    boga       = (macd_son > signal_son)

    ayida_mum = 0
    if not boga:
        for i in range(1, min(7, len(df))):
            m = float(df.iloc[-i]["MACD"])
            s = float(df.iloc[-i]["MACD_SIGNAL"])
            if m < s: ayida_mum += 1
            else: break

    sonuc["detay"].update({
        "MACD": round(macd_son, 4), "MACD_SIGNAL": round(signal_son, 4),
        "ayida_mum": ayida_mum if not boga else 0,
    })

    if filtre.get("cb_macd", True):
        mum_esik = filtre.get("macd_mum_esik", 5)
        sonuc["kosullar"]["macd"] = boga or (ayida_mum <= mum_esik)
    else:
        sonuc["kosullar"]["macd"] = True

    # ── Genel sonuç ───────────────────────────────────────────────────────────
    sonuc["gecti"] = all(sonuc["kosullar"].values())
    return sonuc


def hisse_analiz_et(ticker: str, filtre: dict = None) -> dict | None:
    """
    Tek hisse için tüm analizi çalıştırır.
    filtre verilmezse varsayılan değerler kullanılır.
    """
    if filtre is None:
        filtre = VARSAYILAN_FILTRE

    df = veri_cek(ticker)
    if df is None:
        return None

    df = ema_hesapla(df)
    df = stochastic_hesapla(df)
    df = macd_hesapla(df)
    df.dropna(inplace=True)

    if len(df) < 5:
        return None

    try:
        sonuc = kosul_kontrol(df, filtre)
        sonuc["ticker"] = ticker.replace(".IS", "")
        return sonuc
    except Exception:
        return None
