"""
indicators.py
-------------
Uygulamada kullanılacak indikatörlerin tanımları.
app.py bu dosyayı okuyarak sol panelde alanları dinamik üretir.
analiz.py bu dosyadaki yapı üzerinden hesaplama ve kontrol yapar.
"""

INDICATORS = {
    "ema_trend": {
        "label": "📐 EMA Yükseliş Trendi",
        "help": "EMA20 > EMA50 > EMA100 > EMA200",
        "enabled_default": True,
        "params": {}
    },
    "fiyat_band": {
        "label": "🎯 Fiyat EMA Bandında",
        "help": "Fiyat EMA20 ve EMA50 çevresindeki tolerans bandında olacak",
        "enabled_default": True,
        "params": {
            "fiyat_tolerans": {
                "label": "Bant Toleransı (%)",
                "type": "int",
                "default": 2,
                "min": 1,
                "max": 10,
                "step": 1
            }
        }
    },
    "stochastic": {
        "label": "📉 Stochastic (5,3,3)",
        "help": "Aşırı satım + dönüş sinyali",
        "enabled_default": True,
        "params": {
            "stoch_esik": {
                "label": "Stochastic Eşiği",
                "type": "int",
                "default": 30,
                "min": 10,
                "max": 40,
                "step": 5
            }
        }
    },
    "macd": {
        "label": "📊 MACD (50,100,9)",
        "help": "Boğa ya da kısa süreli ayı yapısı",
        "enabled_default": True,
        "params": {
            "macd_mum_esik": {
                "label": "Ayı Mum Toleransı",
                "type": "int",
                "default": 5,
                "min": 1,
                "max": 10,
                "step": 1
            }
        }
    },

    # İleride aktif etmek istersen hazır dursun:
    "rsi": {
        "label": "🌀 RSI",
        "help": "RSI aşırı satım kontrolü",
        "enabled_default": False,
        "params": {
            "rsi_window": {
                "label": "RSI Periyodu",
                "type": "int",
                "default": 14,
                "min": 2,
                "max": 50,
                "step": 1
            },
            "rsi_esik": {
                "label": "RSI Eşiği",
                "type": "int",
                "default": 30,
                "min": 5,
                "max": 50,
                "step": 1
            }
        }
    },
    "bollinger": {
        "label": "🌐 Bollinger Bands",
        "help": "Fiyat alt bandın altında/çevresinde mi?",
        "enabled_default": False,
        "params": {
            "bb_window": {
                "label": "BB Periyodu",
                "type": "int",
                "default": 20,
                "min": 5,
                "max": 100,
                "step": 1
            },
            "bb_std": {
                "label": "BB Std",
                "type": "float",
                "default": 2.0,
                "min": 1.0,
                "max": 4.0,
                "step": 0.5
            }
        }
    }
}
