# MLOps Text Embedding Pipeline - Tervdokumentáció

**Verzió:** 1.0
**Dátum:** 2025-08-14
**Szerző:** Gemini (Senior Software Architect)

## 1. Bevezetés és Célkitűzések

Ez a dokumentum a "MLOps Text Embedding Pipeline" projekt technikai tervét és architektúráját részletezi. A projekt célja egy minimális, de productie-kész MLOps batch pipeline kiépítése és telepítése, amely szöveges bemeneteket dolgoz fel és alakít át vektoros beágyazásokká (vector embeddings) egy adott HuggingFace-kompatibilis modell segítségével.

### Főbb Célkitűzések:

- **Automatizált Feldolgozás:** Szöveges adatok automatikus, kötegelt (batch) feldolgozása.
- **Szöveg Darabolás (Chunking):** A modell maximális szekvenciahosszát meghaladó szövegek intelligens darabolása.
- **Verziókezelt Adattárolás:** A feldolgozott adatok és a hozzájuk tartozó beágyazások tárolása egy verziókezeléssel ellátott S3 bucketben az auditálhatóság érdekében.
- **Metaadatok Naplózása:** Minden futtatásról részletes metaadatok (időbélyeg, feldolgozott inputok száma, modell verzió, stb.) rögzítése.
- **Infrastruktúra mint Kód (IaC):** Az összes felhő erőforrás definiálása és kezelése Terraform segítségével.
- **Konténerizáció:** A teljes alkalmazás Docker konténerbe csomagolása a hordozhatóság és a konzisztens futtatási környezet biztosításáért.
- **Monitorozás és Hibakezelés:** Alapszintű monitorozás és logolás implementálása, valamint a pipeline robusztussá tétele a hibás bemenetekkel szemben.
- **Konfigurálhatóság:** A pipeline paramétereinek (pl. S3 bucket név, chunk méret) külső konfigurációs fájlból történő kezelése.

## 2. Rendszerarchitektúra

A javasolt architektúra egy eseményvezérelt, szerver nélküli megközelítést követ az AWS felhőben, a maximális skálázhatóság és a minimális üzemeltetési teher érdekében.

