import streamlit as st
import requests
import time

# 1. NASTAVENÍ STRÁNKY
st.set_page_config(
    page_title="Maintenance helpdesk", 
    page_icon="🛠️",
    layout="centered"
)

# 2. DESIGN: Profesionální a čistý
st.markdown("""
    <style>
        .stApp {
            background-color: #f8fafc !important;
        }
        
        [data-testid="stForm"] {
            background-color: #ffffff !important;
            border-radius: 8px !important;
            padding: 3rem !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        }

        h1 {
            color: #1e293b !important;
            font-weight: 700 !important;
        }

        .stButton>button {
            background-color: #2563eb !important;
            color: white !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            height: 3em !important;
            width: 100% !important;
            border: none !important;
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

# 3. OBSAH STRÁNKY
st.title("🛠️ Technický report závady")
st.markdown("Vyplňte prosím technické parametry závady. Informace budou okamžitě odeslány k řešení.")

with st.form("service_desk", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        department = st.text_input("📍 1. Oddělení")
    with col2:
        technology = st.text_input("⚙️ 2. Technologie")

    col3, col4 = st.columns(2)
    with col3:
        location = st.text_input("🏢 3. Místo / Lokace")
    with col4:
        # Priority v angličtině dle požadavku
        priority = st.selectbox("⚡ 4. Priority", ["Low", "Medium", "High"], index=1)
    
    # Velké okno pro popis
    description = st.text_area("📝 Detailní popis závady *", height=220, placeholder="Popište technický problém...")
    note = st.text_area("💡 Dodatečná poznámka (volitelné)", height=80)
    
    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.form_submit_button("ODESLAT HLÁŠENÍ")

    if submit:
        if description:
            payload = {
                "department": department,
                "technology": technology,
                "location": location,
                "priority": priority,
                "description": description,
                "note": note
            }

            if send_to_n8n(payload):
                # Pouze progress bar bez balónků
                progress_bar = st.progress(0)
                for p in range(100):
                    time.sleep(0.005)
                    progress_bar.progress(p + 1)
                
                st.success("✅ Hlášení bylo úspěšně odesláno.")
                st.info("Záznam byl vytvořen a odeslán do kanálu Teams. Souhrnný report proběhne v 08:00.")
            else:
                st.error("❌ Chyba spojení. Zkontrolujte připojení k Alza síti (VPN).")
        else:
            st.warning("⚠️ Pole 'Detailní popis závady' je povinné.")
