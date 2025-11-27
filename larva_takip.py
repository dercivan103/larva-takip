import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- AYARLAR ---
st.set_page_config(page_title="Larva AR-GE Sistemi", layout="wide")

# --- SABİTLER ---
TANK_ICON = "https://cdn-icons-png.flaticon.com/512/427/427112.png"
BALIK_ICON_GENEL = "https://cdn-icons-png.flaticon.com/512/3063/3063822.png"

# --- GOOGLE SHEETS BAĞLANTISI ---
# Yerel Excel yerine artık internetteki tabloyu kullanıyoruz
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_getir():
    """Google Sheets'ten verileri okur."""
    try:
        # Verileri önbelleğe almadan (ttl=0) taze okuyalım
        df = conn.read(worksheet="Sayfa1", ttl=0)
        return df
    except Exception as e:
        st.error(f"Veri okunurken hata: {e}")
        return pd.DataFrame(columns=["Tarih", "Tank ID", "Tür", "Sıcaklık", "pH", "Tuzluluk", "Oksijen", "Işık", "Yemleme", "Gözlemler"])

def veriyi_kaydet(yeni_df):
    """Veriyi Google Sheets'e yazar."""
    try:
        conn.update(worksheet="Sayfa1", data=yeni_df)
        st.cache_data.clear() # Önbelleği temizle ki yeni veriyi görelim
        return True
    except Exception as e:
        st.error(f"Kayıt hatası: {e}")
        return False

# --- BELLEK YÖNETİMİ ---
if 'secilen_tank' not in st.session_state:
    st.session_state.secilen_tank = None

if 'aktif_unite_hafizasi' not in st.session_state:
    st.session_state.aktif_unite_hafizasi = "Üretim 1 (16 Tank)"

# --- ARAYÜZ BAŞLANGICI ---
st.sidebar.title("🐟 Larva Tesisi (Cloud)")
unite_secimi = st.sidebar.radio("Ünite Seçiniz:", ["Üretim 1 (16 Tank)", "Üretim 2 (8 Tank)"])

# Ünite değişirse seçimi sıfırla
if unite_secimi != st.session_state.aktif_unite_hafizasi:
    st.session_state.secilen_tank = None
    st.session_state.aktif_unite_hafizasi = unite_secimi
    st.rerun()

tank_sayisi = 16 if "Üretim 1" in unite_secimi else 8
tank_prefix = "U1" if "Üretim 1" in unite_secimi else "U2"

# --- VERİLERİ ÇEK ---
df_tum_veri = verileri_getir()

# --- SAYFA MANTIĞI ---

# 1. GENEL GÖRÜNÜM
if st.session_state.secilen_tank is None:
    st.title(f"{unite_secimi} - Genel Durum")
    cols = st.columns(4)
    for i in range(1, tank_sayisi + 1):
        tank_adi = f"{tank_prefix}-Tank {i}"
        col = cols[(i-1) % 4]
        with col:
            # Tank butonuna basınca
            if st.button(f"🔵 {tank_adi}", use_container_width=True):
                st.session_state.secilen_tank = tank_adi
                st.rerun()

# 2. DETAY EKRANI
else:
    mevcut_tank = st.session_state.secilen_tank
    bugun_str = datetime.now().strftime("%d-%m-%Y")

    # Navigasyon
    col_nav1, col_nav2 = st.columns([1, 4])
    with col_nav1:
        if st.button("⬅️ Geri Dön"):
            st.session_state.secilen_tank = None
            st.rerun()
    
    st.markdown(f"## 📊 {mevcut_tank} - Veri Girişi")
    st.info(f"📅 Tarih: {bugun_str}")

    # FORM ALANLARI
    with st.form("veri_formu"):
        st.subheader("💧 Su Parametreleri")
        c1, c2, c3, c4, c5 = st.columns(5)
        sicaklik = c1.number_input("Sıcaklık (°C)", value=17.0, step=0.1)
        ph = c2.number_input("pH", value=8.0, step=0.1)
        tuzluluk = c3.number_input("Tuzluluk", value=25.0, step=0.5)
        oksijen = c4.number_input("Oksijen", value=8.0, step=0.1)
        isik = c5.number_input("Işık (Lux)", value=500, step=50)
        
        c_sol, c_orta, c_sag = st.columns([1,1,1])
        with c_sol:
            yem_notu = st.text_area("Yemleme Notu", placeholder="Örn: 10 ppm Rotifer")
        with c_orta:
            tur = st.selectbox("Tür", ["Çipura", "Levrek"])
            st.image(TANK_ICON, width=50)
        with c_sag:
            gozlem = st.text_area("Gözlemler", placeholder="Mortalite vb.")
            
        kaydet_btn = st.form_submit_button("💾 VERİYİ BULUTA KAYDET", type="primary")

    if kaydet_btn:
        # Yeni veriyi hazırla
        yeni_satir = pd.DataFrame([{
            "Tarih": bugun_str,
            "Tank ID": mevcut_tank,
            "Tür": tur,
            "Sıcaklık": sicaklik,
            "pH": ph,
            "Tuzluluk": tuzluluk,
            "Oksijen": oksijen,
            "Işık": isik,
            "Yemleme": yem_notu,
            "Gözlemler": gozlem
        }])
        
        # Mevcut veriye ekle
        guncel_df = pd.concat([df_tum_veri, yeni_satir], ignore_index=True)
        
        # Google Sheets'e gönder
        if veriyi_kaydet(guncel_df):
            st.success("Veri Google Sheets'e başarıyla işlendi!")
            st.rerun()

    # GEÇMİŞİ GÖSTER
    st.markdown("---")
    st.markdown("### 📋 Bu Tankın Geçmişi (Google Sheets)")
    
    # Sadece bu tanka ait verileri filtrele
    if not df_tum_veri.empty:
        tank_gecmisi = df_tum_veri[df_tum_veri["Tank ID"] == mevcut_tank]
        if not tank_gecmisi.empty:
            st.dataframe(tank_gecmisi, use_container_width=True)
        else:
            st.info("Bu tank için henüz kayıt yok.")