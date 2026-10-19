"""Arayüz. İş mantığı extractor.py ve db.py'de."""
from datetime import date

import streamlit as st

import db
import extractor

st.set_page_config(page_title="Belge Tarayıcı", page_icon="📄", layout="wide")
db.init_db()

st.title("📄 Belge Tarayıcı")

# ---------- Yükleme ----------
with st.sidebar:
    st.header("Belge yükle")
    files = st.file_uploader(
        "PDF, resim, Word veya TXT",
        type=["pdf", "png", "jpg", "jpeg", "docx", "txt"],
        accept_multiple_files=True,
    )
    if files and st.button("Tara ve kaydet", type="primary"):
        for f in files:
            data = f.getvalue()
            with st.spinner(f"{f.name} taranıyor..."):
                text = extractor.extract_text(f.name, data)
                dates = extractor.find_dates(text)
                db.add_document(f.name, f.type, data, text, dates)
            st.success(f"{f.name}: {len(dates)} tarih bulundu")
        st.rerun()

tab_dates, tab_docs, tab_search = st.tabs(["📅 Tarihler", "🗂️ Belgeler", "🔎 Ara"])

# ---------- Tarihler ----------
with tab_dates:
    df = db.list_dates()
    if df.empty:
        st.info("Henüz tarih yok. Soldan belge yükle.")
    else:
        df["kalan_gun"] = df["tarih"].apply(lambda d: (d - date.today()).days)
        only_future = st.checkbox("Sadece gelecek tarihler")
        if only_future:
            df = df[df["kalan_gun"] >= 0]
        st.dataframe(df.drop(columns="belge_id"), use_container_width=True, hide_index=True)

# ---------- Belgeler ----------
with tab_docs:
    docs = db.list_documents()
    if docs.empty:
        st.info("Kayıtlı belge yok.")
    for _, row in docs.iterrows():
        c1, c2, c3 = st.columns([5, 1, 1])
        c1.write(f"**{row['filename']}** · {row['tarih_sayisi']} tarih · {row['uploaded_at']:%d.%m.%Y %H:%M}")
        file = db.get_file(int(row["id"]))
        c2.download_button("İndir", file.content.tobytes() if hasattr(file.content, "tobytes") else bytes(file.content),
                           file_name=file.filename, key=f"dl{row['id']}")
        if c3.button("Sil", key=f"del{row['id']}"):
            db.delete_document(int(row["id"]))
            st.rerun()

# ---------- Arama ----------
with tab_search:
    q = st.text_input("Belge içinde ara")
    if q:
        res = db.search_text(q)
        st.dataframe(res, use_container_width=True, hide_index=True) if not res.empty else st.write("Sonuç yok.")
