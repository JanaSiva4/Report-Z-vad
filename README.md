# Maintenance Helpdesk CZLC4

Webova aplikace pro hlaseni, sledovani a vyhodnocovani technickych zavad ve skladu CZLC4.

Projekt je pripraveny pro firemni Vibe Coding platformu. Puvodni Streamlit verze byla prevedena na FastAPI backend a staticke webove rozhrani, ktere bezi v kontejneru na portu 8080.

## Co aplikace umi

- Formular pro nahlaseni zavady vcetne oddeleni, technologie, mista, priority a popisu.
- Ulozeni zavady do Firestore v GCP.
- Prilohy k zavade včetně nahledu obrazku primo v detailu.
- Dashboard nad daty z backendu aplikace.
- Prehled nevyresenych zavad, zavad v reseni i vyresenych zavad.
- Prehled vsech dat, grafy, filtry a export.
- Pripominky zavad otevrenych dele nez 24 hodin.
- Automaticke tahani AutoStore/Uniify vypadku primo z API bez n8n a bez Teams.

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

Volitelne hodnoty pro integrace:

- `UNIFY_API_URL` - URL na Uniify/CubeAnalytics API, odkud aplikace pravidelne cte stop udalosti
- `UNIFY_API_TOKEN` - API token pro Uniify/CubeAnalytics, predava se v hlavicce `API-Authorization: Token <token>`
- `UNIFY_POLL_SECONDS` - interval v sekundach pro automaticky sync z Uniify API

Service account se do `config.env` nedava. Platforma ho pouziva pri behu aplikace.

Citlive hodnoty jako API tokeny a hesla se do repozitare neukladaji. Aplikace je umi nacist z prostredi pri behu aplikace.

## Uniify / AutoStore integrace

Aplikace umi novy Uniify/AutoStore stop zpracovat primo z API bez n8n, bez Outlook workflow a bez Teams.

Co je potreba:

1. doplnit `UNIFY_API_URL`
2. doplnit `UNIFY_API_TOKEN`
3. nechat behet aplikaci, aby si data sama stahovala v intervalech

Aplikace pak:

- nacte data z Uniify API,
- rozpozna `System Stop` i `Manual System Stop`,
- zalozi z nich zavadu v aplikaci jako `AutoStore`,
- a stejny vypadek nedeuplikuje.

Pro ručni test existuje i endpoint:

```text
POST /api/integrations/unify-sync
X-API-Key: <WEBHOOK_API_KEY>
```

## Odeslani ticketu

Pri zalozeni zavady se ticket ulozi do Firestore a aplikace si ho sama zobrazi v seznamu i v dashboardu.

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
