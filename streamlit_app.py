import streamlit as st
import requests
import time
import base64

# 1. NASTAVENÍ STRÁNKY
st.set_page_config(
    page_title="Maintenance Helpdesk", 
    page_icon="🛠️",
    layout="centered"
)

# 2. DESIGN
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

# Seznamy
DEPARTMENTS = [
    "předák balení F1",
    "předák balení F2",
    "předák AS",
    "předák nakládka F1",
    "předák nakládka F2",
    "předák doplňování F2",
    "předák SPO",
    "předák BPO",
    "VS příjem",
    "VS potvrzování",
    "VS balení",
    "VS pick AS",
    "VS nakládka",
    "Specialista AS",
    "Specialista IT",
    "Vedení LC"
]

TECHNOLOGIES = [
    "AS",
    "TMT",
    "Innotech",
    "Knapp",
    "SSI",
    "ElVy",
    "Robopal",
    "Ropaso",
    "Intralox",
    "Ranpak closer",
    "Lantech erector",
    "Gaty",
    "Budova"
]

def send_to_n8n(data):
    WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook/54ef8aa9-e750-4e22-9dad-3b4969e05053"
    try:
        r = requests.post(WEBHOOK_URL, json=data, timeout=30)
        return r.status_code == 200
    except:
        return False

# 3. OBSAH STRÁNKY
st.title("🛠️ Technical Fault Report")
st.markdown("Please fill in the technical details of the issue. The information will be immediately sent for resolution.")

with st.form("service_desk", clear_on_submit=True):

    reported_by = st.text_input("👤 Reported by *")

    col1, col2 = st.columns(2)
    with col1:
        department_select = st.selectbox(
            "📍 1. Department *",
            options=[""] + DEPARTMENTS,
            index=0
        )
        if department_select == "➕ Jiné / Other":
            department_custom = st.text_input("Enter department / Zadejte oddělení")
        else:
            department_custom = ""

    with col2:
        technology_select = st.selectbox(
            "⚙️ 2. Technology *",
            options=[""] + TECHNOLOGIES,
            index=0
        )
        if technology_select == "➕ Jiné / Other":
            technology_custom = st.text_input("Enter technology / Zadejte technologii")
        else:
            technology_custom = ""

    col3, col4 = st.columns(2)
    with col3:
        location = st.text_input("🏢 3. Location *")
    with col4:
        priority = st.selectbox("⚡ 4. Priority", ["Low", "Medium", "High"], index=1)

    description = st.text_area("📝 Detailed fault description *", height=220, placeholder="Describe the technical issue...")
    note = st.text_area("💡 Additional note (optional)", height=80)
    attachment = st.file_uploader("📎 Attachment (optional)", type=["jpg", "jpeg", "png", "pdf"])

    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.form_submit_button("SUBMIT REPORT")

    if submit:
        department = department_custom if department_select == "➕ Jiné / Other" else department_select
        technology = technology_custom if technology_select == "➕ Jiné / Other" else technology_select

        if not reported_by:
            st.warning("⚠️ Please fill in your name.")
        elif not department:
            st.warning("⚠️ Please select or enter a department.")
        elif not technology:
            st.warning("⚠️ Please select or enter a technology.")
        elif not location:
            st.warning("⚠️ Please fill in the location.")
        elif not description:
            st.warning("⚠️ The 'Detailed fault description' field is required.")
        else:
            payload = {
                "reported_by": reported_by,
                "department": department,
                "technology": technology,
                "location": location,
                "priority": priority,
                "description": description,
                "note": note,
                "attachment": None,
                "attachment_name": None
            }

            if attachment is not None:
                file_bytes = attachment.read()
                file_b64 = base64.b64encode(file_bytes).decode("utf-8")
                payload["attachment"] = file_b64
                payload["attachment_name"] = attachment.name

            if send_to_n8n(payload):
                progress_bar = st.progress(0)
                for p in range(100):
                    time.sleep(0.005)
                    progress_bar.progress(p + 1)
                st.success("✅ Report submitted successfully.")
                st.info("The record has been created and sent to the Teams channel.")
            else:
                st.error("❌ Connection error. Please check your connection to the Alza network (VPN).")
