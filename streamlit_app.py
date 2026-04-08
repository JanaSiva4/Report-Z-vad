import streamlit as st
import requests

# Konfigurace stránky
st.set_page_config(page_title="Hlášení závad", page_icon="🛠")

def send_to_n8n(data):
    # Nezapomeň pak vyměnit za Production URL, až budeš mít workflow aktivované!
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook-test/54ef8aa9-e750-42e2-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data)
        return r.status_code == 200
    except:
        return False

st.header("🛠 Detailní hlášení závady")

with st.form("service_desk", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        department = st.selectbox("Oddělení", ["Logistika", "IT", "HR", "Sales", "Provoz", "Jiné"])
        technology = st.selectbox("Technologie", ["Hardware", "Software", "Síť", "Budova/Elektro", "Ostatní"])
    
    with col2:
        priority = st.select_slider("Priorita", options=["Low", "Medium", "High"])
        location = st.text_input("Místnost/Lokalita")

    subject = st.text_input("Stručný název závady (předmět)")
    details = st.text_area("Detailní popis problému")
    note = st.text_area("Poznámka pro technika (nepovinné)")
    
    submit = st.form_submit_button("Odeslat do systému")

    if submit:
        if subject and details:
            payload = {
                "department": department,
                "technology": technology,
                "priority": priority,
                "location": location,
                "subject": subject,
                "description": details,
                "note": note,
                "reporter": "Streamlit App"
            }
            
            with st.spinner('Odesílám...'):
                if send_to_n8n(payload):
                    st.success("✅ Hotovo! Závada byla zapsána a odeslána do Asany.")
                    st.balloons()
                else:
                    st.error("❌ Chyba spojení s n8n.")
        else:
            st.warning("⚠️ Vyplňte prosím alespoň Předmět a Popis.")
