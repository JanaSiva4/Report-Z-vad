import streamlit as st
import requests
import time
import base64
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

st.set_page_config(
    page_title="Maintenance Helpdesk CZLC4",
    page_icon="🛠️",
    layout="wide"
)

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwY2WxHmmw27DwsB3L24ElvxYB9cQWBnervUhwOsGfoWA56E8Diw17PhATdIOMODgYIOw/exec"
WEBHOOK_URL = "https://n8n.dev.gcp.alza.cz/webhook/54ef8aa9-e750-4e22-9dad-3b4969e05053"

DEPARTMENTS = [
    "balení F1", "balení F2", "AS",
    "nakládka F1", "nakládka F2", "doplňování F2",
    "SPO", "BPO", "VS příjem", "VS potvrzování",
    "VS balení", "VS pick AS", "VS nakládka", "Specialista AS",
    "Specialista IT", "Vedení LC", "➕ Jiné / Other"
]

TECHNOLOGIES = [
    "AS", "TMT", "Innotech", "Knapp", "SSI", "ElVy", "Robopal",
    "Ropaso", "Intralox", "Ranpak closer", "Lantech erector", "Gaty",
    "Budova", "➕ Jiné / Other"
]

if "page" not in st.session_state:
    st.session_state.page = "form"
if "dashboard_auth" not in st.session_state:
    st.session_state.dashboard_auth = False
if "days_filter" not in st.session_state:
    st.session_state.days_filter = "30"

st.markdown("""
<style>
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    .block-container { padding-top: 5rem !important; padding-bottom: 2rem !important; }
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        padding: 2.5rem !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07) !important;
        max-width: 720px !important;
        margin: 0 auto !important;
    }
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        height: 2.8em !important;
        width: 100% !important;
        font-size: 14px !important;
        border: 1.5px solid #e2e8f0 !important;
        background: white !important;
        color: #475569 !important;
    }
    .stButton>button:hover {
        background: #f1f5f9 !important;
        color: #1e293b !important;
    }
    .metric-box {
        background: white;
        border-radius: 10px;
        padding: 14px 10px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .metric-box-alert {
        background: white;
        border-radius: 10px;
        padding: 14px 10px;
        border: 1.5px solid #dc2626;
        text-align: center;
    }
    .metric-num { font-size: 1.6rem; font-weight: 700; color: #1e293b; }
    .metric-num-green { font-size: 1.6rem; font-weight: 700; color: #16a34a; }
    .metric-num-red { font-size: 1.6rem; font-weight: 700; color: #dc2626; }
    .metric-num-blue { font-size: 1.6rem; font-weight: 700; color: #2563eb; }
    .metric-num-purple { font-size: 1.6rem; font-weight: 700; color: #7c3aed; }
    .metric-lbl { font-size: 0.72rem; color: #64748b; margin-top: 2px; }
    .metric-desc { font-size: 0.65rem; color: #94a3b8; margin-top: 3px; font-style: italic; }
    .chart-desc { font-size: 0.7rem; color: #94a3b8; margin-top: 4px; font-style: italic; }
    .pill-active {
        display: inline-block; padding: 4px 14px; border-radius: 20px;
        background: #2563eb; color: white; font-size: 12px; font-weight: 600;
        border: none; cursor: pointer; margin-right: 4px;
    }
    .pill-inactive {
        display: inline-block; padding: 4px 14px; border-radius: 20px;
        background: #f1f5f9; color: #475569; font-size: 12px; font-weight: 500;
        border: 1px solid #e2e8f0; cursor: pointer; margin-right: 4px;
    }
</style>
""", unsafe_allow_html=True)

# NAVIGACE
_, nav_center, _ = st.columns([1, 2, 1])
with nav_center:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        btn_form = st.button("🛠️ Formulář", use_container_width=True)
    with nav_col2:
        btn_dash = st.button("📊 Power BI Dashboard", use_container_width=True)

if btn_form:
    st.session_state.page = "form"
    st.rerun()
if btn_dash:
    st.session_state.page = "dashboard"
    st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ==================== FORMULÁŘ ====================
