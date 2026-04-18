"""
strateji_db.py
--------------
SQLite veritabanına strateji kaydetme, yükleme, güncelleme ve silme işlemleri.

Veritabanı yapısı (stratejiler.db):

Tablo: stratejiler
┌────────────────────────┬─────────┬──────────────────────────────┐
│ Sütun                  │ Tip     │ Açıklama                     │
├────────────────────────┼─────────┼──────────────────────────────┤
│ id                     │ INTEGER │ Otomatik artan birincil anahtar│
│ ad                     │ TEXT    │ Strateji adı (benzersiz)      │
│ stochastic_enabled     │ INTEGER │ 0 = kapalı, 1 = açık         │
│ stochastic_set1        │ INTEGER │ Stochastic eşik değeri        │
│ macd_enabled           │ INTEGER │ 0 = kapalı, 1 = açık         │
│ macd_set1              │ INTEGER │ MACD ayı mum toleransı        │
│ ema_tolerans_enabled   │ INTEGER │ 0 = kapalı, 1 = açık         │
│ ema_tolerans_set1      │ INTEGER │ EMA bant toleransı (%)        │
│ ema_trend_enabled      │ INTEGER │ 0 = kapalı, 1 = açık         │
│ fiyat_band_enabled     │ INTEGER │ 0 = kapalı, 1 = açık         │
│ olusturma_tarihi       │ TEXT    │ ISO format tarih/saat         │
│ guncelleme_tarihi      │ TEXT    │ ISO format tarih/saat         │
└────────────────────────┴─────────┴──────────────────────────────┘
"""

import sqlite3
import os
from datetime import datetime

DB_DOSYA = "stratejiler.db"


# ── Bağlantı yardımcısı ───────────────────────────────────────────────────────
def _baglan() -> sqlite3.Connection:
    """
    Veritabanına bağlanır.
    row_factory ile sütun adlarına dict gibi erişim sağlar.
    """
    con = sqlite3.connect(DB_DOSYA)
    con.row_factory = sqlite3.Row   # sonuçlara row["ad"] şeklinde erişim
    return con


# ── Veritabanını başlat (tablo yoksa oluştur) ─────────────────────────────────
def db_baslat():
    """
    Uygulama başlarken bir kez çağrılır.
    Tablo zaten varsa dokunmaz (IF NOT EXISTS).
    """
    con = _baglan()
    con.execute("""
        CREATE TABLE IF NOT EXISTS stratejiler (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            ad                   TEXT    NOT NULL UNIQUE,
            stochastic_enabled   INTEGER NOT NULL DEFAULT 0,
            stochastic_set1      INTEGER NOT NULL DEFAULT 30,
            macd_enabled         INTEGER NOT NULL DEFAULT 0,
            macd_set1            INTEGER NOT NULL DEFAULT 5,
            ema_tolerans_enabled INTEGER NOT NULL DEFAULT 0,
            ema_tolerans_set1    INTEGER NOT NULL DEFAULT 2,
            ema_trend_enabled    INTEGER NOT NULL DEFAULT 0,
            fiyat_band_enabled   INTEGER NOT NULL DEFAULT 0,
            olusturma_tarihi     TEXT,
            guncelleme_tarihi    TEXT
        )
    """)
    con.commit()
    con.close()


# ── Strateji listesi ──────────────────────────────────────────────────────────
def strateji_listesi() -> list[str]:
    """
    Kayıtlı tüm strateji adlarını alfabetik sırayla döner.
    """
    db_baslat()
    con = _baglan()
    rows = con.execute("SELECT ad FROM stratejiler ORDER BY ad").fetchall()
    con.close()
    return [r["ad"] for r in rows]


# ── Strateji yükle ────────────────────────────────────────────────────────────
def strateji_yukle(ad: str) -> dict | None:
    """
    Verilen ada sahip stratejiyi dict olarak döner.
    app.py'nin beklediği anahtar formatı korunur (büyük harf).
    """
    db_baslat()
    con = _baglan()
    row = con.execute(
        "SELECT * FROM stratejiler WHERE ad = ?", (ad,)
    ).fetchone()
    con.close()

    if row is None:
        return None

    # app.py'nin strateji_uygula() fonksiyonunun beklediği format
    return {
        "Stochastic_Enabled":   row["stochastic_enabled"],
        "Stochastic_Set1":      row["stochastic_set1"],
        "MACD_Enabled":         row["macd_enabled"],
        "MACD_Set1":            row["macd_set1"],
        "EMA_Tolerans_Enabled": row["ema_tolerans_enabled"],
        "EMA_Tolerans_Set1":    row["ema_tolerans_set1"],
        "EMA_Trend_Enabled":    row["ema_trend_enabled"],
        "Fiyat_Band_Enabled":   row["fiyat_band_enabled"],
    }


