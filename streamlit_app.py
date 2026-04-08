import streamlit as st
import requests

def send_to_n8n(data):
    # Tady vložíš URL z n8n Webhooku
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook/54ef8aa9-e750-4e22-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data)
        return r.status_code == 200
    except:
        return False

st.header("🛠 Hlášení provozní závady")

with st.form("service_desk"):
    task_name = st.text_input("Stručný název závady")
    room_no = st.text_input("Místnost/Lokalita")
    details = st.text_area("Detailní popis problému")
    
    submit = st.form_submit_button("Odeslat k opravě")

    if submit:
        if task_name and details:
            payload = {
                "subject": task_name,
                "location": room_no,
                "description": details,
                "reporter": "Streamlit App" # Můžeš vytáhnout z login session
            }
            if send_to_n8n(payload):
                st.success("Díky! Závada byla zapsána a v Asaně už na tom pracují.")
            else:
                st.error("Chyba spojení s n8n. Zkus to prosím znovu.")
        else:
            st.warning("Vyplň prosím název a popis.")
