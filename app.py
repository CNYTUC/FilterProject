import time
import pandas as pd
import streamlit as st

from analiz import hisse_analiz_et
from hisseler import BIST_HISSELER
from strateji_xml import (
    strateji_listesi,
    strateji_yukle,
    strateji_ekle,
    strateji_guncelle,
    strateji_sil,
    xml_icerik_goster,
)

st.set_page_config(
    page_title="BIST Gün Sonu Tarayıcı",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp {max-width: 1400px; margin: auto;}
        .metric-box {
            background: #111827;
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 14px;
            text-align: center;
        }
        .metric-title {font-size: 0.80rem; color: #9ca3af;}
        .metric-value {font-size: 1.6rem; font-weight: 700; color: #60a5fa;}
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session() -> None:
    varsayilanlar = {
        "sonuclar": [],
        "tarama_yapildi": False,
        "cb_ema_trend": True,
        "cb_mum_ema": True,
        "mum_tolerans": 2,
        "cb_stoch": True,
        "stoch_esik": 30,
        "cb_macd": True,
        "macd_mum_esik": 5,
        "strateji_adi": "",
        "bildirim": None,
        "bildirim_tip": "info",
    }
    for anahtar, deger in varsayilanlar.items():
        if anahtar not in st.session_state:
            st.session_state[anahtar] = deger


init_session()


def mevcut_ayarlar() -> dict:
    return {
        "EMA_Trend_Enabled": 1 if st.session_state["cb_ema_trend"] else 0,
        "Mum_EMA_Enabled": 1 if st.session_state["cb_mum_ema"] else 0,
        "Mum_EMA_Set1": st.session_state["mum_tolerans"],
        "Stochastic_Enabled": 1 if st.session_state["cb_stoch"] else 0,
        "Stochastic_Set1": st.session_state["stoch_esik"],
        "MACD_Enabled": 1 if st.session_state["cb_macd"] else 0,
        "MACD_Set1": st.session_state["macd_mum_esik"],
    }


def strateji_uygula(veri: dict) -> None:
    st.session_state["cb_ema_trend"] = bool(veri.get("EMA_Trend_Enabled", 1))
    st.session_state["cb_mum_ema"] = bool(veri.get("Mum_EMA_Enabled", 1))
    st.session_state["mum_tolerans"] = int(veri.get("Mum_EMA_Set1", 2))
    st.session_state["cb_stoch"] = bool(veri.get("Stochastic_Enabled", 1))
    st.session_state["stoch_esik"] = int(veri.get("Stochastic_Set1", 30))
    st.session_state["cb_macd"] = bool(veri.get("MACD_Enabled", 1))
    st.session_state["macd_mum_esik"] = int(veri.get("MACD_Set1", 5))


with st.sidebar:
    st.header("⚙️ Filtre ve Strateji")

    st.subheader("📂 Strateji Yönetimi")
    liste = strateji_listesi()
    secenekler = ["— Strateji Seç —"] + liste
    secili_strateji = st.selectbox("Kayıtlı Stratejiler", options=secenekler, index=0)
    st.text_input("Strateji Adı", key="strateji_adi_input", placeholder="Örn: Gün sonu tarama")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Yükle", use_container_width=True):
            if secili_strateji == "— Strateji Seç —":
                st.session_state["bildirim"] = "Önce listeden bir strateji seç."
                st.session_state["bildirim_tip"] = "warning"
            else:
                veri = strateji_yukle(secili_strateji)
                if veri:
                    strateji_uygula(veri)
                    st.session_state["strateji_adi_input"] = secili_strateji
                    st.session_state["bildirim"] = f"{secili_strateji} yüklendi."
                    st.session_state["bildirim_tip"] = "success"
                    st.rerun()
    with c2:
        if st.button("Ekle", use_container_width=True):
            ok, mesaj = strateji_ekle(st.session_state["strateji_adi"].strip(), mevcut_ayarlar())
            st.session_state["bildirim"] = mesaj
            st.session_state["bildirim_tip"] = "success" if ok else "error"
            if ok:
                st.rerun()
    with c3:
        if st.button("Güncelle", use_container_width=True):
            ok, mesaj = strateji_guncelle(st.session_state["strateji_adi"].strip(), mevcut_ayarlar())
            st.session_state["bildirim"] = mesaj
            st.session_state["bildirim_tip"] = "success" if ok else "error"
            if ok:
                st.rerun()

    c4, c5 = st.columns(2)
    with c4:
        if st.button("Temizle", use_container_width=True):
            st.session_state["strateji_adi_input"] = ""
            st.session_state["bildirim"] = "Seçim temizlendi."
            st.session_state["bildirim_tip"] = "info"
            st.rerun()
    with c5:
        if st.button("Sil", use_container_width=True):
            ad = st.session_state["strateji_adi_input"].strip() or (
                secili_strateji if secili_strateji != "— Strateji Seç —" else ""
            )
            ok, mesaj = strateji_sil(ad)
            st.session_state["bildirim"] = mesaj
            st.session_state["bildirim_tip"] = "success" if ok else "error"
            if ok:
                st.session_state["strateji_adi_input"] = ""
                st.rerun()

    if st.session_state["bildirim"]:
        tip = st.session_state["bildirim_tip"]
        mesaj = st.session_state["bildirim"]
        {
            "success": st.success,
            "error": st.error,
            "warning": st.warning,
            "info": st.info,
        }[tip](mesaj)

    st.divider()
    st.subheader("📌 Teknik Koşullar")

    st.checkbox("EMA yükseliş trendi (20 > 50 > 100 > 200)", key="cb_ema_trend")
    st.checkbox("Mum çubukları EMA bölgesinde", key="cb_mum_ema")
    if st.session_state["cb_mum_ema"]:
        st.slider("EMA bölgesi toleransı (%)", 1, 10, key="mum_tolerans")

    st.checkbox("Stochastic (5,3,3) aşırı satım + dönüş", key="cb_stoch")
    if st.session_state["cb_stoch"]:
        st.slider("Stochastic eşik", 10, 40, key="stoch_esik")

    st.checkbox("MACD (50,100,9) boğa / kısa ayı", key="cb_macd")
    if st.session_state["cb_macd"]:
        st.slider("Ayı mum sayısı üst sınırı", 1, 10, key="macd_mum_esik")

    st.divider()
    st.subheader("📋 Hisse Seçimi")
    tumunu_tara = st.checkbox("Tüm BIST listesini tara", value=True)

    if tumunu_tara:
        taranacak_hisseler = BIST_HISSELER
    else:
        secilenler = st.multiselect(
            "Hisseler",
            options=[h.replace(".IS", "") for h in BIST_HISSELER],
            default=["THYAO", "GARAN", "ASELS"],
        )
        taranacak_hisseler = [f"{h}.IS" for h in secilenler]

    st.caption(f"Toplam {len(taranacak_hisseler)} hisse taranacak.")

    with st.expander("XML önizleme"):
        st.code(xml_icerik_goster(), language="xml")


st.title("📈 BIST Gün Sonu Teknik Sinyal Tarayıcı")
st.write(
    "Bu ekran, günlük kapanış verisine göre BIST hisselerinde teknik filtreleme yapmak için hazırlandı."
)

aktif_kosullar = []
if st.session_state["cb_ema_trend"]:
    aktif_kosullar.append("EMA Trend")
if st.session_state["cb_mum_ema"]:
    aktif_kosullar.append(f"Mum + EMA Bölgesi (%{st.session_state['mum_tolerans']})")
if st.session_state["cb_stoch"]:
    aktif_kosullar.append(f"Stochastic < {st.session_state['stoch_esik']}")
if st.session_state["cb_macd"]:
    aktif_kosullar.append(f"MACD Ayı ≤ {st.session_state['macd_mum_esik']} mum")

if aktif_kosullar:
    st.info("Aktif koşullar: " + " | ".join(aktif_kosullar))
else:
    st.warning("Hiç koşul seçilmedi.")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f'<div class="metric-box"><div class="metric-title">TARANACAK HİSSE</div><div class="metric-value">{len(taranacak_hisseler)}</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    sinyal_sayisi = len([x for x in st.session_state["sonuclar"] if x.get("gecti")])
    st.markdown(
        f'<div class="metric-box"><div class="metric-title">SİNYAL VEREN</div><div class="metric-value">{sinyal_sayisi}</div></div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f'<div class="metric-box"><div class="metric-title">AKTİF KOŞUL</div><div class="metric-value">{len(aktif_kosullar)}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")

if st.button("🔍 Taramayı Başlat", use_container_width=True):
    if not aktif_kosullar:
        st.error("En az bir koşul seçmelisin.")
    elif not taranacak_hisseler:
        st.error("En az bir hisse seçmelisin.")
    else:
        st.session_state["sonuclar"] = []
        st.session_state["tarama_yapildi"] = False

        filtre = {
            "cb_ema_trend": st.session_state["cb_ema_trend"],
            "cb_mum_ema": st.session_state["cb_mum_ema"],
            "mum_tolerans": st.session_state["mum_tolerans"],
            "cb_stoch": st.session_state["cb_stoch"],
            "stoch_esik": st.session_state["stoch_esik"],
            "cb_macd": st.session_state["cb_macd"],
            "macd_mum_esik": st.session_state["macd_mum_esik"],
        }

        progress = st.progress(0)
        durum = st.empty()
        toplam = len(taranacak_hisseler)

        for i, ticker in enumerate(taranacak_hisseler, start=1):
            durum.write(f"Analiz ediliyor: {ticker} ({i}/{toplam})")
            sonuc = hisse_analiz_et(ticker, filtre)
            if sonuc:
                st.session_state["sonuclar"].append(sonuc)
            progress.progress(i / toplam)
            time.sleep(0.03)

        progress.empty()
        durum.empty()
        st.session_state["tarama_yapildi"] = True
        st.success(f"Tarama tamamlandı. {toplam} hisse kontrol edildi.")


if st.session_state["tarama_yapildi"] and st.session_state["sonuclar"]:
    tum_sonuclar = st.session_state["sonuclar"]
    sinyal_verenler = [x for x in tum_sonuclar if x["gecti"]]

    tab1, tab2, tab3 = st.tabs([
        f"✅ Sinyal Verenler ({len(sinyal_verenler)})",
        f"📊 Tüm Sonuçlar ({len(tum_sonuclar)})",
        "🗂️ XML",
    ])

    with tab1:
        if not sinyal_verenler:
            st.info("Bu filtrelere göre sinyal veren hisse bulunamadı.")
        else:
            satirlar = []
            for s in sinyal_verenler:
                d = s["detay"]
                satirlar.append(
                    {
                        "Hisse": s["ticker"],
                        "Fiyat": s["fiyat"],
                        "EMA20": d.get("EMA20"),
                        "EMA50": d.get("EMA50"),
                        "EMA100": d.get("EMA100"),
                        "EMA200": d.get("EMA200"),
                        "Stoch K": d.get("STOCH_K"),
                        "Stoch D": d.get("STOCH_D"),
                        "MACD": d.get("MACD"),
                        "MACD Sinyal": d.get("MACD_SIGNAL"),
                        "Ayı Mum": d.get("AYI_MUM_SAYISI"),
                    }
                )

            df = pd.DataFrame(satirlar)
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "CSV indir",
                data=csv,
                file_name="bist_gun_sonu_sinyaller.csv",
                mime="text/csv",
            )

    with tab2:
        satirlar = []
        for s in tum_sonuclar:
            kosullar = s["kosullar"]
            satirlar.append(
                {
                    "Hisse": s["ticker"],
                    "Fiyat": s["fiyat"],
                    "EMA Trend": "✅" if kosullar.get("ema_trend") else "❌",
                    "Mum + EMA": "✅" if kosullar.get("mum_ema") else "❌",
                    "Stochastic": "✅" if kosullar.get("stoch") else "❌",
                    "MACD": "✅" if kosullar.get("macd") else "❌",
                    "Sonuç": "🎯 Sinyal" if s["gecti"] else "—",
                }
            )
        df2 = pd.DataFrame(satirlar)
        st.dataframe(df2, use_container_width=True, hide_index=True)

    with tab3:
        st.code(xml_icerik_goster(), language="xml")

st.divider()
st.caption(
    "Bu uygulama eğitim ve tarama amaçlıdır. Yatırım tavsiyesi değildir. Veriler Yahoo Finance üzerinden alınır."
)