# ── Strateji ekle ─────────────────────────────────────────────────────────────
def strateji_ekle(ad: str, ayarlar: dict) -> tuple[bool, str]:
    """
    Yeni strateji ekler.
    Aynı ad zaten varsa hata mesajı döner.
    """
    if not ad.strip():
        return False, "⚠️ Strateji adı boş olamaz."

    db_baslat()
    simdi = datetime.now().isoformat(sep=" ", timespec="seconds")

    try:
        con = _baglan()
        con.execute("""
            INSERT INTO stratejiler
                (ad, stochastic_enabled, stochastic_set1,
                 macd_enabled, macd_set1,
                 ema_tolerans_enabled, ema_tolerans_set1,
                 ema_trend_enabled, fiyat_band_enabled,
                 olusturma_tarihi, guncelleme_tarihi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ad.strip(),
            ayarlar.get("Stochastic_Enabled",   0),
            ayarlar.get("Stochastic_Set1",       30),
            ayarlar.get("MACD_Enabled",          0),
            ayarlar.get("MACD_Set1",             5),
            ayarlar.get("EMA_Tolerans_Enabled",  0),
            ayarlar.get("EMA_Tolerans_Set1",     2),
            ayarlar.get("EMA_Trend_Enabled",     0),
            ayarlar.get("Fiyat_Band_Enabled",    0),
            simdi, simdi,
        ))
        con.commit()
        con.close()
        return True, f"✅ '{ad}' stratejisi başarıyla kaydedildi."

    except sqlite3.IntegrityError:
        return False, f"❌ '{ad}' adında bir strateji zaten var. Farklı ad girin veya 'Güncelle' kullanın."
    except Exception as e:
        return False, f"❌ Beklenmeyen hata: {e}"


# ── Strateji güncelle ─────────────────────────────────────────────────────────
def strateji_guncelle(ad: str, yeni_ayarlar: dict) -> tuple[bool, str]:
    """
    Mevcut stratejiyi yeni ayarlarla günceller.
    """
    if not ad.strip():
        return False, "⚠️ Strateji adı boş olamaz."

    db_baslat()
    simdi = datetime.now().isoformat(sep=" ", timespec="seconds")

    con = _baglan()
    mevcut = con.execute(
        "SELECT id FROM stratejiler WHERE ad = ?", (ad,)
    ).fetchone()

    if mevcut is None:
        con.close()
        return False, f"❌ '{ad}' adında strateji bulunamadı. Önce 'Ekle' ile kaydedin."

    con.execute("""
        UPDATE stratejiler SET
            stochastic_enabled   = ?,
            stochastic_set1      = ?,
            macd_enabled         = ?,
            macd_set1            = ?,
            ema_tolerans_enabled = ?,
            ema_tolerans_set1    = ?,
            ema_trend_enabled    = ?,
            fiyat_band_enabled   = ?,
            guncelleme_tarihi    = ?
        WHERE ad = ?
    """, (
        yeni_ayarlar.get("Stochastic_Enabled",   0),
        yeni_ayarlar.get("Stochastic_Set1",       30),
        yeni_ayarlar.get("MACD_Enabled",          0),
        yeni_ayarlar.get("MACD_Set1",             5),
        yeni_ayarlar.get("EMA_Tolerans_Enabled",  0),
        yeni_ayarlar.get("EMA_Tolerans_Set1",     2),
        yeni_ayarlar.get("EMA_Trend_Enabled",     0),
        yeni_ayarlar.get("Fiyat_Band_Enabled",    0),
        simdi,
        ad,
    ))
    con.commit()
    con.close()
    return True, f"✅ '{ad}' stratejisi güncellendi."


# ── Strateji sil ──────────────────────────────────────────────────────────────
def strateji_sil(ad: str) -> tuple[bool, str]:
    """
    Stratejiyi veritabanından kalıcı olarak siler.
    """
    if not ad.strip():
        return False, "⚠️ Strateji adı boş olamaz."

    db_baslat()
    con = _baglan()
    cursor = con.execute(
        "DELETE FROM stratejiler WHERE ad = ?", (ad,)
    )
    con.commit()
    etkilenen = cursor.rowcount
    con.close()

    if etkilenen > 0:
        return True, f"🗑️ '{ad}' stratejisi silindi."
    else:
        return False, f"❌ '{ad}' adında strateji bulunamadı."


# ── DB önizleme (tüm kayıtları tablo olarak al) ───────────────────────────────
def strateji_tablo() -> list[dict]:
    """
    Tüm stratejileri sözlük listesi olarak döner.
    Sidebar'daki önizleme tablosu için kullanılır.
    """
    db_baslat()
    con = _baglan()
    rows = con.execute("""
        SELECT
            ad                              AS "Strateji Adı",
            CASE stochastic_enabled
                WHEN 1 THEN '✅ ' || stochastic_set1
                ELSE '—'
            END                             AS "Stochastic",
            CASE macd_enabled
                WHEN 1 THEN '✅ ' || macd_set1 || ' mum'
                ELSE '—'
            END                             AS "MACD",
            CASE ema_tolerans_enabled
                WHEN 1 THEN '✅ %' || ema_tolerans_set1
                ELSE '—'
            END                             AS "EMA Tolerans",
            CASE ema_trend_enabled
                WHEN 1 THEN '✅'
                ELSE '—'
            END                             AS "EMA Trend",
            guncelleme_tarihi               AS "Son Güncelleme"
        FROM stratejiler
        ORDER BY ad
    """).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ── DB dosya boyutu ───────────────────────────────────────────────────────────
def db_bilgi() -> str:
    """Sidebar'da gösterilecek kısa DB bilgisi."""
    if not os.path.exists(DB_DOSYA):
        return "Veritabanı henüz oluşturulmadı."
    boyut = os.path.getsize(DB_DOSYA)
    adet  = len(strateji_listesi())
    return f"📁 {DB_DOSYA}  |  {adet} strateji  |  {boyut:,} byte"
