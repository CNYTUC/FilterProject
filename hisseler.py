# BIST hisse listesi - Yahoo Finance formatı (.IS)
# İstersen bu listeyi zamanla artırabilir veya azaltabilirsin.

BIST_HISSELER = [
    "AKBNK.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS", "DOHOL.IS",
    "EKGYO.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "GUBRF.IS",
    "HALKB.IS", "ISCTR.IS", "KCHOL.IS", "KOZAA.IS", "KOZAL.IS",
    "KRDMD.IS", "LOGO.IS", "MGROS.IS", "ODAS.IS", "OYAKC.IS",
    "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS",
    "SOKM.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS",
    "TOASO.IS", "TTKOM.IS", "TUPRS.IS", "VAKBN.IS", "VESTL.IS",
    "YKBNK.IS",
    "AEFES.IS", "AGHOL.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS",
    "ASUZU.IS", "BAGFS.IS", "BANVT.IS", "BRISA.IS", "CCOLA.IS",
    "CEMTS.IS", "CIMSA.IS", "CLEBI.IS", "DOAS.IS", "EGEEN.IS",
    "ENKAI.IS", "ENJSA.IS", "EUPWR.IS", "FENER.IS", "GLYHO.IS",
    "GOLTS.IS", "GOODY.IS", "HEKTS.IS", "IPEKE.IS", "ISGYO.IS",
    "ISMEN.IS", "KARSN.IS", "KLNMA.IS", "KONTR.IS", "KONYA.IS",
    "KORDS.IS", "MAVI.IS", "MPARK.IS", "NETAS.IS", "NTHOL.IS",
    "OTKAR.IS", "PARSN.IS", "POLHO.IS", "QUAGR.IS", "REEDR.IS",
    "RYSAS.IS", "SELEC.IS", "SMRTG.IS", "TATGD.IS", "TMSN.IS",
    "TRGYO.IS", "TRILC.IS", "TURSG.IS", "ULKER.IS", "VESBE.IS",
    "VKGYO.IS", "ZOREN.IS",
]

# Tekrar edenleri otomatik temizle
BIST_HISSELER = list(dict.fromkeys(BIST_HISSELER))
