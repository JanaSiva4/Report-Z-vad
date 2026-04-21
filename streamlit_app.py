import streamlit as st
import requests
import time
import base64
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Maintenance Helpdesk CZLC4",
    page_icon="🛠️",
    layout="wide"
)

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwY2WxHmmw27DwsB3L24ElvxYB9cQWBnervUhwOsGfoWA56E8Diw17PhATdIOMODgYIOw/exec"
WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook/54ef8aa9-e750-4e22-9dad-3b4969e05053"

DEPARTMENTS = [
    "předák balení F1", "předák balení F2", "předák AS",
    "předák nakládka F1", "předák nakládka F2", "předák doplňování F2",
    "předák SPO", "předák BPO", "VS příjem", "VS potvrzování",
    "VS balení", "VS pick AS", "VS nakládka", "Specialista AS",
    "Specialista IT", "Vedení LC", "➕ Jiné / Other"
]

TECHNOLOGIES = [
    "AS", "TMT", "Innotech", "Knapp", "SSI", "ElVy", "Robopal",
    "Ropaso", "Intralox", "Ranpak closer", "Lantech erector", "Gaty",
    "Budova", "➕ Jiné / Other"
]

st.markdown("""
<style>
    .stApp { background-color: #f1f5f9 !important; }
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        border: 1px solid #e2e8f0 !important;
    }
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .block-container { padding-top: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "form"

col_nav1, col_nav2, col_nav3 = st.columns([1.2, 1.8, 7])
with col_nav1:
    if st.button("🛠️ Formulář", use_container_width=True):
        st.session_state.page = "form"
with col_nav2:
    if st.button("📊 Power BI Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"

st.markdown("---")

# ==================== FORMULÁŘ ====================
if st.session_state.page == "form":
    st.title("🛠️ Technical Fault Report")
    st.markdown("Please fill in the technical details of the issue. The information will be immediately sent for resolution.")

    with st.form("service_desk", clear_on_submit=True):
        reported_by = st.text_input("👤 Reported by *")
        col1, col2 = st.columns(2)
        with col1:
            department_select = st.selectbox("📍 1. Department *", options=[""] + DEPARTMENTS, index=0)
            if department_select == "➕ Jiné / Other":
                department_custom = st.text_input("Enter department / Zadejte oddělení")
            else:
                department_custom = ""
        with col2:
            technology_select = st.selectbox("⚙️ 2. Technology *", options=[""] + TECHNOLOGIES, index=0)
            if technology_select == "➕ Jiné / Other":
                technology_custom = st.text_input("Enter technology / Zadejte technologii")
            else:
                technology_custom = ""
        col3, col4 = st.columns(2)
        with col3:
            location = st.text_input("🏢 3. Location *")
        with col4:
            priority = st.selectbox("⚡ 4. Priority", ["Low", "Medium", "High"], index=1)
        description = st.text_area("📝 Detailed fault description *", height=200, placeholder="Describe the technical issue...")
        note = st.text_area("💡 Additional note (optional)", height=80)
        attachment = st.file_uploader("📎 Attachment (optional)", type=["jpg", "jpeg", "png", "pdf"])
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("SUBMIT REPORT", use_container_width=True)

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
                    "reported_by": reported_by, "department": department,
                    "technology": technology, "location": location,
                    "priority": priority, "description": description,
                    "note": note, "attachment": None, "attachment_name": None
                }
                if attachment is not None:
                    file_bytes = attachment.read()
                    payload["attachment"] = base64.b64encode(file_bytes).decode("utf-8")
                    payload["attachment_name"] = attachment.name
                try:
                    r = requests.post(WEBHOOK_URL, json=payload, timeout=30)
                    if r.status_code == 200:
                        progress_bar = st.progress(0)
                        for p in range(100):
                            time.sleep(0.005)
                            progress_bar.progress(p + 1)
                        st.success("✅ Report submitted successfully.")
                        st.info("The record has been created and sent to the Teams channel.")
                    else:
                        st.error("❌ Connection error. Please check your connection to the Alza network (VPN).")
                except:
                    st.error("❌ Connection error. Please check your connection to the Alza network (VPN).")

# ==================== DASHBOARD ====================
elif st.session_state.page == "dashboard":
    st.title("📊 Power BI Dashboard — CZLC4")

    @st.cache_data(ttl=300)
    def load_data():
        try:
            r = requests.get(APPS_SCRIPT_URL, timeout=30)
            raw = r.json().get("data", [])
            df = pd.DataFrame(raw)
            if df.empty:
                return df
            for col in ["Čas nahlášení", "Čas reakce", "Čas vyřešení"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                    df[col] = df[col].dt.tz_convert("Europe/Prague")
            df["datum"] = df["Čas nahlášení"].dt.date
            df["vyreseno"] = df["Čas vyřešení"].notna() & (df["Čas vyřešení"] != "")
            df["doba_reakce_min"] = (df["Čas reakce"] - df["Čas nahlášení"]).dt.total_seconds() / 60
            df["doba_opravy_min"] = (df["Čas vyřešení"] - df["Čas nahlášení"]).dt.total_seconds() / 60
            df["doba_reakce_min"] = df["doba_reakce_min"].clip(lower=0)
            df["doba_opravy_min"] = df["doba_opravy_min"].clip(lower=0)
            return df
        except Exception as e:
            st.error(f"Chyba při načítání dat: {e}")
            return pd.DataFrame()

    with st.spinner("Načítám data..."):
        df = load_data()

    if df.empty:
        st.warning("Žádná data k zobrazení.")
        st.stop()

    # FILTRY
    with st.expander("🔍 Filtry", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            tech_options = ["Vše"] + sorted(df["Technologie"].dropna().unique().tolist())
            tech_filter = st.selectbox("Technologie", tech_options)
        with col_f2:
            priority_options = ["Vše", "High", "Medium", "Low"]
            priority_filter = st.selectbox("Priorita", priority_options)
        with col_f3:
            days_filter = st.selectbox("Období", ["Posledních 7 dní", "Posledních 30 dní", "Vše"], index=2)

    dff = df.copy()
    if tech_filter != "Vše":
        dff = dff[dff["Technologie"] == tech_filter]
    if priority_filter != "Vše":
        dff = dff[dff["Priorita"] == priority_filter]
    if days_filter == "Posledních 7 dní":
        cutoff = pd.Timestamp.now(tz="Europe/Prague") - timedelta(days=7)
        dff = dff[dff["Čas nahlášení"] >= cutoff]
    elif days_filter == "Posledních 30 dní":
        cutoff = pd.Timestamp.now(tz="Europe/Prague") - timedelta(days=30)
        dff = dff[dff["Čas nahlášení"] >= cutoff]

    # METRIKY
    total = len(dff)
    vyreseno = dff["vyreseno"].sum()
    nevyreseno = total - vyreseno
    avg_reakce = dff["doba_reakce_min"].dropna().mean()
    avg_oprava = dff["doba_opravy_min"].dropna().mean()
    pct = round(vyreseno / total * 100, 1) if total > 0 else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📋 Celkem závad", total)
    m2.metric("✅ Vyřešeno", int(vyreseno), f"{pct} %")
    m3.metric("⚠️ Nevyřešeno", int(nevyreseno))
    m4.metric("⏱️ Prům. reakce", f"{round(avg_reakce, 1)} min" if not pd.isna(avg_reakce) else "—")
    m5.metric("🔧 Prům. oprava", f"{round(avg_oprava, 1)} min" if not pd.isna(avg_oprava) else "—")

    st.markdown("---")

    # GRAFY
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📈 Závady za den")
        daily = dff.groupby("datum").size().reset_index(name="počet")
        daily["datum"] = pd.to_datetime(daily["datum"])
        daily = daily.sort_values("datum")
        st.line_chart(daily.set_index("datum")["počet"], use_container_width=True)

    with col_g2:
        st.subheader("⚙️ Top technologie")
        tech_counts = dff["Technologie"].value_counts().head(8).reset_index()
        tech_counts.columns = ["Technologie", "Počet"]
        st.bar_chart(tech_counts.set_index("Technologie"), use_container_width=True)

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("⚡ Závady podle priority")
        priority_counts = dff["Priorita"].value_counts().reset_index()
        priority_counts.columns = ["Priorita", "Počet"]
        st.bar_chart(priority_counts.set_index("Priorita"), use_container_width=True)

    with col_g4:
        st.subheader("📍 Závady podle oddělení")
        dept_counts = dff["Oddělení"].value_counts().head(8).reset_index()
        dept_counts.columns = ["Oddělení", "Počet"]
        st.bar_chart(dept_counts.set_index("Oddělení"), use_container_width=True)

    st.markdown("---")

    # TABULKA NEVYŘEŠENÝCH
    st.subheader("⚠️ Nevyřešené závady")
    nevyr = dff[~dff["vyreseno"]][["Čas nahlášení", "Technologie", "Místo", "Priorita", "Popis", "Nahlásil"]].copy()
    nevyr["Čas nahlášení"] = nevyr["Čas nahlášení"].dt.strftime("%d.%m.%Y %H:%M")
    nevyr = nevyr.sort_values("Čas nahlášení", ascending=False)
    st.dataframe(nevyr, use_container_width=True, hide_index=True)

    st.markdown("---")

    # VŠECHNA DATA
    with st.expander("📋 Všechna data"):
        all_data = dff[["Čas nahlášení", "Technologie", "Místo", "Priorita", "Popis", "Nahlásil", "Čas reakce", "Čas vyřešení", "Popis řešení"]].copy()
        for col in ["Čas nahlášení", "Čas reakce", "Čas vyřešení"]:
            all_data[col] = all_data[col].dt.strftime("%d.%m.%Y %H:%M").fillna("—")
        st.dataframe(all_data, use_container_width=True, hide_index=True)

    if st.button("🔄 Obnovit data"):
        st.cache_data.clear()
        st.rerun()
