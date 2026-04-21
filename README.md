# 🛠️ Maintenance Helpdesk CZLC4

Systém pro digitální hlášení, sledování a reportování technických závad ve skladu CZLC4.

**Aplikace:** [reportzavad.streamlit.app](https://maintenancedesk.streamlit.app/)

---

## 📋 Co to umí

- **Formulář** — pracovníci hlásí závady přes webový formulář s přílohou
- **Teams notifikace** — automatické odeslání do Teams kanálu
- **Google Sheets** — záznamy všech závad včetně časů reakce a vyřešení
- **SharePoint** — dočasné úložiště příloh (auto-mazání po 24h)
- **AI Reporty** — Gemini generuje předávací reporty pro Asanu každých 12h
- **Power BI Dashboard** — statistiky a grafy v reálném čase (chráněno heslem)

---

## 🏗️ Technický stack

| Část | Technologie |
|------|-------------|
| Frontend | Python + Streamlit |
| Automatizace | n8n (dev.gcp.alza.cz) |
| AI model | Google Gemini 2.5 Flash (Vertex AI) |
| Notifikace | Microsoft Teams |
| Data | Google Sheets + Apps Script |
| Přílohy | SharePoint (24h TTL) |
| Reporty | Asana |
| Hosting | Streamlit Community Cloud |

---

## 🚀 Jak spustit lokálně

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

---

## ⚙️ Konfigurace

### Streamlit Secrets
Vytvoř soubor `.streamlit/secrets.toml`:

```toml
DASHBOARD_PASSWORD = "tvoje_heslo"
```

### Proměnné v kódu
V `streamlit_app.py` uprav:
```python
APPS_SCRIPT_URL = "..."   # URL Apps Script webhooku pro čtení Sheets
WEBHOOK_URL = "..."        # URL n8n webhooku pro příjem formulářů
```

---

## 📁 Struktura projektu

```
├── streamlit_app.py      # Hlavní aplikace (formulář + dashboard)
├── requirements.txt      # Python závislosti
└── README.md             # Dokumentace
```

---

## 📦 Závislosti

```
streamlit
requests
pandas
plotly
```

---

## 🔄 n8n Workflows

### WF1 — Příjem závady
```
Webhook → Teams notifikace → SharePoint (příloha) → Google Sheets
```

### WF2 — Sledování a Reporty
```
Teams Trigger → Čas reakce / Čas vyřešení + Popis řešení → Sheets
Schedule 6:00 → Noční report → Asana (Gemini AI)
Schedule 18:00 → Denní report + AI doporučení → Asana
Schedule 6:05 → Mazání příloh SharePoint
```

---

## 📊 Google Sheets — struktura

| Sloupec | Popis |
|---------|-------|
| Oddělení | Oddělení nahlašovatele |
| Technologie | Typ technologie |
| Místo | Lokace závady |
| Priorita | Low / Medium / High |
| Popis | Detailní popis závady |
| ID Teams | ID vlákna v Teams |
| Čas nahlášení | Timestamp hlášení (Praha) |
| Čas reakce | První reakce technika |
| Čas vyřešení | Čas vyřešení |
| Popis řešení | Co technik napsal |
| Příloha | URL fotky na SharePointu |

---

## 🔒 Přístup

- **Formulář** — veřejný, kdokoli s odkazem
- **Dashboard** — chráněn heslem (nastavit v Streamlit Secrets)

---

*Jana Sivačenko | CZLC4 | Duben 2026*
