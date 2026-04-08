import streamlit as st
import requests

# Konfigurace stránky
st.set_page_config(
    page_title="Report závad", 
    page_icon="🛠",
    layout="centered"
)

# DESIGN: Vlastní CSS pro moderní technický vzhled
st.markdown("""
    <style>
        /* Celkové pozadí aplikace (soft grey) */
        .stApp {
            background-color: #f4f7f9;
        }
        
        /* Styl bílé karty formuláře */
        [data-testid="stForm"] {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 40px;
            border: 1px solid #e1e4e8;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        }
        
        /* Úprava nadpisu */
        .main-title {
            color: #1a1c23;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 20px;
            text-align: center;
        }

        /* Styl tlačítek */
        .stButton>button {
            width: 100%;
            background-color: #2563eb;
            color: white;
            border-radius: 8px;
            padding: 12px;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #1d4ed8;
            color: white;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        /* Vizuální oddělovač */
        hr {
            margin-top: 25px;
            margin-bottom: 25px;
            border: 0;
            border-top: 1px solid #eee;
        }
    </style>
""", unsafe_allow_html=True)

def send_to_n8n(data):
    # TVOJE URL Z n8n
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook-test/54ef8aa9-e750-42e2-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

# Hlavička aplikace
st.markdown('<div class="main-title">🛠 Technický report závady</div>', unsafe_allow_html=True)
st.write("Vyplňte prosím detaily závady pro servisní tým.")

# Formulář
with st.form("service_desk", clear_on_submit=True):
    
    # První řada: Předmět a Lokalita
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Předmět závady *")
    with col2:
        location = st.text_input("Místo / Lokalita")

    # Druhá řada: Oddělení a Technologie
    col3, col4 = st.columns(2)
    with col3:
        department = st.text_input("Oddělení")
    with col4:
        technology = st.text_input("Technologie")
    
    # Třetí řada: Priorita
    priority = st.selectbox("Priorita", ["Low", "Medium", "High"], index=1)
    
    # Textové oblasti
    description = st.text_area("Detailní popis závady *", help="Popište, co přesně nefunguje.")
    note = st.text_area("Poznámka / Zpráva (volitelné)")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    submit = st.form_submit_button("ODESLAT DO SYSTÉMU")

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
            
            with st.spinner('Odesílám...'):
                if send_to_n8n(payload):
                    st.success("✅ Závada byla úspěšně nahlášena.")
                    st.balloons()
                else:
                    st.error("❌ Došlo k chybě při odesílání. Prověřte n8n.")
        else:
            st.warning("⚠️ Předmět a Popis jsou povinná pole.")
