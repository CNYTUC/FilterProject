import pandas as pd
import yfinance as yf
import ta

# Varsayılan filtre ayarları
VARSAYILAN_FILTRE = {
    "cb_ema_trend": True,
    "cb_mum_ema": True,
    "mum_tolerans": 2,
    "cb_stoch": True,
    "stoch_esik": 30,
    "cb_macd": True,
    "macd_mum_esik": 5,
}


def veri_cek(ticker: str, periyot: str = "1y") -> pd.DataFrame | None:
    """
    Yahoo Finance üzerinden günlük veriyi çeker.
    EMA200 hesaplanabilsin diye yaklaşık 1 yıllık veri istenir.
    """
    try:
        df = yf.download(
            ticker,
            period=periyot,
            interval="1d",
            progress=False,
            auto_adjust=True,
            group_by="column",
            threads=False,
        )

        if df is None or df.empty:
            return None

        # Bazen çok seviyeli kolon dönebilir, sadeleştir.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        gerekli = {"Open", "High", "Low", "Close"}
        if not gerekli.issubset(set(df.columns)):
            return None

        df = df.dropna().copy()
        if len(df) < 210:
            return None

        return df
    except Exception:
        return None


def indiktorleri_hesapla(df: pd.DataFrame) -> pd.DataFrame:
    """EMA, Stochastic ve MACD sütunlarını ekler."""
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)

    # EMA
    df["EMA20"] = ta.trend.ema_indicator(close, window=20)
    df["EMA50"] = ta.trend.ema_indicator(close, window=50)
    df["EMA100"] = ta.trend.ema_indicator(close, window=100)
    df["EMA200"] = ta.trend.ema_indicator(close, window=200)

    # Stochastic (5,3,3)
    stoch = ta.momentum.StochasticOscillator(
        high=high,
        low=low,
        close=close,
        window=5,
        smooth_window=3,
    )
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()

    # MACD (50,100,9) -> fast=50, slow=100
    macd = ta.trend.MACD(
        close=close,
        window_fast=50,
        window_slow=100,
        window_sign=9,
    )
    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()
    df["MACD_HIST"] = macd.macd_diff()

    return df


def mum_ema_teyidi(son_mum: pd.Series, ema20: float, ema50: float, tolerans_yuzde: float) -> tuple[bool, float, float]:
    """
    Fiyatın hareketli ortalamalar bölgesinde olup olmadığını kontrol eder.
    Mantık:
    - Mumun düşük seviyesi EMA50'ye yakın olsun
    - Mumun yüksek seviyesi EMA20'ye yakın olsun
    - Ya da mum bu iki ortalamanın bölgesine temas etsin
    """
    tolerans = tolerans_yuzde / 100.0
    alt_bant = ema50 * (1 - tolerans)
    ust_bant = ema20 * (1 + tolerans)

    mum_low = float(son_mum["Low"])
    mum_high = float(son_mum["High"])
    kapanis = float(son_mum["Close"])

    kosul = (
        (alt_bant <= kapanis <= ust_bant)
        or (mum_low <= ust_bant and mum_high >= alt_bant)
        or (alt_bant <= mum_low <= ust_bant)
        or (alt_bant <= mum_high <= ust_bant)
    )

    return kosul, round(alt_bant, 2), round(ust_bant, 2)


def macd_ayi_mum_sayisi(df: pd.DataFrame) -> int:
    """Son mumdan geriye doğru MACD'nin kaç mum ayıda kaldığını sayar."""
    sayi = 0
    for i in range(1, min(len(df), 30) + 1):
        satir = df.iloc[-i]
        if float(satir["MACD"]) < float(satir["MACD_SIGNAL"]):
            sayi += 1
        else:
            break
    return sayi


def kosullari_kontrol_et(df: pd.DataFrame, filtre: dict) -> dict:
    son = df.iloc[-1]
    onceki = df.iloc[-2]

    ema20 = float(son["EMA20"])
    ema50 = float(son["EMA50"])
    ema100 = float(son["EMA100"])
    ema200 = float(son["EMA200"])

    k_son = float(son["STOCH_K"])
    d_son = float(son["STOCH_D"])
    k_onceki = float(onceki["STOCH_K"])
    d_onceki = float(onceki["STOCH_D"])

    macd_son = float(son["MACD"])
    macd_signal_son = float(son["MACD_SIGNAL"])
    fiyat = float(son["Close"])

    sonuc = {
        "gecti": False,
        "fiyat": round(fiyat, 2),
        "kosullar": {},
        "detay": {
            "EMA20": round(ema20, 2),
            "EMA50": round(ema50, 2),
            "EMA100": round(ema100, 2),
            "EMA200": round(ema200, 2),
            "STOCH_K": round(k_son, 2),
            "STOCH_D": round(d_son, 2),
            "MACD": round(macd_son, 4),
            "MACD_SIGNAL": round(macd_signal_son, 4),
        },
    }

    # 1) EMA yükseliş trendi
    if filtre.get("cb_ema_trend", True):
        sonuc["kosullar"]["ema_trend"] = ema20 > ema50 > ema100 > ema200
    else:
        sonuc["kosullar"]["ema_trend"] = True

    # 2) Mum çubukları + EMA bölgesi teyidi
    if filtre.get("cb_mum_ema", True):
        mum_ok, alt_bant, ust_bant = mum_ema_teyidi(
            son,
            ema20=ema20,
            ema50=ema50,
            tolerans_yuzde=filtre.get("mum_tolerans", 2),
        )
        sonuc["kosullar"]["mum_ema"] = mum_ok
        sonuc["detay"]["EMA_BANT_ALT"] = alt_bant
        sonuc["detay"]["EMA_BANT_UST"] = ust_bant
    else:
        sonuc["kosullar"]["mum_ema"] = True

    # 3) Stochastic aşırı satım + dönüş sinyali
    if filtre.get("cb_stoch", True):
        esik = filtre.get("stoch_esik", 30)
        asiri_satim = (k_son < esik) and (d_son < esik)
        kesisim = (k_son > d_son) and (k_onceki <= d_onceki)
        sonuc["kosullar"]["stoch"] = asiri_satim and kesisim
    else:
        sonuc["kosullar"]["stoch"] = True

    # 4) MACD boğa veya kısa süreli ayı
    if filtre.get("cb_macd", True):
        boga = macd_son > macd_signal_son
        ayi_mum = 0 if boga else macd_ayi_mum_sayisi(df)
        sonuc["kosullar"]["macd"] = boga or (ayi_mum <= filtre.get("macd_mum_esik", 5))
        sonuc["detay"]["AYI_MUM_SAYISI"] = ayi_mum
    else:
        sonuc["kosullar"]["macd"] = True
        sonuc["detay"]["AYI_MUM_SAYISI"] = 0

    sonuc["gecti"] = all(sonuc["kosullar"].values())
    return sonuc


def hisse_analiz_et(ticker: str, filtre: dict | None = None) -> dict | None:
    """Tek bir hisseyi analiz eder."""
    if filtre is None:
        filtre = VARSAYILAN_FILTRE.copy()

    df = veri_cek(ticker)
    if df is None:
        return None

    df = indiktorleri_hesapla(df)
    df = df.dropna().copy()

    if len(df) < 5:
        return None

    try:
        sonuc = kosullari_kontrol_et(df, filtre)
        sonuc["ticker"] = ticker.replace(".IS", "")
        return sonuc
    except Exception:
        return None