if st.session_state.page == "form":
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<h1 style='text-align:center'>🛠️ Technical Fault Report</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748b;margin-bottom:1.5rem'>Please fill in the technical details of the issue. The information will be immediately sent for resolution.</p>", unsafe_allow_html=True)

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
            description = st.text_area("📝 Detailed fault description *", height=220, placeholder="Describe the technical issue...")
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

    if not st.session_state.dashboard_auth:
        _, center, _ = st.columns([1, 1, 1])
        with center:
            st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
            st.markdown("### 🔒 Přístup do dashboardu")
            st.markdown("Dashboard je dostupný pouze oprávněným uživatelům.")
            password = st.text_input("Zadejte heslo", type="password")
            if st.button("Přihlásit se", use_container_width=True):
                correct = st.secrets.get("DASHBOARD_PASSWORD", "czlc4admin")
                if password == correct:
                    st.session_state.dashboard_auth = True
                    st.rerun()
                else:
                    st.error("❌ Nesprávné heslo.")
        st.stop()

    @st.cache_data(ttl=300)
    def load_data():
        try:
            session = requests.Session()
            r = session.get(APPS_SCRIPT_URL, timeout=30, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
            raw = r.json().get("data", [])
            df = pd.DataFrame(raw)
            if df.empty:
                return df
            for col in ["Čas nahlášení", "Čas reakce", "Čas vyřešení"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                    df[col] = df[col].dt.tz_convert("Europe/Prague")
            df["datum"] = df["Čas nahlášení"].dt.date
            df["den_tydne"] = df["Čas nahlášení"].dt.day_name()
            df["vyreseno"] = df["Čas vyřešení"].notna()
            df["doba_reakce_min"] = (df["Čas reakce"] - df["Čas nahlášení"]).dt.total_seconds() / 60
            df["doba_opravy_min"] = (df["Čas vyřešení"] - df["Čas nahlášení"]).dt.total_seconds() / 60
            df["doba_reakce_min"] = df["doba_reakce_min"].clip(lower=0)
            df["doba_opravy_min"] = df["doba_opravy_min"].clip(lower=0)
            df["sla_splneno"] = df["doba_opravy_min"] <= 30
            return df
        except Exception as e:
            st.error(f"Chyba při načítání dat: {e}")
            return pd.DataFrame()

    with st.spinner("Načítám data..."):
        df = load_data()

    if df.empty:
        st.warning("Žádná data k zobrazení.")
        st.stop()

    # HEADER
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    col_header, col_logout = st.columns([8, 1])
    with col_header:
        st.markdown(f"### 📊 Power BI Dashboard — CZLC4")
        st.markdown(f"<div style='font-size:12px;color:#94a3b8;margin-top:-12px'>Aktualizováno {now_str} · data z Google Sheets</div>", unsafe_allow_html=True)
    with col_logout:
        if st.button("🔓 Odhlásit", use_container_width=True):
            st.session_state.dashboard_auth = False
            st.session_state.page = "form"
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # FILTRY — pill přepínače pro období + dropdowny pro technologii a prioritu
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
    with col_f1:
        st.markdown("<div style='font-size:12px;color:#64748b;margin-bottom:4px'>📅 Období</div>", unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            if st.button("7 dní", use_container_width=True):
                st.session_state.days_filter = "7"
                st.rerun()
        with p2:
            if st.button("30 dní", use_container_width=True):
                st.session_state.days_filter = "30"
                st.rerun()
        with p3:
            if st.button("Vše", use_container_width=True):
                st.session_state.days_filter = "all"
                st.rerun()
        with p4:
            active_label = {"7": "7 dní", "30": "30 dní", "all": "Vše"}.get(st.session_state.days_filter, "30 dní")
            st.markdown(f"<div style='padding:6px 0;font-size:12px;color:#2563eb;font-weight:600'>✓ {active_label}</div>", unsafe_allow_html=True)
    with col_f2:
        tech_options = ["Vše"] + sorted(df["Technologie"].dropna().unique().tolist())
        tech_filter = st.selectbox("⚙️ Technologie", tech_options)
    with col_f3:
        priority_filter = st.selectbox("⚡ Priorita", ["Vše", "High", "Medium", "Low"])
    with col_f4:
        if st.button("🔄 Obnovit", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # FILTROVÁNÍ DAT
    dff = df.copy()
    if tech_filter != "Vše":
        dff = dff[dff["Technologie"] == tech_filter]
    if priority_filter != "Vše":
        dff = dff[dff["Priorita"] == priority_filter]

    if st.session_state.days_filter == "7":
        cutoff = pd.Timestamp.now(tz="Europe/Prague") - timedelta(days=7)
        dff = dff[dff["Čas nahlášení"] >= cutoff]
        prev = df[(df["Čas nahlášení"] >= cutoff - timedelta(days=7)) & (df["Čas nahlášení"] < cutoff)]
    elif st.session_state.days_filter == "30":
        cutoff = pd.Timestamp.now(tz="Europe/Prague") - timedelta(days=30)
        dff = dff[dff["Čas nahlášení"] >= cutoff]
        prev = df[(df["Čas nahlášení"] >= cutoff - timedelta(days=30)) & (df["Čas nahlášení"] < cutoff)]
    else:
        prev = pd.DataFrame()

    total = len(dff)
    vyreseno = int(dff["vyreseno"].sum())
    nevyreseno = total - vyreseno
    avg_reakce = dff["doba_reakce_min"].dropna().mean()
    avg_oprava = dff["doba_opravy_min"].dropna().mean()
    pct = round(vyreseno / total * 100, 1) if total > 0 else 0
    sla = round(dff["sla_splneno"].sum() / total * 100, 1) if total > 0 else 0
    trend = len(dff) - len(prev) if not prev.empty else None
    trend_positive = trend and trend > 0

    st.markdown("---")

    # METRIKY
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.markdown(f"""<div class='metric-box'>
        <div class='metric-num'>{total}</div>
        <div class='metric-lbl'>📋 Celkem závad</div>
        <div class='metric-desc'>všechna hlášení</div>
    </div>""", unsafe_allow_html=True)
    m2.markdown(f"""<div class='metric-box'>
        <div class='metric-num-green'>{vyreseno}</div>
        <div class='metric-lbl'>✅ Vyřešeno ({pct} %)</div>
        <div class='metric-desc'>hotovo / vyřešeno</div>
    </div>""", unsafe_allow_html=True)
    m3.markdown(f"""<div class='metric-box'>
        <div class='metric-num-red'>{nevyreseno}</div>
        <div class='metric-lbl'>⚠️ Nevyřešeno</div>
        <div class='metric-desc'>čeká na opravu</div>
    </div>""", unsafe_allow_html=True)
    m4.markdown(f"""<div class='metric-box'>
        <div class='metric-num-blue'>{round(avg_reakce,1) if not pd.isna(avg_reakce) else '—'} min</div>
        <div class='metric-lbl'>⏱️ Prům. reakce</div>
        <div class='metric-desc'>do první odpovědi technika</div>
    </div>""", unsafe_allow_html=True)
    m5.markdown(f"""<div class='metric-box'>
        <div class='metric-num-blue'>{round(avg_oprava,1) if not pd.isna(avg_oprava) else '—'} min</div>
        <div class='metric-lbl'>🔧 Prům. oprava</div>
        <div class='metric-desc'>od nahlášení do vyřešení</div>
    </div>""", unsafe_allow_html=True)
    m6.markdown(f"""<div class='metric-box'>
        <div class='metric-num-purple'>{sla} %</div>
        <div class='metric-lbl'>📊 SLA &lt;30 min</div>
        <div class='metric-desc'>vyřešeno do 30 minut</div>
    </div>""", unsafe_allow_html=True)
    trend_txt = f"+{trend}" if trend and trend > 0 else str(trend) if trend is not None else "—"
    trend_color = "metric-num-red" if trend_positive else "metric-num-green" if trend is not None and trend < 0 else "metric-num"
    box_class = "metric-box-alert" if trend_positive else "metric-box"
    m7.markdown(f"""<div class='{box_class}'>
        <div class='{trend_color}'>{trend_txt}</div>
        <div class='metric-lbl'>📈 vs předchozí</div>
        <div class='metric-desc'>oproti min. období</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # GRAFY řada 1
    col_g1, col_g2, col_g3 = st.columns([2, 1, 1])
    with col_g1:
        st.markdown("**📈 Závady za den**")
        daily = dff.groupby("datum").size().reset_index(name="Závady")
        daily["datum"] = pd.to_datetime(daily["datum"])
        st.line_chart(daily.sort_values("datum").set_index("datum"), use_container_width=True, height=180)
        st.markdown("<div class='chart-desc'>Denní počet nahlášených závad — odhaluje vytížené dny a trendy v čase</div>", unsafe_allow_html=True)
    with col_g2:
        st.markdown("**⚙️ Top technologie**")
        st.bar_chart(dff["Technologie"].value_counts().head(6), use_container_width=True, height=180)
        st.markdown("<div class='chart-desc'>Které technologie selhávají nejčastěji — priorita pro preventivní údržbu</div>", unsafe_allow_html=True)
    with col_g3:
        st.markdown("**📅 Závady dle dne v týdnu**")
        day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        day_names_cz = {"Monday":"Po","Tuesday":"Út","Wednesday":"St",
                       "Thursday":"Čt","Friday":"Pá","Saturday":"So","Sunday":"Ne"}
        weekly = dff.groupby("den_tydne").size().reset_index(name="Počet")
        weekly["den_tydne"] = pd.Categorical(weekly["den_tydne"], categories=day_order, ordered=True)
        weekly = weekly.sort_values("den_tydne")
        weekly["den_cz"] = weekly["den_tydne"].map(day_names_cz)
        max_day = weekly.loc[weekly["Počet"].idxmax(), "den_cz"] if not weekly.empty else "—"
        weekly["barva"] = weekly["den_cz"].apply(lambda x: "#dc2626" if x == max_day else "#2563eb")
        fig_week = px.bar(weekly, x="den_cz", y="Počet", height=180,
                         color="barva", color_discrete_map="identity")
        fig_week.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
                              plot_bgcolor="white", paper_bgcolor="white")
        fig_week.update_xaxes(showgrid=False)
        fig_week.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig_week, use_container_width=True)
        st.markdown(f"<div class='chart-desc'>Který den je nejvytíženější — červený sloupec = nejvíce závad ({max_day})</div>", unsafe_allow_html=True)

    # GRAFY řada 2
    col_g4, col_g5, col_g6 = st.columns(3)
    with col_g4:
        st.markdown("**⚡ Podle priority**")
        pri_counts = dff["Priorita"].value_counts().reset_index()
        pri_counts.columns = ["Priorita", "Počet"]
        color_map = {"High": "#dc2626", "Medium": "#f59e0b", "Low": "#22c55e"}
        fig_pri = px.bar(pri_counts, x="Priorita", y="Počet",
                        color="Priorita", color_discrete_map=color_map, height=180)
        fig_pri.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
                             plot_bgcolor="white", paper_bgcolor="white")
        fig_pri.update_xaxes(showgrid=False)
        fig_pri.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig_pri, use_container_width=True)
        st.markdown("<div class='chart-desc'>Rozložení závad dle naléhavosti — červená = okamžitý zásah, žlutá = brzy, zelená = plánovaně</div>", unsafe_allow_html=True)
    with col_g5:
        st.markdown("**📍 Podle oddělení**")
        st.bar_chart(dff["Oddělení"].value_counts().head(6), use_container_width=True, height=180)
        st.markdown("<div class='chart-desc'>Kde je největší technická zátěž — pomáhá přidělit techniky tam kde je to nejvíc potřeba</div>", unsafe_allow_html=True)
    with col_g6:
        st.markdown("**📍 Nejproblematičtější místa**")
        st.bar_chart(dff["Místo"].value_counts().head(6), use_container_width=True, height=180)
        st.markdown("<div class='chart-desc'>Lokace s opakujícími se poruchami — kandidáti na preventivní prohlídku</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**⚠️ Nevyřešené závady**")
    nevyr = dff[~dff["vyreseno"]][["Čas nahlášení", "Technologie", "Místo", "Priorita", "Popis", "Nahlásil"]].copy()
    nevyr["Čas nahlášení"] = nevyr["Čas nahlášení"].dt.strftime("%d.%m. %H:%M")
    st.dataframe(nevyr.sort_values("Čas nahlášení", ascending=False), use_container_width=True, hide_index=True)

    with st.expander("📋 Všechna data"):
        all_data = dff[["Čas nahlášení", "Technologie", "Místo", "Priorita", "Popis", "Nahlásil", "Čas reakce", "Čas vyřešení", "Popis řešení"]].copy()
        for col in ["Čas nahlášení", "Čas reakce", "Čas vyřešení"]:
            all_data[col] = all_data[col].dt.strftime("%d.%m. %H:%M")
        st.dataframe(all_data, use_container_width=True, hide_index=True)
