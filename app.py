import uuid
from datetime import date, datetime
from urllib.parse import urlparse
import streamlit as st
from supabase import create_client, Client

# -----------------------------------------------------------------------------
# SAYFA VE MOBİL TASARIM AYARLARI (MOBILE-FIRST)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Market SKT Takip",
    page_icon="⛽",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Telefondan rahat kullanım için özel CSS (Tam genişlikte butonlar ve mobil kart görünümü)
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 520px;
        }
        div.stButton > button {
            width: 100%;
            min-height: 3rem;
            font-weight: 600;
            border-radius: 10px;
        }
        .uyari-kirmizi {
            background-color: #ffe5e5;
            color: #b30000;
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: 700;
            margin-bottom: 10px;
            border: 1px solid #ffb3b3;
        }
        .uyari-sari {
            background-color: #fff8e1;
            color: #8c6d00;
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: 700;
            margin-bottom: 10px;
            border: 1px solid #ffe082;
        }
        .uyari-yesil {
            background-color: #e8f5e9;
            color: #1b5e20;
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: 700;
            margin-bottom: 10px;
            border: 1px solid #a5d6a7;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# SUPABASE BAĞLANTISI
# -----------------------------------------------------------------------------
BUCKET_NAME = "market_images"
TABLE_NAME = "urunler"

supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# -----------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# -----------------------------------------------------------------------------
def skt_uyari_olustur(skt_str: str) -> str:
    """SKT'ye kalan gün sayısını hesaplar ve renkli uyarı HTML'i döndürür."""
    skt_tarihi = datetime.strptime(skt_str, "%Y-%m-%d").date()
    kalan_gun = (skt_tarihi - date.today()).days

    if kalan_gun < 0:
        return f'<div class="uyari-kirmizi">🔴 Acil • SKT {abs(kalan_gun)} gün geçti!</div>'
    elif kalan_gun < 30:
        return f'<div class="uyari-kirmizi">🔴 Acil • {kalan_gun} gün kaldı</div>'
    elif kalan_gun <= 60:
        return f'<div class="uyari-sari">🟡 Yaklaşıyor • {kalan_gun} gün kaldı</div>'
    else:
        return f'<div class="uyari-yesil">🟢 Güvenli • {kalan_gun} gün kaldı</div>'


def storage_dosya_adi_bul(resim_url: str) -> str:
    """Public URL içinden Storage'daki dosya adını ayıklar."""
    if not resim_url:
        return ""
    return urlparse(resim_url).path.split("/")[-1]


# -----------------------------------------------------------------------------
# ARAYÜZ & SEKMELER
# -----------------------------------------------------------------------------
st.title("⛽ Market SKT Takip")
st.caption("Mobil Hızlı SKT Kontrol Paneli")

tab_ekle, tab_liste = st.tabs(["📸 Ürün Ekle", "📋 SKT Listesi"])

# =============================================================================
# SEKME 1: ÜRÜN EKLE
# =============================================================================
with tab_ekle:
    st.subheader("Yeni Ürün Ekle")

    cekilen_foto = st.camera_input("Ürün Fotoğrafı Çek")
    urun_adi = st.text_input("Ürün Adı", placeholder="Örn: Kaşarlı Sandviç / Süt 1L")
    skt_tarih = st.date_input("Son Kullanma Tarihi (SKT)", value=date.today())
    kalan_adet = st.number_input("Kalan Adet", min_value=1, max_value=1000, value=1, step=1)

    if st.button("💾 Kaydet", type="primary"):
        if cekilen_foto is None:
            st.warning("⚠️ Lütfen önce kamerayla ürünün fotoğrafını çekin.")
        elif not urun_adi.strip():
            st.warning("⚠️ Lütfen ürün adını girin.")
        else:
            with st.spinner("Fotoğraf yükleniyor ve ürün kaydediliyor..."):
                try:
                    # 1. Benzersiz dosya adı oluştur ve Storage'a yükle
                    dosya_adi = f"{uuid.uuid4().hex}.jpg"
                    foto_bytes = cekilen_foto.getvalue()

                    supabase.storage.from_(BUCKET_NAME).upload(
                        path=dosya_adi,
                        file=foto_bytes,
                        file_options={"content-type": cekilen_foto.type or "image/jpeg"}
                    )

                    # 2. Public URL'i al
                    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(dosya_adi)

                    # 3. Veritabanındaki 'urunler' tablosuna kaydet
                    yeni_urun = {
                        "urun_adi": urun_adi.strip(),
                        "skt": skt_tarih.isoformat(),
                        "kalan_adet": int(kalan_adet),
                        "resim_url": public_url
                    }
                    supabase.table(TABLE_NAME).insert(yeni_urun).execute()

                    st.success(f"✅ '{urun_adi}' başarıyla kaydedildi!")
                except Exception as e:
                    st.error(f"❌ Kayıt sırasında bir hata oluştu: {e}")

# =============================================================================
# SEKME 2: SKT LİSTESİ (MOBİL KART TASARIMI)
# =============================================================================
with tab_liste:
    st.subheader("SKT Sıralı Ürün Listesi")

    if st.button("🔄 Listeyi Yenile"):
        st.rerun()

    try:
        # SKT'ye göre en yakından uzağa (artan) sıralı çek
        yanit = (
            supabase.table(TABLE_NAME)
            .select("*")
            .order("skt", desc=False)
            .execute()
        )
        urunler = yanit.data
    except Exception as e:
        st.error(f"❌ Ürünler yüklenemedi: {e}")
        urunler = []

    if not urunler:
        st.info("Henüz kayıtlı ürün bulunmuyor. '📸 Ürün Ekle' sekmesinden ürün ekleyebilirsiniz.")
    else:
        for urun in urunler:
            urun_id = urun.get("id")
            ad = urun.get("urun_adi", "İsimsiz Ürün")
            skt_str = urun.get("skt")
            adet = urun.get("kalan_adet", 0)
            resim_url = urun.get("resim_url", "")

            uyari_html = skt_uyari_olustur(skt_str)
            formatli_skt = datetime.strptime(skt_str, "%Y-%m-%d").strftime("%d.%m.%Y")

            # Her ürün için dikey mobil kart (st.container)
            with st.container(border=True):
                # Renkli SKT Uyarısı (🔴 Acil / 🟡 Yaklaşıyor / 🟢 Güvenli)
                st.markdown(uyari_html, unsafe_allow_html=True)

                # Ürün Resmi
                if resim_url:
                    st.image(resim_url, use_container_width=True)

                # Ürün Bilgileri
                st.markdown(f"### {ad}")
                st.markdown(f"📅 **SKT:** `{formatli_skt}`")
                st.markdown(f"📦 **Kalan Adet:** `{adet}`")

                st.divider()

                # Hem tablodan hem storage'dan silen buton
                if st.button("🗑️ Çözüldü / Kaldır", key=f"sil_{urun_id}"):
                    with st.spinner("Ürün ve fotoğrafı siliniyor..."):
                        try:
                            # 1. Storage'dan fotoğrafı sil
                            dosya_adi = storage_dosya_adi_bul(resim_url)
                            if dosya_adi:
                                supabase.storage.from_(BUCKET_NAME).remove([dosya_adi])

                            # 2. 'urunler' tablosundan kaydı sil
                            supabase.table(TABLE_NAME).delete().eq("id", urun_id).execute()

                            st.success(f"✅ '{ad}' başarıyla silindi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Silme işlemi sırasında hata oluştu: {e}")
