import streamlit as st
import requests
import time

# 1. NASTAVENÍ STRÁNKY
st.set_page_config(
    page_title="Hlášení technických závad", 
    page_icon="🛠️",
    layout="centered"
)

# 2. DESIGN (CSS)
st.markdown("""
    <style>
        .stApp { background-color: #f8fafc !important; }
        [data-testid="stForm"] {
            background-color: #ffffff !important;
            border-radius: 8px !important;
            padding: 3rem !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        }
        .stButton>button {
            background-color: #2563eb !important;
            color: white !important;
            border-radius: 6px !important;
            height: 3em !important;
            width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)

def send_to_n8n(data):
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook/54ef8aa9-e750-4e22-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

st.title("🛠️ Technický report závady")

# Začátek formuláře - vnitřní názvy jsou teď ČESKY (bez diakritiky pro jistotu)
with st.form("service_desk", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        oddeleni = st.text_input("📍 1. Oddělení")
    with col2:
        technologie = st.text_input("⚙️ 2. Technologie")

    col3, col4 = st.columns(2)
    with col3:
        misto = st.text_input("🏢 3. Místo / Lokace")
    with col4:
        priorita = st.selectbox("⚡ 4. Priority", ["Low", "Medium", "High"], index=1)
    
    popis = st.text_area("📝 Detailní popis závady *", height=220)
    poznamka = st.text_area("💡 Dodatečná poznámka (volitelné)", height=80)
    
    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.form_submit_button("ODESLAT HLÁŠENÍ")

    if submit:
        if popis:
            # Tady posíláme data do n8n s českými názvy klíčů
            payload = {
                "oddeleni": oddeleni,
                "technologie": technologie,
                "misto": misto,
                "priorita": priorita,
                "popis": popis,
                "poznamka": poznamka
            }

            if send_to_n8n(payload):
                progress_bar = st.progress(0)
                for p in range(100):
                    time.sleep(0.005)
                    progress_bar.progress(p + 1)
                
                st.success("✅ Hlášení bylo úspěšně odesláno.")
            else:
                st.error("❌ Chyba spojení. Zkontrolujte VPN.")
        else:
            st.warning("⚠️ Vyplňte prosím popis závady.")
