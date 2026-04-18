import time
import pandas as pd
import streamlit as st

from hisseler import BIST_HISSELER
from indicators import INDICATORS
from analiz import hisse_analiz_et, VARSAYILAN_FILTRE
from strateji_xml import (
    strateji_listesi,
    strateji_yukle,
    strateji_ekle,
    strateji_guncelle,
    strateji_sil,
    xml_icerik_goster,
)

st.set_page_config(
    page_title="BIST Sinyal Tarayıcı",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Space Mono', monospace; }
    .metric-card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 10px; padding: 16px; text-align: center;
    }
    .metric-card .label { color: #8b949e; font-size: 0.8rem; }
    .metric-card .value { color: #58a6ff; font-size: 1.8rem; font-weight: 700; font-family: 'Space Mono'; }
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


def _init():
    defaults = {
        "sonuclar": [],
        "tarama_yapildi": False,
        "strateji_adi": "",
        "bildirim": None,
        "bildirim_tip": "info",
    }
    defaults.update(VARSAYILAN_FILTRE.copy())

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def mevcut_ayarlar_al() -> dict:
    """
    XML içine yazmak için tüm aktif/pasif ve parametre değerlerini düz dict halinde toplar.
    """
    ayarlar = {}
    for key, meta in INDICATORS.items():
        ayarlar[f"cb_{key}"] = 1 if st.session_state.get(f"cb_{key}", False) else 0
        for param_key in meta.get("params", {}).keys():
            ayarlar[param_key] = st.session_state.get(param_key)
    return ayarlar


def strateji_uygula(veri: dict):
    """
    XML'den gelen stratejiyi session_state'e uygular.
    Eski strateji dosyalarında olmayan yeni alanlar varsayılanda kalır.
    """
    for key, meta in INDICATORS.items():
        cb_key = f"cb_{key}"
        if cb_key in veri:
            st.session_state[cb_key] = bool(veri.get(cb_key, 0))

        for param_key, param_meta in meta.get("params", {}).items():
            if param_key in veri:
                varsayilan = param_meta.get("default")
                try:
                    if isinstance(varsayilan, float):
                        st.session_state[param_key] = float(veri[param_key])
                    else:
                        st.session_state[param_key] = int(veri[param_key])
                except Exception:
                    st.session_state[param_key] = varsayilan


def filtre_ozet_metinleri():
    aktif = []
    for key, meta in INDICATORS.items():
        if st.session_state.get(f"cb_{key}", False):
            if key == "ema_trend":
                aktif.append("📐 EMA Trend")
            elif key == "fiyat_band":
                aktif.append(f"🎯 Fiyat Bandı ±{st.session_state.get('fiyat_tolerans', 2)}%")
            elif key == "stochastic":
                aktif.append(f"📉 Stoch < {st.session_state.get('stoch_esik', 30)}")
            elif key == "macd":
                aktif.append(f"📊 MACD ≤ {st.session_state.get('macd_mum_esik', 5)} ayı mum")
            elif key == "rsi":
                aktif.append(f"🌀 RSI < {st.session_state.get('rsi_esik', 30)}")
            elif key == "bollinger":
                aktif.append("🌐 Bollinger Alt Band")
            else:
                aktif.append(meta["label"])
    return aktif


_init()

with st.sidebar:
    st.markdown("### 📂 Strateji Yönetimi")

    liste = strateji_listesi()
    secenekler = ["— Strateji Seç —"] + liste
    secili_strateji = st.selectbox(
        "Kayıtlı Stratejiler",
        options=secenekler,
        index=0,
        help="Listeden strateji seçip yükleyebilirsin."
    )

    strateji_adi_input = st.text_input(
        "Strateji Adı",
        value=st.session_state.get("strateji_adi", ""),
        placeholder="Örn: Gün sonu tarama"
    )
    st.session_state["strateji_adi"] = strateji_adi_input

    b1, b2, b3 = st.columns(3)
    b4, b5 = st.columns(2)

    with b1:
        if st.button("📥 Yükle", use_container_width=True):
            if secili_strateji == "— Strateji Seç —":
                st.session_state.update(bildirim="Listeden bir strateji seçin.", bildirim_tip="warning")
            else:
                veri = strateji_yukle(secili_strateji)
                if veri:
                    strateji_uygula(veri)
                    st.session_state["strateji_adi"] = secili_strateji
                    st.session_state.update(
                        bildirim=f"✅ '{secili_strateji}' yüklendi.",
                        bildirim_tip="success"
                    )
                    st.rerun()

    with b2:
        if st.button("➕ Ekle", use_container_width=True):
            ad = st.session_state.get("strateji_adi", "").strip()
            ok, msg = strateji_ekle(ad, mevcut_ayarlar_al())
            st.session_state.update(bildirim=msg, bildirim_tip="success" if ok else "error")
            if ok:
                st.rerun()

    with b3:
        if st.button("✏️ Güncelle", use_container_width=True):
            ad = st.session_state.get("strateji_adi", "").strip()
            if not ad:
                st.session_state.update(bildirim="Strateji adını girin.", bildirim_tip="warning")
            else:
                ok, msg = strateji_guncelle(ad, mevcut_ayarlar_al())
                st.session_state.update(bildirim=msg, bildirim_tip="success" if ok else "error")
                if ok:
                    st.rerun()

    with b4:
        if st.button("🙈 Kaldır", use_container_width=True):
            st.session_state["strateji_adi"] = ""
            st.session_state.update(
                bildirim="Seçim kaldırıldı. Kalıcı silmek için 'Sil' kullanın.",
                bildirim_tip="info"
            )
            st.rerun()

    with b5:
        if st.button("🗑️ Sil", use_container_width=True):
            ad = st.session_state.get("strateji_adi", "").strip() or (
                secili_strateji if secili_strateji != "— Strateji Seç —" else ""
            )
            if not ad:
                st.session_state.update(bildirim="Silinecek strateji adını girin.", bildirim_tip="warning")
            else:
                ok, msg = strateji_sil(ad)
                st.session_state.update(bildirim=msg, bildirim_tip="success" if ok else "error")
                if ok:
                    st.session_state["strateji_adi"] = ""
                    st.rerun()

    if st.session_state["bildirim"]:
        tip = st.session_state["bildirim_tip"]
        msg = st.session_state["bildirim"]
        {"success": st.success, "error": st.error,
         "warning": st.warning, "info": st.info}[tip](msg)

    st.divider()
    st.markdown("### ⚙️ Filtre Ayarları")
    st.caption("İşaretlenen koşullar taramaya dahil edilir.")

    for key, meta in INDICATORS.items():
        with st.container(border=True):
            cb_key = f"cb_{key}"

            help_text = f"({meta.get('help')})" if meta.get("help") else ""

            st.checkbox(
                f"{meta['label']} {help_text}",
                key=cb_key
            )


            if st.session_state.get(cb_key, False):
                for param_key, param_meta in meta.get("params", {}).items():
                    input_label = param_meta.get("label", param_key)
                    input_type = param_meta.get("type", "int")
                    default = param_meta.get("default")
                    min_value = param_meta.get("min")
                    max_value = param_meta.get("max")
                    step = param_meta.get("step", 1)

                    if input_type == "float":
                        st.number_input(
                            input_label,
                            min_value=float(min_value),
                            max_value=float(max_value),
                            step=float(step),
                            key=param_key,
                        )
                    else:
                        st.number_input(
                            input_label,
                            min_value=int(min_value),
                            max_value=int(max_value),
                            step=int(step),
                            key=param_key,
                        )

    st.divider()
    st.markdown("### 📋 Hisse Seçimi")
    tum_hisseler = st.checkbox("Tüm Listeyi Tara", value=True)
    if not tum_hisseler:
        secili_hisse = st.multiselect(
            "Hisseleri Seç",
            options=[h.replace(".IS", "") for h in BIST_HISSELER],
            default=["THYAO", "GARAN", "ASELS"]
        )
        taranacak = [f"{h}.IS" for h in secili_hisse]
    else:
        taranacak = BIST_HISSELER

    st.markdown(f"**{len(taranacak)}** hisse taranacak.")

    with st.expander("🗂️ stratejiler.xml önizleme"):
        st.code(xml_icerik_goster(), language="xml")


st.markdown("## 📈 BIST Teknik Sinyal Tarayıcı")
st.markdown("*Gün sonu tarama · Dinamik indikatör paneli · XML strateji kaydı*")
st.divider()

aktif = filtre_ozet_metinleri()
if aktif:
    st.info("**Aktif Koşullar:** " + " | ".join(aktif))
else:
    st.warning("⚠️ Hiçbir koşul seçilmedi.")

col1, col2, col3, col4 = st.columns(4)
sinyal_sayisi = len([s for s in st.session_state["sonuclar"] if s.get("gecti")])
strat_adi_goster = (st.session_state.get("strateji_adi") or "—")[:18]

with col1:
    st.markdown(
        f'<div class="metric-card"><div class="label">TARANAN HİSSE</div><div class="value">{len(taranacak)}</div></div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f'<div class="metric-card"><div class="label">SİNYAL VEREN</div><div class="value" style="color:#3fb950">{sinyal_sayisi}</div></div>',
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        f'<div class="metric-card"><div class="label">AKTİF KOŞUL</div><div class="value">{len(aktif)}</div></div>',
        unsafe_allow_html=True
    )
with col4:
    st.markdown(
        f'<div class="metric-card"><div class="label">STRATEJİ</div><div class="value" style="font-size:1rem;padding-top:8px">{strat_adi_goster}</div></div>',
        unsafe_allow_html=True
    )

st.markdown("")

if st.button("🔍 Taramayı Başlat", use_container_width=True):
    if not aktif:
        st.error("En az bir koşul seçmelisiniz!")
    elif not taranacak:
        st.error("En az bir hisse seçmelisiniz!")
    else:
        st.session_state["sonuclar"] = []
        ilerleme = st.progress(0)
        durum_yazisi = st.empty()
        toplam = len(taranacak)

        filtre = {}
        for key, meta in INDICATORS.items():
            filtre[f"cb_{key}"] = st.session_state.get(f"cb_{key}", False)
            for param_key in meta.get("params", {}).keys():
                filtre[param_key] = st.session_state.get(param_key)

        for i, ticker in enumerate(taranacak):
            durum_yazisi.markdown(f"⏳ `{ticker}` analiz ediliyor... ({i+1}/{toplam})")
            ilerleme.progress((i + 1) / toplam)
            sonuc = hisse_analiz_et(ticker, filtre)
            if sonuc:
                st.session_state["sonuclar"].append(sonuc)
            time.sleep(0.03)

        ilerleme.empty()
        durum_yazisi.empty()
        st.session_state["tarama_yapildi"] = True
        st.success(f"✅ Tarama tamamlandı! {toplam} hisse analiz edildi.")


if st.session_state["tarama_yapildi"] and st.session_state["sonuclar"]:
    tum_sonuclar = st.session_state["sonuclar"]
    sinyal_verenler = [s for s in tum_sonuclar if s["gecti"]]

    tab1, tab2, tab3 = st.tabs([
        f"✅ Sinyal Verenler ({len(sinyal_verenler)})",
        f"📊 Tüm Sonuçlar ({len(tum_sonuclar)})",
        "🗂️ XML İçeriği",
    ])

    with tab1:
        if not sinyal_verenler:
            st.info("Sinyal veren hisse bulunamadı.")
        else:
            rows = []
            for s in sinyal_verenler:
                d = s["detay"]
                rows.append({
                    "Hisse": s["ticker"],
                    "Fiyat": s["fiyat"],
                    "EMA20": d.get("EMA20", "-"),
                    "EMA50": d.get("EMA50", "-"),
                    "EMA100": d.get("EMA100", "-"),
                    "EMA200": d.get("EMA200", "-"),
                    "Stoch %K": d.get("STOCH_K", "-"),
                    "Stoch %D": d.get("STOCH_D", "-"),
                    "MACD": d.get("MACD", "-"),
                    "MACD Signal": d.get("MACD_SIGNAL", "-"),
                    "Ayı Mum": d.get("ayida_mum", 0),
                    "RSI": d.get("RSI", "-"),
                    "BB Low": d.get("BB_LOW", "-"),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ CSV İndir",
                data=csv,
                file_name="bist_sinyaller.csv",
                mime="text/csv"
            )

    with tab2:
        rows2 = []
        for s in tum_sonuclar:
            k = s["kosullar"]
            rows2.append({
                "Hisse": s["ticker"],
                "Fiyat": s["fiyat"],
                "EMA Trend": "✅" if k.get("ema_trend") else ("—" if not st.session_state.get("cb_ema_trend", False) else "❌"),
                "Fiyat Bandı": "✅" if k.get("fiyat_band") else ("—" if not st.session_state.get("cb_fiyat_band", False) else "❌"),
                "Stochastic": "✅" if k.get("stochastic") else ("—" if not st.session_state.get("cb_stochastic", False) else "❌"),
                "MACD": "✅" if k.get("macd") else ("—" if not st.session_state.get("cb_macd", False) else "❌"),
                "RSI": "✅" if k.get("rsi") else ("—" if not st.session_state.get("cb_rsi", False) else "❌"),
                "Bollinger": "✅" if k.get("bollinger") else ("—" if not st.session_state.get("cb_bollinger", False) else "❌"),
                "Sonuç": "🎯 SİNYAL" if s["gecti"] else "—"
            })
        df2 = pd.DataFrame(rows2).sort_values("Sonuç", ascending=False).reset_index(drop=True)
        st.dataframe(df2, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### 🗂️ stratejiler.xml")
        st.code(xml_icerik_goster(), language="xml")

st.divider()
st.markdown("""<small style="color:#8b949e">
📌 Sol panel artık indicators.py dosyasından dinamik üretilir.<br>
📌 XML strateji kaydı korunur.<br>
⚠️ <i>Bu uygulama yatırım tavsiyesi değildir. Veriler Yahoo Finance üzerinden çekilmektedir.</i>
</small>""", unsafe_allow_html=True)
