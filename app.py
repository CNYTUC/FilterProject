import streamlit as st
import pandas as pd
import time
from hisseler import BIST_HISSELER
from analiz import hisse_analiz_et
from strateji_db import (
    strateji_listesi, strateji_yukle,
    strateji_ekle, strateji_guncelle,
    strateji_sil, strateji_tablo, db_bilgi
)

# ── Sayfa Ayarları ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BIST Sinyal Tarayıcı",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
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


# ── Session State ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        "sonuclar": [], "tarama_yapildi": False,
        "cb_ema_trend": True, "cb_stoch": True,
        "cb_macd": True, "cb_fiyat_band": True,
        "stoch_esik": 30, "macd_mum_esik": 5, "fiyat_tolerans": 2,
        "strateji_adi_input": "", "bildirim": None, "bildirim_tip": "info",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


def mevcut_ayarlar_al() -> dict:
    return {
        "Stochastic_Enabled":   1 if st.session_state["cb_stoch"]      else 0,
        "Stochastic_Set1":      st.session_state["stoch_esik"],
        "MACD_Enabled":         1 if st.session_state["cb_macd"]        else 0,
        "MACD_Set1":            st.session_state["macd_mum_esik"],
        "EMA_Tolerans_Enabled": 1 if st.session_state["cb_fiyat_band"]  else 0,
        "EMA_Tolerans_Set1":    st.session_state["fiyat_tolerans"],
        "EMA_Trend_Enabled":    1 if st.session_state["cb_ema_trend"]   else 0,
        "Fiyat_Band_Enabled":   1 if st.session_state["cb_fiyat_band"]  else 0,
    }

def strateji_uygula(veri: dict):
    st.session_state["cb_stoch"]       = bool(veri.get("Stochastic_Enabled", 0))
    st.session_state["stoch_esik"]     = int(veri.get("Stochastic_Set1", 30))
    st.session_state["cb_macd"]        = bool(veri.get("MACD_Enabled", 0))
    st.session_state["macd_mum_esik"]  = int(veri.get("MACD_Set1", 5))
    st.session_state["cb_fiyat_band"]  = bool(veri.get("EMA_Tolerans_Enabled", 0))
    st.session_state["fiyat_tolerans"] = int(veri.get("EMA_Tolerans_Set1", 2))
    st.session_state["cb_ema_trend"]   = bool(veri.get("EMA_Trend_Enabled", 0))


