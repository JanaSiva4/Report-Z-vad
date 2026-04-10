import streamlit as st
import requests
import time

# 1. NASTAVENÍ STRÁNKY
st.set_page_config(
    page_title="Hlášení technických závad", 
    page_icon="🛠️",
    layout="centered"
)

# 2. DESIGN: CSS (vylepšený vzhled a větší okna)
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to bottom, #f0f4f8, #d9e2ec) !important;
        }
        
        [data-testid="stForm"] {
            background-color: #ffffff !important;
            border-radius: 15px !important;
            padding: 3rem !important;
            border: none !important;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1) !important;
        }

        h1 {
            color: #102a43 !important;
            font-weight: 700 !important;
        }

        /* Styl pro tlačítko */
        .stButton>button {
            background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: white !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            height: 3.5em !important;
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

# 3. OBSAH STRÁNKY
st.title("🛠️ Technický report závady")
st.markdown("Vyplňte prosím údaje o závadě. Kolegové v Teams budou ihned informováni.")

with st.form("service_desk", clear_on_submit=True):
    # První řádek
    col1, col2 = st.columns(2)
    with col1:
        department = st.text_input("📍 1. Oddělení")
    with col2:
        technology = st.text_input("⚙️ 2. Technologie")

    # Druhý řádek
    col3, col4 = st.columns(2)
    with col3:
        location = st.text_input("🏢 3. Místo / Lokace")
    with col4:
        priority = st.selectbox("⚡ 4. Priorita", ["Nízká", "Střední", "Vysoká"], index=1)
    
    # Velké textové pole pro popis
    description = st.text_area("📝 Detailní popis závady *", height=250, placeholder="Co přesně nefunguje?")
    
    # Menší pole pro poznámku
    note = st.text_area("💡 Dodatečná poznámka (volitelné)", height=100)
    
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
                progress_bar = st.progress(0)
                for p in range(100):
                    time.sleep(0.005)
                    progress_bar.progress(p + 1)
                
                st.balloons()
                st.success("Skvělé! Vaše hlášení jsme přijali a kolegové v Teams už o něm vědí.")
                st.info("Souhrnný report všech oprav proběhne automaticky zítra v 08:00.")
            else:
                st.error("Něco se nepovedlo. Zkontrolujte připojení k Alza síti (VPN).")
        else:
            st.warning("Bez popisu závady se nehneme. Prosím, doplňte jej.")
