# Maintenance Helpdesk CZLC4

Webova aplikace pro hlaseni, sledovani a vyhodnocovani technickych zavad ve skladu CZLC4.

Projekt je pripraveny pro firemni Vibe Coding platformu. Puvodni Streamlit verze byla prevedena na FastAPI backend a staticke webove rozhrani, ktere bezi v kontejneru na portu 8080.

## Co aplikace umi

- Formular pro nahlaseni zavady vcetne oddeleni, technologie, mista, priority a popisu.
- Odeslani zavady do napojene automatizace.
- Dashboard nad daty z Google Sheets.
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
