import streamlit as st
import requests

# 1. VYNUCENÍ SVĚTLÉHO REŽIMU (Light Mode)
st.set_page_config(
    page_title="Hlášení závad", 
    page_icon="🛠",
    layout="centered"
)

# Trocha CSS pro zesvětlení a úpravu vzhledu
st.markdown("""
    <style>
        /* Vynucení světlého pozadí a tmavého písma */
        .stApp {
            background-color: white;
            color: black;
        }
        /* Úprava barvy nadpisů */
        h1, h2, h3 {
            color: #1E1E1E !important;
        }
        /* Styl pro tlačítko */
        .stButton>button {
            background-color: #0078D4;
            color: white;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

def send_to_n8n(data):
    # Tady si dej svou URL
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook-test/54ef8aa9-e750-42e2-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Chyba spojení: {e}")
        return False

st.header("🛠 Formulář hlášení závady")
st.write("Pro nahlášení nové závady vyplňte prosím následující pole.")

with st.form("hlavni_formular", clear_on_submit=True):
    
    # Textová pole (volné psaní)
    subject = st.text_input("Předmět závady *")
    department = st.text_input("Oddělení")
    technology = st.text_input("Technologie")
    location = st.text_input("Místo / Lokalita")
    
    # Výběr priority
    priority = st.selectbox("Priorita", ["Low", "Medium", "High"], index=1)
    
    # Velká pole
    description = st.text_area("Detailní popis závady *")
    note = st.text_area("Zpráva / Poznámka")
    
    submit = st.form_submit_button("Odeslat hlášení")

    if submit:
        if subject and description:
            payload = {
                "subject": subject,
                "department": department,
                "technology": technology,
                "location": location,
                "priority": priority,
                "description": description,
                "note": note
            }
            
            with st.spinner('Odesílám...'):
                if send_to_n8n(payload):
                    st.success("✅ Odesláno! Data byla zapsána.")
                else:
                    st.error("❌ Nepodařilo se odeslat.")
        else:
            st.warning("⚠️ Vyplňte povinná pole (předmět a popis).")
