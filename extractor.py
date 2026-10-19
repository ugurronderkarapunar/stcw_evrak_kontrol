"""Belgeden metin çıkarma ve tarih bulma. Veritabanından bağımsız."""
import io
import re
from datetime import date

AYLAR = {
    "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "haziran": 6,
    "temmuz": 7, "ağustos": 8, "eylül": 9, "ekim": 10, "kasım": 11, "aralık": 12,
}

RE_SAYISAL = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")
RE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
RE_YAZILI = re.compile(
    r"\b(\d{1,2})\s+(" + "|".join(AYLAR) + r")\s+(\d{4})\b", re.IGNORECASE
)


def extract_text(filename: str, data: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if ext in ("png", "jpg", "jpeg"):
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(io.BytesIO(data)), lang="tur+eng")
    if ext == "docx":
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    if ext == "txt":
        return data.decode("utf-8", errors="ignore")
    return ""


def _safe_date(y, m, d):
    try:
        return date(int(y), int(m), int(d))
    except ValueError:
        return None


def find_dates(text: str, context_chars: int = 40):
    """Metindeki tarihleri [(date, çevresindeki metin), ...] olarak döner."""
    found = []

    def add(match, d):
        if d is None:
            return
        s = max(0, match.start() - context_chars)
        e = min(len(text), match.end() + context_chars)
        found.append((d, " ".join(text[s:e].split())))

    for m in RE_SAYISAL.finditer(text):
        add(m, _safe_date(m.group(3), m.group(2), m.group(1)))
    for m in RE_ISO.finditer(text):
        add(m, _safe_date(m.group(1), m.group(2), m.group(3)))
    for m in RE_YAZILI.finditer(text):
        add(m, _safe_date(m.group(3), AYLAR[m.group(2).lower()], m.group(1)))

    # Aynı tarih+bağlam tekrarını temizle
    return list(dict.fromkeys(found))
