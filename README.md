# Maintenance Helpdesk CZLC4

Webova aplikace pro hlaseni, sledovani a vyhodnocovani technickych zavad ve skladu CZLC4.

Projekt je pripraveny pro firemni Vibe Coding platformu. Puvodni Streamlit verze byla prevedena na FastAPI backend a staticke webove rozhrani, ktere bezi v kontejneru na portu 8080.

## Co aplikace umi

- Formular pro nahlaseni zavady vcetne oddeleni, technologie, mista, priority a popisu.
- Ulozeni zavady do Firestore v GCP.
- Odeslani dat do n8n pouze pro integrace, ktere aplikace nema delat primo, hlavne Teams a SharePoint.
- Dashboard nad daty z backendu aplikace.
- Prehled nevyresenych zavad a zavad v reseni.
- Prehled vsech dat, grafy, filtry a export.
- Sprava pripominek pres napojeny webhook.

## Nasazeni

Platformni cast je ve slozce `container/`.

Hlavni pozadavky platformy:

- aplikacni kod je uvnitr `container/`
- backend bezi pres FastAPI
- health check je dostupny na `GET /healthz`
- aplikace posloucha na portu 8080
- Dockerfile spousti `uvicorn`
- projektova konfigurace je v `container/config.env`
- strukturovana data zavad jsou ve Firestore
- priloha/Teams/SharePoint integrace probiha pres n8n webhook

## Lokalni spusteni

Z korene projektu lze pouzit soubor `Spustit_aplikaci.bat`.

Manualne:

```powershell
cd container\backend
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Potom otevrit:

```text
http://127.0.0.1:8080
```

Health check:

```text
http://127.0.0.1:8080/healthz
```

## Konfigurace

Konfigurace pro platformu je v `container/config.env`.

Vyplnene hodnoty:

- `GCP_PROJECT_ID`
- `GCS_BUCKET`

Service account se do `config.env` nedava. Platforma ho pouziva pri behu aplikace.

Citlive hodnoty jako webhook URL, podpisove tokeny a hesla se do repozitare neukladaji. Aplikace je umi nacist z prostredi pri behu aplikace.

Runtime hodnoty mimo repozitar:

- `WEBHOOK_URL` - n8n webhook pro Teams/SharePoint notifikaci po vytvoreni zavady
- `WEBHOOK_API_KEY` - sdileny API klic mezi aplikaci a n8n; aplikace ho posila v hlavicce `X-API-Key` a stejny klic vyzaduje u callbacku z n8n
- `DASHBOARD_PASSWORD` - docasne heslo dashboardu, pokud se nepouzije jen IAP/Alza prihlaseni
- `TEAMS_REMINDER_WEBHOOK` - volitelny webhook pro pripominky do Teams

Google Sheets uz nejsou primarni uloziste dat. Pokud se pouziji, tak jen docasne pro migraci nebo porovnani dat.

## n8n integrace

Aplikace vytvori zavadu ve Firestore a potom zavola n8n webhook. Payload obsahuje bezna pole formulare a `ticket_id`.

n8n muze po odeslani Teams zpravy vratit JSON s `teams_id`, ktery si aplikace ulozi k zavade.

Pokud n8n sleduje odpovedi v Teams vlakne, muze poslat callback:

```text
POST /api/integrations/teams-reply
X-API-Key: <WEBHOOK_API_KEY>
```

Body:

```json
{
  "teams_id": "ID puvodni Teams zpravy",
  "message": "text odpovedi z Teams",
  "author": "jmeno autora"
}
```

Backend podle textu doplni prvni reakci, stav `V reseni` nebo `Vyreseno` a popis reseni.

## Napojeni denniho AI reportu

Samostatny n8n workflow pro denni AI report muze misto Google Sheets cist souhrn z aplikace:

```text
GET /api/reports/shift-summary
X-API-Key: <WEBHOOK_API_KEY>
```

Endpoint vraci JSON se souhrnem nocni smeny, denni smeny a hotovym textem v poli `text`. Tento vystup nahrazuje puvodni vetev `Google Sheets - poruchy`.

## Lokalni Google Cloud pristup

Pro lokalni vyvoj se service account nepridava do kodu ani do `config.env`. Pouziva se prihlaseni pres Google Cloud CLI a impersonace service accountu:

```powershell
gcloud auth login
gcloud auth application-default login --impersonate-service-account=sa-gcp-mhczlc4@l-plat-gencode-mhczlc4.iam.gserviceaccount.com
gcloud config set project l-plat-gencode-mhczlc4
```

Na pocitaci musi byt nainstalovany Google Cloud CLI. Zadny JSON klic ani credentials soubor se do repozitare nepridava.

## Struktura

```text
container/
  Dockerfile
  config.env
  backend/
    requirements.txt
    app/
      main.py
      config.py
      auth.py
      routers/
      services/
    static/
      index.html
```

## Dalsi krok

Zmeny se nahraji do Azure DevOps repozitare na novou `feature/` vetev. Po pushnuti se spusti platformni proces pro sestaveni a nasazeni aplikace.