# ═══════════════════════════════════════════════════════════════════════════════
# SOL PANEL
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Strateji Dropdown ────────────────────────────────────────────────────
    st.markdown("### 📂 Strateji Yönetimi")

    liste     = strateji_listesi()
    secenekler = ["— Strateji Seç —"] + liste
    secili_strateji = st.selectbox(
        "Kayıtlı Stratejiler",
        options=secenekler, index=0,
        help="Listeden bir strateji seçip 'Yükle' butonuna basın."
    )

    # ── Strateji Adı ─────────────────────────────────────────────────────────
    st.text_input("Strateji Adı", placeholder="Örn: Stratejim 1", key="strateji_adi_input")

    # ── 5 Buton ──────────────────────────────────────────────────────────────
    b1, b2, b3 = st.columns(3)
    b4, b5     = st.columns(2)

    with b1:
        if st.button("📥 Yükle", use_container_width=True, help="Seçili stratejiyi yükle"):
            if secili_strateji == "— Strateji Seç —":
                st.session_state.update(bildirim="Listeden bir strateji seçin.", bildirim_tip="warning")
            else:
                veri = strateji_yukle(secili_strateji)
                if veri:
                    strateji_uygula(veri)
                    st.session_state["strateji_adi_input"] = secili_strateji
                    st.session_state.update(bildirim=f"✅ '{secili_strateji}' yüklendi.", bildirim_tip="success")
                    st.rerun()

    with b2:
        if st.button("➕ Ekle", use_container_width=True, help="Yeni strateji olarak kaydet"):
            ad = st.session_state["strateji_adi_input"].strip()
            ok, msg = strateji_ekle(ad, mevcut_ayarlar_al())
            st.session_state.update(bildirim=msg, bildirim_tip="success" if ok else "error")
            if ok: st.rerun()

    with b3:
        if st.button("✏️ Güncelle", use_container_width=True, help="Mevcut stratejiyi güncelle"):
            ad = st.session_state["strateji_adi_input"].strip()
            if not ad:
                st.session_state.update(bildirim="Strateji adını girin.", bildirim_tip="warning")
            else:
                ok, msg = strateji_guncelle(ad, mevcut_ayarlar_al())
                st.session_state.update(bildirim=msg, bildirim_tip="success" if ok else "error")
                if ok: st.rerun()

    with b4:
        if st.button("🙈 Kaldır", use_container_width=True, help="Seçimi sıfırla (kalıcı değil)"):
            st.session_state.update(
                bildirim="Seçim kaldırıldı. Kalıcı silmek için 'Sil' kullanın.",
                bildirim_tip="info"
            )
            st.rerun()

    with b5:
        if st.button("🗑️ Sil", use_container_width=True, help="Stratejiyi kalıcı sil"):
            ad = st.session_state["strateji_adi_input"].strip() or (
                secili_strateji if secili_strateji != "— Strateji Seç —" else "")
            if not ad:
                st.session_state.update(bildirim="Silinecek strateji adını girin.", bildirim_tip="warning")
            else:
                ok, msg = strateji_sil(ad)
                st.session_state.update(bildirim=msg, bildirim_tip="success" if ok else "error")
                if ok:
                    st.session_state["strateji_adi_input"] = ""
                    st.rerun()

    # ── Bildirim ─────────────────────────────────────────────────────────────
    if st.session_state["bildirim"]:
        tip = st.session_state["bildirim_tip"]
        msg = st.session_state["bildirim"]
        {"success": st.success, "error": st.error,
         "warning": st.warning, "info": st.info}[tip](msg)

    st.divider()

    # ── Filtre Ayarları (Checkbox + Slider) ──────────────────────────────────
    st.markdown("### ⚙️ Filtre Ayarları")
    st.caption("İşaretlenen koşullar taramaya dahil edilir.")

    # EMA Trend
    with st.container(border=True):
        st.checkbox("📐 EMA Yükseliş Trendi *(20 > 50 > 100 > 200)*",
                    key="cb_ema_trend")

    # Stochastic
    with st.container(border=True):
        st.checkbox("📉 Stochastic (5,3,3) Aşırı Satım", key="cb_stoch")
        if st.session_state["cb_stoch"]:
            st.slider("Stochastic Eşiği (üst sınır)",
                      min_value=10, max_value=40, step=5, key="stoch_esik")

    # MACD
    with st.container(border=True):
        st.checkbox("📊 MACD (50,100,9) Boğa / Kısa Ayı", key="cb_macd")
        if st.session_state["cb_macd"]:
            st.slider("Ayı Mum Toleransı",
                      min_value=1, max_value=10, step=1, key="macd_mum_esik")

    # Fiyat Bandı
    with st.container(border=True):
        st.checkbox("🎯 Fiyat EMA20-EMA50 Bandında", key="cb_fiyat_band")
        if st.session_state["cb_fiyat_band"]:
            st.slider("Bant Toleransı (%)",
                      min_value=1, max_value=10, step=1, key="fiyat_tolerans")

    st.divider()

    # ── Hisse Seçimi ─────────────────────────────────────────────────────────
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

    # ── DB Önizleme ──────────────────────────────────────────────────────────
    with st.expander("🗃️ Kayıtlı Stratejiler Tablosu"):
        st.caption(db_bilgi())
        kayitlar = strateji_tablo()
        if kayitlar:
            st.dataframe(pd.DataFrame(kayitlar), use_container_width=True, hide_index=True)
        else:
            st.info("Henüz kayıtlı strateji yok.")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA İÇERİK
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📈 BIST Teknik Sinyal Tarayıcı")
st.markdown("*EMA Trendi · Stochastic (5,3,3) · MACD (50,100,9) · Günlük Mum*")
st.divider()

# Aktif koşul özeti
aktif = []
if st.session_state["cb_ema_trend"]:  aktif.append("📐 EMA Trend")
if st.session_state["cb_stoch"]:      aktif.append(f"📉 Stoch < {st.session_state['stoch_esik']}")
if st.session_state["cb_macd"]:       aktif.append(f"📊 MACD ≤{st.session_state['macd_mum_esik']} ayı mum")
if st.session_state["cb_fiyat_band"]: aktif.append(f"🎯 Fiyat Bandı ±{st.session_state['fiyat_tolerans']}%")

if aktif:
    st.info("**Aktif Koşullar:** " + "  |  ".join(aktif))
else:
    st.warning("⚠️ Hiçbir koşul seçilmedi! Sol panelden en az bir koşulu işaretleyin.")

# Metrik kartlar
col1, col2, col3, col4 = st.columns(4)
sinyal_sayisi = len([s for s in st.session_state["sonuclar"] if s.get("gecti")])
strat_adi_goster = (st.session_state.get("strateji_adi_input") or "—")[:14]

with col1:
    st.markdown(f'<div class="metric-card"><div class="label">TARANAN HİSSE</div><div class="value">{len(taranacak)}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="label">SİNYAL VEREN</div><div class="value" style="color:#3fb950">{sinyal_sayisi}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="label">AKTİF KOŞUL</div><div class="value">{len(aktif)}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="label">STRATEJİ</div><div class="value" style="font-size:1rem;padding-top:8px">{strat_adi_goster}</div></div>', unsafe_allow_html=True)

st.markdown("")

