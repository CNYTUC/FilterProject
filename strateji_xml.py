"""
Basit XML strateji kayıt sistemi.
Not: Streamlit Cloud ortamında dosya kalıcılığı garanti değildir.
İlk aşama için yeterlidir.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

XML_DOSYA = "stratejiler.xml"


def _guzel_yaz(root: ET.Element) -> str:
    ham = ET.tostring(root, encoding="unicode")
    duzenli = minidom.parseString(ham).toprettyxml(indent="  ")
    satirlar = [s for s in duzenli.splitlines() if s.strip()]
    return "\n".join(satirlar)


def _kaydet(root: ET.Element) -> None:
    icerik = _guzel_yaz(root)
    with open(XML_DOSYA, "w", encoding="utf-8") as dosya:
        dosya.write(icerik)


def xml_oku() -> ET.Element:
    if not os.path.exists(XML_DOSYA):
        root = ET.Element("Kosullar")
        _kaydet(root)
        return root

    try:
        tree = ET.parse(XML_DOSYA)
        return tree.getroot()
    except ET.ParseError:
        root = ET.Element("Kosullar")
        _kaydet(root)
        return root


def strateji_listesi() -> list[str]:
    root = xml_oku()
    return [kosul.get("Adi", "") for kosul in root.findall("Kosul")]


def strateji_yukle(ad: str) -> dict | None:
    root = xml_oku()
    for kosul in root.findall("Kosul"):
        if kosul.get("Adi") == ad:
            veri = {}
            for alt in kosul:
                try:
                    veri[alt.tag] = int(alt.text or "0")
                except ValueError:
                    veri[alt.tag] = 0
            return veri
    return None


def strateji_ekle(ad: str, ayarlar: dict) -> tuple[bool, str]:
    if not ad.strip():
        return False, "Strateji adı boş olamaz."

    root = xml_oku()
    mevcutlar = [k.get("Adi") for k in root.findall("Kosul")]
    if ad in mevcutlar:
        return False, "Bu isimde strateji zaten var."

    yeni = ET.SubElement(root, "Kosul")
    yeni.set("Adi", ad)
    for anahtar, deger in ayarlar.items():
        alt = ET.SubElement(yeni, anahtar)
        alt.text = str(deger)

    _kaydet(root)
    return True, f"'{ad}' stratejisi eklendi."


def strateji_guncelle(ad: str, ayarlar: dict) -> tuple[bool, str]:
    root = xml_oku()
    for kosul in root.findall("Kosul"):
        if kosul.get("Adi") == ad:
            for alt in list(kosul):
                kosul.remove(alt)
            for anahtar, deger in ayarlar.items():
                alt = ET.SubElement(kosul, anahtar)
                alt.text = str(deger)
            _kaydet(root)
            return True, f"'{ad}' stratejisi güncellendi."
    return False, "Güncellenecek strateji bulunamadı."


def strateji_sil(ad: str) -> tuple[bool, str]:
    root = xml_oku()
    for kosul in root.findall("Kosul"):
        if kosul.get("Adi") == ad:
            root.remove(kosul)
            _kaydet(root)
            return True, f"'{ad}' stratejisi silindi."
    return False, "Silinecek strateji bulunamadı."


def xml_icerik_goster() -> str:
    if not os.path.exists(XML_DOSYA):
        return "(Henüz kayıtlı strateji yok)"
    with open(XML_DOSYA, "r", encoding="utf-8") as dosya:
        return dosya.read()
