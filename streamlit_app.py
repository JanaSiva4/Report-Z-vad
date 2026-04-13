import streamlit as st
import requests
import time

# 1. NASTAVENÍ STRÁNKY
st.set_page_config(
    page_title="Maintenance Helpdesk", 
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
st.title("🛠️ Technical Fault Report")
st.markdown("Please fill in the technical details of the issue. The information will be immediately sent for resolution.")

with st.form("service_desk", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        department = st.text_input("📍 1. Department")
    with col2:
        technology = st.text_input("⚙️ 2. Technology")

    col3, col4 = st.columns(2)
    with col3:
        location = st.text_input("🏢 3. Location")
    with col4:
        priority = st.selectbox("⚡ 4. Priority", ["Low", "Medium", "High"], index=1)
    
    description = st.text_area("📝 Detailed fault description *", height=220, placeholder="Describe the technical issue...")
    note = st.text_area("💡 Additional note (optional)", height=80)
    
    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.form_submit_button("SUBMIT REPORT")

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
                
                st.success("✅ Report submitted successfully.")
                st.info("The record has been created and sent to the Teams channel. A summary report will be generated at 08:00.")
            else:
                st.error("❌ Connection error. Please check your connection to the Alza network (VPN).")
        else:
            st.warning("⚠️ The 'Detailed fault description' field is required.")
