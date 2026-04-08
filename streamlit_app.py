import streamlit as st
import requests

# Nastavení vzhledu stránky
st.set_page_config(page_title="Hlášení závad", page_icon="🛠")

def send_to_n8n(data):
    # SEM VLOŽ SVOU URL (zatím nechávám tu testovací z tvého screenshotu)
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook-test/54ef8aa9-e750-42e2-9dad-3b4969e05053"
    
    try:
        r = requests.post(WEBHOOK_URL, json=data)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Chyba spojení: {e}")
        return False

st.header("🛠 Formulář hlášení závady")
st.info("Vyplňte údaje o závadě. Pole označená hvězdičkou (*) jsou povinná.")

# Samotný formulář
with st.form("hlavni_formular", clear_on_submit=True):
    
    # Volná textová pole
    subject = st.text_input("Předmět závady *")
    department = st.text_input("Oddělení")
    technology = st.text_input("Technologie")
    location = st.text_input("Místo / Lokalita")
    
    # Výběr priority (jediné fixní pole)
    priority = st.selectbox("Priorita", ["Low", "Medium", "High"])
    
    # Popisy a poznámky
    description = st.text_area("Detailní popis závady *")
    note = st.text_area("Zpráva / Poznámka")
    
    # Tlačítko pro odeslání
    submit = st.form_submit_button("Odeslat hlášení")

    if submit:
        # Validace povinných polí
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
            
            with st.spinner('Odesílám data do systému...'):
                if send_to_n8n(payload):
                    st.success("✅ Závada byla úspěšně nahlášena!")
                    st.balloons()
                else:
                    st.error("❌ Nepodařilo se odeslat. Zkontrolujte připojení nebo n8n.")
        else:
            st.warning("⚠️ Prosím, vyplňte povinná pole: Předmět a Detailní popis.")
