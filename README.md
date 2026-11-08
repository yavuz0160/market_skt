# ⛽ İstasyon Market SKT Takip (Mobile-First MVP)

Akaryakıt istasyonu market personeli için telefon kamerasıyla hızlıca ürün fotoğrafı çekip **Son Kullanma Tarihi (SKT)** takibi yapmayı sağlayan mobil uyumlu Streamlit & Supabase uygulaması.

## 📁 Proje Dosyaları
- `app.py`: Mobil kart tasarımlı Streamlit uygulaması (`📸 Ürün Ekle` ve `📋 SKT Listesi` sekmeleri).
- `requirements.txt`: Gerekli Python kütüphaneleri (`streamlit`, `supabase`).
- `.streamlit/secrets.toml`: Supabase bağlantı anahtarları şablonu.
- `.streamlit/config.toml`: Mobil görünüm ve tema ayarları.
- `supabase_setup.sql`: Supabase tablo (`urunler`), bucket (`market_images`) ve RLS izinlerini tek seferde oluşturan SQL betiği.

## 🚀 Kurulum
1. **Supabase:** Supabase SQL Editor'de `supabase_setup.sql` dosyasındaki sorguları çalıştırın.
2. **Secrets:** `.streamlit/secrets.toml` dosyasına kendi `SUPABASE_URL` ve `SUPABASE_KEY` değerlerinizi girin.
3. **Çalıştırma:**
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

