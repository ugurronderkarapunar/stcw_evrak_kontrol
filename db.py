"""Veritabanı katmanı (Neon PostgreSQL). Sadece SQL burada durur."""
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text


@st.cache_resource
def get_engine():
    # Neon boştayken uyur; pool_pre_ping kopan bağlantıyı otomatik yeniler.
    return create_engine(
        st.secrets["DATABASE_URL"], pool_pre_ping=True, pool_recycle=300
    )


def init_db():
    with get_engine().begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT,
                content BYTEA,
                text_content TEXT,
                uploaded_at TIMESTAMPTZ DEFAULT NOW()
            )"""))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS document_dates (
                id SERIAL PRIMARY KEY,
                document_id INT REFERENCES documents(id) ON DELETE CASCADE,
                date_value DATE NOT NULL,
                context TEXT
            )"""))


def add_document(filename, file_type, content, text_content, dates):
    """Belgeyi ve bulunan tarihleri kaydeder. dates = [(date, context), ...]"""
    with get_engine().begin() as conn:
        doc_id = conn.execute(
            text("""INSERT INTO documents (filename, file_type, content, text_content)
                    VALUES (:f, :t, :c, :x) RETURNING id"""),
            {"f": filename, "t": file_type, "c": content, "x": text_content},
        ).scalar()
        for d, ctx in dates:
            conn.execute(
                text("""INSERT INTO document_dates (document_id, date_value, context)
                        VALUES (:i, :d, :c)"""),
                {"i": doc_id, "d": d, "c": ctx},
            )
    return doc_id


def list_documents() -> pd.DataFrame:
    return pd.read_sql(
        text("""SELECT d.id, d.filename, d.file_type, d.uploaded_at,
                       COUNT(dd.id) AS tarih_sayisi
                FROM documents d LEFT JOIN document_dates dd ON dd.document_id = d.id
                GROUP BY d.id ORDER BY d.uploaded_at DESC"""),
        get_engine(),
    )


def list_dates() -> pd.DataFrame:
    return pd.read_sql(
        text("""SELECT dd.date_value AS tarih, d.filename AS belge,
                       dd.context AS baglam, d.id AS belge_id
                FROM document_dates dd JOIN documents d ON d.id = dd.document_id
                ORDER BY dd.date_value"""),
        get_engine(),
    )


def get_file(doc_id):
    with get_engine().connect() as conn:
        return conn.execute(
            text("SELECT filename, content FROM documents WHERE id = :i"),
            {"i": doc_id},
        ).first()


def search_text(query) -> pd.DataFrame:
    return pd.read_sql(
        text("""SELECT id, filename, uploaded_at FROM documents
                WHERE text_content ILIKE :q ORDER BY uploaded_at DESC"""),
        get_engine(),
        params={"q": f"%{query}%"},
    )


def delete_document(doc_id):
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM documents WHERE id = :i"), {"i": doc_id})
