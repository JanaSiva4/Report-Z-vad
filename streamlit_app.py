import streamlit as st
import requests
import time

# ... (CSS část zůstává stejná, tu jsem pro přehlednost vynechal) ...

def send_to_n8n(data):
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook/54ef8aa9-e750-4e22-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

st.title("🛠 Technický report závady")

# Začátek formuláře
with st.form("service_desk", clear_on_submit=True):
    # 1. ŘÁDEK
    col1, col2 = st.columns(2)
    with col1:
        # Změna: 'subject' už není předmět, ale definujeme tu Oddělení
        department = st.text_input("1. Oddělení")
    with col2:
        # Změna: Definujeme Technologii
        technology = st.text_input("2. Technologie")

    # 2. ŘÁDEK
    col3, col4 = st.columns(2)
    with col3:
        # Změna: Definujeme Místo
        location = st.text_input("3. Místo / Lokace")
    with col4:
        # Přidali jsme Prioritu do druhého řádku
        priority = st.selectbox("4. Priorita", ["Low", "Medium", "High"], index=1)
    
    # Zbytek formuláře
    description = st.text_area("Detailní popis závady *")
    note = st.text_area("Poznámka / Zpráva (volitelné)")
    
    st.markdown("---")
    submit = st.form_submit_button("ODESLAT REPORT")

    if submit:
        # Kontrola, zda je vyplněn aspoň popis (Předmět jsme z kontroly vyndali)
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
                for percent_complete in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(percent_complete + 1)
                
                st.success("✅ Data byla úspěšně odeslána.")
            else:
                st.error("❌ Chyba odesílání. Zkontrolujte VPN / n8n status.")
        else:
            st.warning("⚠️ Prosím vyplňte Popis závady.")
