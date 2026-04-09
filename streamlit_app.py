import streamlit as st
import requests

# Konfigurace stránky
st.set_page_config(
    page_title="Report závad", 
    page_icon="🛠",
    layout="centered"
)

# DESIGN: Agresivnější CSS, které přebije systémové nastavení
st.markdown("""
    <style>
        /* Vynucení šedého pozadí na celou plochu */
        .stApp {
            background-color: #f4f7f9 !important;
        }
        
        /* Bílá karta pro formulář */
        [data-testid="stForm"] {
            background-color: #ffffff !important;
            border-radius: 12px !important;
            padding: 40px !important;
            border: 1px solid #e1e4e8 !important;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
        }

        /* Zajištění, aby text nebyl bílý na bílém */
        .stMarkdown, p, span, label {
            color: #1a1c23 !important;
        }

        /* Tlačítko */
        .stButton>button {
            background-color: #2563eb !important;
            color: white !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)

def send_to_n8n(data):
    # TVOJE URL Z n8n
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook-test/54ef8aa9-e750-4e22-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

st.title("🛠 Technický report závady")

with st.form("service_desk", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Předmět závady *")
    with col2:
        location = st.text_input("Místo / Lokalita")

    col3, col4 = st.columns(2)
    with col3:
        department = st.text_input("Oddělení")
    with col4:
        technology = st.text_input("Technologie")
    
    priority = st.selectbox("Priorita", ["Low", "Medium", "High"], index=1)
    description = st.text_area("Detailní popis závady *")
    note = st.text_area("Poznámka / Zpráva (volitelné)")
    
    st.markdown("---")
    submit = st.form_submit_button("ODESLAT REPORT")

    if submit:
        if subject and description:
            payload = {
                "subject": subject,
                "location": location,
                "department": department,
                "technology": technology,
                "priority": priority,
                "description": description,
                "note": note
            }
st.markdown("---")
    submit = st.form_submit_button("ODESLAT REPORT")

    if submit:
        # Kontrola, zda jsou vyplněna povinná pole
        if subject and description:
            payload = {
                "subject": subject,
                "location": location,
                "department": department,
                "technology": technology,
                "priority": priority,
                "description": description,
                "note": note
            }

st.markdown("---")
    submit = st.form_submit_button("ODESLAT REPORT")

    if submit:
        # Kontrola, zda jsou vyplněna povinná pole
        if subject and description:
            payload = {
                "subject": subject,
                "location": location,
                "department": department,
                "technology": technology,
                "priority": priority,
                "description": description,
                "note": note
            }

            # Samotné odeslání do n8n
            if send_to_n8n(payload):
                # Efektní progress bar pro techniky
                progress_bar = st.progress(0)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(percent_complete + 1)
                
                st.success("✅ Data byla úspěšně zapsána do systému.")
            else:
                st.error("❌ Chyba odesílání.")
        else:
            # Varování, pokud zapomenou vyplnit základní věci
            st.warning("⚠️ Prosím vyplňte Předmět a Popis závady.")