![Architecture Diagram](https://i.imgur.com/9A3XIPG.png)
*(Megjegyzés: Ez egy koncepcionális diagram a folyamat szemléltetésére)*

### Komponensek és Technológiák:

- **Futtatási Környezet:** **AWS ECS Fargate**
  - **Indoklás:** Szerver nélküli konténer-futtató szolgáltatás, amely ideális batch feladatokhoz. Nem igényel EC2-példányok menedzselését, és a feladatok erőforrás-igénye (CPU/memória) könnyen skálázható. Robusztusabb a hosszú futási idejű feladatokhoz, mint az AWS Lambda.

- **Konténerizáció:** **Docker**
  - **Indoklás:** Az iparági szabvány a szoftverek izolált, hordozható környezetbe csomagolására. Biztosítja, hogy az alkalmazás ugyanúgy fusson a fejlesztői gépen, mint a cloud környezetben. A `python:3.11-slim` alapképet használjuk a biztonság és a méretoptimalizálás jegyében.

- **Adattárolás:** **AWS S3 (Simple Storage Service)**
  - **Indoklás:** Költséghatékony, rendkívül tartós és skálázható objektumtároló.
    - **Felhasználás:**
      1.  **Kimenetek és Metaadatok:** A generált JSON fájlok tárolása. A **verziókezelés** bekapcsolása kritikus az auditálhatóság és a visszakereshetőség szempontjából.
      2.  **Terraform State:** A Terraform állapotfájljának (remote state) központi, biztonságos tárolása.

- **Ütemezés és Indítás:** **AWS EventBridge**
  - **Indoklás:** Lehetővé teszi a pipeline időzített (pl. `cron(0 2 * * ? *)` - minden nap hajnali 2-kor) vagy eseményvezérelt (pl. manuális indítás) futtatását.

- **Infrastruktúra mint Kód:** **Terraform**
  - **Indoklás:** Lehetővé teszi a teljes felhő-infrastruktúra (S3, ECS, IAM, stb.) deklaratív kódként való leírását, verziókezelését és automatizált telepítését.

- **Logolás és Monitorozás:** **AWS CloudWatch**
  - **Indoklás:** Az ECS Fargate natívan integrálódik a CloudWatch-csal. Minden, a konténer által a standard outputra írt log automatikusan ide kerül, lehetővé téve a központi naplózást, elemzést és riasztások beállítását.

- **Identitás- és Hozzáférés-kezelés:** **AWS IAM**
  - **Indoklás:** A "least privilege" elv követéséhez. Külön IAM Role-t hozunk létre az ECS Task számára, amely csak a szükséges S3 bucket-hez és más erőforrásokhoz biztosít hozzáférést.

- **Alkalmazás:** **Python 3.11**
  - **Indoklás:** A megadott `requirements.txt` és a data science/ML közösségben való elterjedtsége miatt egyértelmű választás.

## 3. Részletes Működési Folyamat (Workflow)

1.  **Indítás:** Egy AWS EventBridge szabály (időzített vagy manuális) elindít egy új ECS Taskot a definiált Fargate klaszterben.
2.  **Konténer Indulása:** Az ECS lehúzza a legfrissebb Docker image-et az ECR-ből (Elastic Container Registry) és elindítja a konténert.
3.  **Inicializálás:** A konténerben futó `src/main.py` szkript elindul.
    - Betölti a konfigurációt a `config.yaml` fájlból (pl. S3 bucket név, chunk méret).
    - Betölti a `model.joblib` modellt a memóriába (`embedder.py`).
4.  **Adatfeldolgozás:** A szkript soronként olvassa a `data.txt` fájlt.
    - **Validáció:** Minden sort validál (`utils.py`). A nem megfelelő sorokat (pl. csak számokat tartalmazó) kihagyja, és egy figyelmeztető üzenetet logol a CloudWatch-ba.
    - **Darabolás (Chunking):** Ha egy sor hossza meghaladja a modell által megengedett 2048 karaktert, a szöveget több, egymást átfedő darabra (chunk) bontja (`embedder.py`).
    - **Beágyazás Készítése:** Minden szövegdarabhoz legenerálja a vektoros beágyazást a betöltött modellel.
5.  **Eredmények Aggregálása:** A futás során feldolgozott összes adatot (eredeti szövegdarabok és a hozzájuk tartozó vektorok) egyetlen, a specifikációnak megfelelő struktúrájú JSON objektumba gyűjti.
6.  **Adatok Mentése S3-ba:**
    - A futás végén a generált, nagy JSON fájlt elmenti az S3 bucket `embeddings/` mappájába. A fájl neve egy időbélyeg lesz (pl. `2025-08-14_10-30-00.json`).
    - A `storage.py` modul felelős a feltöltésért, amely hibakezeléssel és újrapróbálkozási (retry) logikával van ellátva az S3 API hibák esetére.
7.  **Metaadatok Mentése:** A `metadata.py` segítségével legenerál egy metaadat JSON fájlt (futás időbélyege, input fájl neve, feldolgozott sorok száma, létrehozott chunk-ok száma, pipeline verziója a Git commit hash alapján), és ezt is feltölti az S3 bucket `metadata/` mappájába.
8.  **Befejezés és Logolás:** A szkript sikeresen lefut, a Fargate task leáll. A teljes futás alatt keletkezett minden log (print, warning, error) a CloudWatch-ban érhető el.

## 4. Projekt Struktúra

A projekt a specifikációnak megfelelő, jól strukturált könyvtárszerkezetet követi:

```
mlops-text-embedding-pipeline/
├── .github/
│   └── workflows/
│       └── ci.yml              # Opcionális: CI/CD workflow (lint, test, build)
├── docs/
│   └── Plan.md                 # Ez a dokumentum
├── output/                     # Példa kimenetek a futásból
│   ├── embeddings_YYYY-MM-DD.json
│   ├── metadata_YYYY-MM-DD.json
│   └── logs_YYYY-MM-DD.txt
├── src/                        # A Python alkalmazás forráskódja
│   ├── __init__.py
│   ├── main.py                 # A pipeline belépési pontja
│   ├── pipeline.py             # A teljes feldolgozási folyamat vezénylése
│   ├── embedder.py             # Modell betöltése, darabolás, beágyazás
│   ├── storage.py              # S3 feltöltési logika és hibakezelés
│   ├── metadata.py             # Metaadatok generálása
│   └── utils.py                # Segédfüggvények (pl. validáció)
├── terraform/                  # Infrastruktúra kódja
│   ├── main.tf                 # Fő definíciók (ECS, S3, EventBridge)
│   ├── variables.tf            # Változók (pl. régió, projekt neve)
│   ├── outputs.tf              # Terraform által generált kimenetek
│   └── backend.tf              # Remote state konfiguráció
├── .dockerignore               # Docker build során figyelmen kívül hagyandó fájlok
├── .gitignore                  # Git által figyelmen kívül hagyandó fájlok
├── config.yaml                 # Konfigurációs paraméterek
├── data.txt                    # Bemeneti adatok
├── Dockerfile                  # Docker image definíciója
├── docker-compose.yml          # Lokális fejlesztés és tesztelés segítésére
├── model.joblib                # A gépi tanulási modell
├── README.md                   # Projekt leírása, beüzemelési és futtatási útmutató
└── requirements.txt            # Python függőségek
```

## 5. Megvalósítási Fázisok

1.  **Fázis: Helyi Fejlesztés és Core Logika**
    - A projekt struktúra létrehozása.
    - A Python szkriptek (`embedder`, `utils`, `pipeline`, `main`) megírása és tesztelése lokálisan, a `data.txt` és `model.joblib` fájlokkal.
2.  **Fázis: Konténerizáció és Konfiguráció**
    - A `config.yaml` integrálása a Python kódba.
    - A `Dockerfile` megírása (slim image, non-root user).
    - A `docker-compose.yml` létrehozása a konténeres alkalmazás egyszerű, lokális indításához és teszteléséhez.
3.  **Fázis: Infrastruktúra (Terraform)**
    - A Terraform fájlok megírása az összes szükséges AWS erőforrás (S3, ECR, ECS, EventBridge, IAM) létrehozásához.
    - A Terraform remote state beállítása S3-ra.
4.  **Fázis: Integráció és Telepítés (Deployment)**
    - Egy segédszkript létrehozása a Docker image buildelésére és feltöltésére az AWS ECR-be.
    - A `terraform apply` futtatása az infrastruktúra kiépítéséhez.
    - A pipeline első tesztfuttatása az AWS-en, az eredmények és logok ellenőrzése S3-ban és CloudWatch-ban.
5.  **Fázis: CI/CD és Dokumentáció**
    - (Opcionális) GitHub Actions workflow beállítása a kódminőség (linting) és tesztek automatikus ellenőrzésére.
    - A `README.md` és a példa `output` fájlok véglegesítése.

## 6. Kockázatok és Kezelésük

- **Kockázat:** A `model.joblib` túl nagy, ami lassú image buildet és magas ECR tárolási költséget eredményez.
  - **Kezelés:** A modellt nem építjük be az image-be, hanem egy külön S3 bucket-ben tároljuk, és a konténer indulásakor tölti le azt.
- **Kockázat:** A feldolgozási idő egy-egy input fájl esetén extrém hosszú.
  - **Kezelés:** A Fargate erőforrásainak (CPU/memória) növelése. Ha a probléma továbbra is fennáll, az architektúra átalakítása egy még jobban párhuzamosított mintára (pl. SQS + Lambda/Fargate, ahol minden üzenet egy feldolgozandó sort tartalmaz).
- **Kockázat:** Hibás függőségek vagy Python környezetbeli inkompatibilitás.
  - **Kezelés:** A `requirements.txt` pontos verzióinak rögzítése (`pip freeze`). A Docker biztosítja a konzisztens környezetet.