# ── Tarama Butonu ─────────────────────────────────────────────────────────────
if st.button("🔍 Taramayı Başlat", use_container_width=True):
    if not aktif:
        st.error("En az bir koşul seçmelisiniz!")
    elif not taranacak:
        st.error("En az bir hisse seçmelisiniz!")
    else:
        st.session_state["sonuclar"] = []
        ilerleme     = st.progress(0)
        durum_yazisi = st.empty()
        toplam       = len(taranacak)

        filtre = {
            "cb_ema_trend":   st.session_state["cb_ema_trend"],
            "cb_stoch":       st.session_state["cb_stoch"],
            "stoch_esik":     st.session_state["stoch_esik"],
            "cb_macd":        st.session_state["cb_macd"],
            "macd_mum_esik":  st.session_state["macd_mum_esik"],
            "cb_fiyat_band":  st.session_state["cb_fiyat_band"],
            "fiyat_tolerans": st.session_state["fiyat_tolerans"],
        }

        for i, ticker in enumerate(taranacak):
            durum_yazisi.markdown(f"⏳ `{ticker}` analiz ediliyor... ({i+1}/{toplam})")
            ilerleme.progress((i + 1) / toplam)
            sonuc = hisse_analiz_et(ticker, filtre)
            if sonuc:
                st.session_state["sonuclar"].append(sonuc)
            time.sleep(0.05)

        ilerleme.empty()
        durum_yazisi.empty()
        st.session_state["tarama_yapildi"] = True
        st.success(f"✅ Tarama tamamlandı! {toplam} hisse analiz edildi.")


# ── Sonuçlar ──────────────────────────────────────────────────────────────────
if st.session_state["tarama_yapildi"] and st.session_state["sonuclar"]:
    tum_sonuclar    = st.session_state["sonuclar"]
    sinyal_verenler = [s for s in tum_sonuclar if s["gecti"]]

    tab1, tab2, tab3 = st.tabs([
        f"✅ Sinyal Verenler ({len(sinyal_verenler)})",
        f"📊 Tüm Sonuçlar ({len(tum_sonuclar)})",
        "🗂️ XML İçeriği",
    ])

    with tab1:
        if not sinyal_verenler:
            st.info("Sinyal veren hisse bulunamadı. Filtre ayarlarını genişletmeyi deneyin.")
        else:
            st.markdown(f"### 🎯 {len(sinyal_verenler)} hisse tüm koşulları karşıladı")
            rows = []
            for s in sinyal_verenler:
                d = s["detay"]
                rows.append({
                    "Hisse": s["ticker"], "Fiyat": s["fiyat"],
                    "EMA20": d.get("EMA20","-"), "EMA50": d.get("EMA50","-"),
                    "EMA100": d.get("EMA100","-"), "EMA200": d.get("EMA200","-"),
                    "Stoch %K": d.get("STOCH_K","-"), "Stoch %D": d.get("STOCH_D","-"),
                    "MACD": d.get("MACD","-"), "MACD Sinyal": d.get("MACD_SIGNAL","-"),
                    "Ayı Mum": d.get("ayida_mum", 0),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True,
                column_config={"Fiyat": st.column_config.NumberColumn("Fiyat ₺", format="%.2f"),
                               "Stoch %K": st.column_config.NumberColumn(format="%.1f"),
                               "Stoch %D": st.column_config.NumberColumn(format="%.1f")})
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ CSV İndir", data=csv,
                               file_name="bist_sinyaller.csv", mime="text/csv")

    with tab2:
        rows2 = []
        for s in tum_sonuclar:
            k = s["kosullar"]
            rows2.append({
                "Hisse": s["ticker"], "Fiyat": s["fiyat"],
                "EMA Trend":   "✅" if k.get("yukseli_trendi") else ("—" if not st.session_state["cb_ema_trend"] else "❌"),
                "Fiyat Bandı": "✅" if k.get("fiyat_ema_band") else ("—" if not st.session_state["cb_fiyat_band"] else "❌"),
                "Stochastic":  "✅" if k.get("stochastic")      else ("—" if not st.session_state["cb_stoch"] else "❌"),
                "MACD":        "✅" if k.get("macd")             else ("—" if not st.session_state["cb_macd"] else "❌"),
                "Sonuç":       "🎯 SİNYAL" if s["gecti"] else "—",
            })
        df2 = pd.DataFrame(rows2).sort_values("Sonuç", ascending=False).reset_index(drop=True)
        st.dataframe(df2, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### 🗃️ Kayıtlı Stratejiler — stratejiler.db")
        st.caption(db_bilgi())
        kayitlar = strateji_tablo()
        if kayitlar:
            st.dataframe(pd.DataFrame(kayitlar), use_container_width=True, hide_index=True)
        else:
            st.info("Henüz kayıtlı strateji yok.")


# ── Alt bilgi ─────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""<small style="color:#8b949e">
📌 Koşullar sol panelden açılıp kapatılabilir. Stratejiler XML dosyasına kaydedilir.<br>
⚠️ <i>Bu uygulama yatırım tavsiyesi değildir. Veriler Yahoo Finance üzerinden çekilmektedir.</i>
</small>""", unsafe_allow_html=True)
