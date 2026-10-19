# Belge Tarayıcı

Streamlit + Neon (PostgreSQL) + GitHub. Belgeler taranır, içindeki tarihler Neon'a kaydedilir.

## Dosya yapısı
- `app.py` – arayüz
- `db.py` – tüm SQL işlemleri
- `extractor.py` – metin çıkarma + tarih bulma
- `packages.txt` – OCR için sistem paketleri (Streamlit Cloud)

## Kurulum
1. neon.tech'te proje aç, **connection string**'i kopyala.
2. Başına `postgresql+psycopg2://` olacak şekilde düzelt.
3. Yerelde: `.streamlit/secrets.toml.example` dosyasını `secrets.toml` yap, `DATABASE_URL`'i yaz.
   `pip install -r requirements.txt` ve `streamlit run app.py`
4. GitHub'a yükle (secrets.toml gitmez).
5. share.streamlit.io > New app > repo'nu seç > Advanced settings > Secrets'a `DATABASE_URL = "..."` yapıştır.

## Notlar
- Dosyalar veritabanında saklanır (Neon ücretsiz 0.5 GB). Çok büyük dosyalar için sonra S3/R2'ye geçilebilir.
- Taranmış (resim) PDF'lerde metin çıkmaz; resim olarak yüklersen OCR çalışır.
