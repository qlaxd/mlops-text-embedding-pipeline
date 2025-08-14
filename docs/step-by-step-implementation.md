# MLOps Text Embedding Pipeline - Részletes Megvalósítási Útmutató

**Verzió:** 1.0
**Dátum:** 2025-08-14

## Bevezetés

Ez a dokumentum egy lépésről-lépésre követhető útmutató egy programozó számára a `ML_Engineer_test_2025_08_07.pdf` dokumentumban specifikált MLOps pipeline teljes körű megvalósításához. A lépések szigorúan követik a specifikációban leírt követelményeket.

---

## 1. Fázis: Projekt Előkészítése és Helyi Környezet

**Cél:** A projekt vázának létrehozása és a fejlesztői környezet beállítása.

1.  **Könyvtárszerkezet Létrehozása:**
    Nyiss egy terminált és hozd létre a projekt főkönyvtárát és az alábbi alkönyvtárakat:
    ```bash
    mkdir -p mlops-text-embedding-pipeline/src mlops-text-embedding-pipeline/terraform mlops-text-embedding-pipeline/output mlops-text-embedding-pipeline/.github/workflows mlops-text-embedding-pipeline/docs
    cd mlops-text-embedding-pipeline
    ```

2.  **Fájlok Elhelyezése:**
    - Másold a kapott `data.txt`, `model.joblib`, és `requirements.txt` fájlokat a projekt gyökérkönyvtárába.

3.  **Python Virtuális Környezet:**
    - Hozz létre egy Python virtuális környezetet és aktiváld:
      ```bash
      python3.11 -m venv .venv
      source .venv/bin/activate
      ```

4.  **Függőségek Telepítése:**
    - A `requirements.txt` fájlt egészítsd ki a `boto3` (AWS SDK), `PyYAML` (konfigurációhoz) és `python-dotenv` (opcionális, .env fájlokhoz) csomagokkal. A végső fájl tartalma valahogy így nézzen ki:
      ```
      transformers==4.32.1
      sentence-transformers==2.2.2
      tokenizers==0.13.3
      joblib==1.2.0
      huggingface_hub==0.15.1
      boto3
      PyYAML
      python-dotenv
      ```
    - Telepítsd a függőségeket:
      ```bash
      pip install -r requirements.txt
      ```

5.  **Git Inicializálás:**
    - Inicializálj egy Git repository-t és hozz létre egy `.gitignore` fájlt:
      ```bash
      git init
      touch .gitignore
      ```
    - A `.gitignore` fájlba írd bele a következőket a felesleges fájlok kizárásához:
      ```
      .venv/
      __pycache__/
      *.pyc
      .DS_Store
      .env
      terraform.tfstate*
      .terraform/
      ```

---

## 2. Fázis: Python Alkalmazás Fejlesztése (`src/`)

**Cél:** A pipeline központi logikájának megírása moduláris, tesztelhető formában.

1.  **Konfigurációs Fájl (`config.yaml`):**
    - Hozz létre egy `config.yaml` fájlt a gyökérkönyvtárban:
      ```yaml
      pipeline:
        model_path: "model.joblib"
        input_data_path: "data.txt"
        max_seq_length: 2048
        # Ezt a Terraform futtatás után kapott értékkel kell majd felülírni
        s3_bucket_name: "your-bucket-name-placeholder" 
      ```

2.  **Konfiguráció Betöltése (`src/config.py`):**
    - Hozz létre egy `src/config.py` fájlt, ami beolvassa a `config.yaml`-t.
    - **Logika:** Használd a `PyYAML` csomagot a fájl beolvasásához és egy szótárként való visszaadásához.

3.  **Segédfüggvények (`src/utils.py`):**
    - Hozz létre egy `src/utils.py` fájlt.
    - **Logika:** Írj egy `is_valid_input(text: str) -> bool` függvényt. A specifikáció szerint a csak számokból, emojikból stb. álló stringek nem validak. Egy egyszerű reguláris kifejezés használható, ami ellenőrzi, hogy a szöveg tartalmaz-e legalább egy betűt.

4.  **Embedding Logika (`src/embedder.py`):**
    - Hozz létre egy `src/embedder.py` fájlt.
    - **Logika:**
        - Definiálj egy `Embedder` osztályt.
        - Az `__init__` metódus töltse be a modellt a `config.py`-ból kapott útvonalról a `joblib.load()` segítségével.
        - Írj egy `chunk_text(text: str, chunk_size: int)` metódust, ami a `textwrap` vagy egyéni logika segítségével feldarabolja a szöveget a `chunk_size` méretű darabokra.
        - Írj egy `process_text(text: str)` metódust, ami:
            - Validálja a bemenetet az `utils.is_valid_input` segítségével. Ha invalid, `None`-t ad vissza.
            - Darabolja a szöveget a `chunk_text` metódussal.
            - A `model.encode()` függvénnyel legenerálja a beágyazásokat minden darabhoz.
            - Visszaad egy listát, ami a szövegdarabokat és a hozzájuk tartozó beágyazásokat tartalmazza.

5.  **S3 Kezelés (`src/storage.py`):**
    - Hozz létre egy `src/storage.py` fájlt.
    - **Logika:**
        - Definiálj egy `S3Storage` osztályt.
        - Az `__init__` metódus inicializáljon egy `boto3.client('s3')`-at és vegye át a bucket nevét.
        - Írj egy `upload_json_to_s3(data: dict, key: str)` metódust. Ez a metódus alakítsa a `data` szótárat JSON stringgé és töltse fel az S3-ba a megadott `key` (elérési út) alá.
        - **Bónusz:** Implementálj egy egyszerű újrapróbálkozási (retry) logikát az `upload` köré (pl. egy `for` ciklus `time.sleep`-pel), hogy kezelje az átmeneti S3 hibákat.

6.  **Metaadat Generálás (`src/metadata.py`):**
    - Hozz létre egy `src/metadata.py` fájlt.
    - **Logika:**
        - Írj egy `generate_metadata(...)` függvényt.
        - Paraméterként vegye át a feldolgozás eredményeit (input fájl neve, feldolgozott sorok száma, összes chunk száma).
        - A `datetime` modullal generáljon egy ISO 8601 formátumú időbélyeget.
        - A `subprocess` modullal kérdezze le az aktuális Git commit hash-t: `git rev-parse HEAD`.
        - Adja vissza a specifikációnak megfelelő szótárat.

7.  **Pipeline Vezénylés (`src/pipeline.py`):**
    - Hozz létre egy `src/pipeline.py` fájlt.
    - **Logika:**
        - Írj egy `run()` függvényt.
        - Ez a függvény fogja össze a teljes folyamatot:
            1. Inicializálja az `Embedder` és `S3Storage` osztályokat.
            2. Egy ciklussal végigmegy a `data.txt` sorain.
            3. Minden sorra meghívja az `embedder.process_text`-et.
            4. A valid eredményeket (szövegdarabok és vektorok) egy nagy listába/szótárba gyűjti, ami megfelel a kimeneti JSON formátumnak.
            5. A ciklus után meghívja a `storage.upload_json_to_s3`-t, hogy feltöltse az eredményeket egy időbélyeggel ellátott néven (pl. `embeddings/2025-08-14_12-00-00.json`).
            6. Meghívja a `metadata.generate_metadata`-t és az eredményt szintén feltölti az S3-ba.
            7. A `print()` függvényt használja a logolásra, hogy a CloudWatch-ba kerüljenek az üzenetek.

8.  **Belépési Pont (`src/main.py`):**
    - Hozz létre egy `src/main.py` fájlt.
    - **Logika:** Ez a fájl csak importálja és meghívja a `pipeline.run()` függvényt. Használj `if __name__ == "__main__":` blokkot.

---

## 3. Fázis: Konténerizáció (Docker)

**Cél:** Az alkalmazás becsomagolása egy hordozható, konzisztens Docker image-be.

1.  **`.dockerignore` Fájl:**
    - Hozz létre egy `.dockerignore` fájlt a gyökérben, és másold bele ugyanazt, mint a `.gitignore`-ba.

2.  **`Dockerfile` Létrehozása:**
    - Hozz létre egy `Dockerfile`-t a gyökérben:
      ```Dockerfile
      # Stage 1: Base
      FROM python:3.11-slim AS base
      
      # Ne fussunk root-ként
      RUN addgroup --system app && adduser --system --group app
      USER app
      WORKDIR /app
      
      # Python környezet beállításai
      ENV PYTHONDONTWRITEBYTECODE 1
      ENV PYTHONUNBUFFERED 1
      
      # Stage 2: Build
      FROM base AS build
      
      COPY requirements.txt .
      RUN pip install --no-cache-dir --user -r requirements.txt
      
      # Stage 3: Final
      FROM base AS final
      
      # Másoljuk a függőségeket
      COPY --from=build /home/app/.local /home/app/.local
      ENV PATH=/home/app/.local/bin:$PATH
      
      # Másoljuk a forráskódot
      COPY . .
      
      # Futtatás
      CMD ["python", "src/main.py"]
      ```

3.  **`docker-compose.yml` (Lokális Teszteléshez):**
    - Hozz létre egy `docker-compose.yml` fájlt a gyökérben:
      ```yaml
      version: '3.8'
      services:
        app:
          build: .
          volumes:
            # Hogy a kimeneteket lássuk lokálisan
            - ./output:/app/output 
            # AWS credentials átadása
            - ~/.aws:/home/app/.aws:ro
          # .env fájl használata a bucket névhez
          env_file:
            - .env 
      ```
    - Hozz létre egy `.env` fájlt: `S3_BUCKET_NAME=your-test-bucket-name` és módosítsd a Python kódot, hogy ezt is figyelembe vegye (a `python-dotenv` csomaggal).

---

## 4. Fázis: Infrastruktúra Kódként (Terraform)

**Cél:** Az AWS erőforrások leírása kóddal a reprodukálható telepítés érdekében.

1.  **Terraform Fájlok (`terraform/`):**
    - `terraform/variables.tf`: Definiálj változókat (pl. `aws_region`, `project_name`).
    - `terraform/backend.tf`: Konfigurálj egy S3 backendet a Terraform state tárolására.
    - `terraform/main.tf`:
        - **S3 Bucket:** Definiálj egy `aws_s3_bucket` erőforrást. **Fontos:** `versioning_configuration { status = "Enabled" }`.
        - **ECR Repository:** Definiálj egy `aws_ecr_repository`-t a Docker image-nek.
        - **IAM Role/Policy:** Definiálj egy `aws_iam_role`-t és a hozzá tartozó policy-t, ami engedélyezi az ECS Task számára az S3-ba írást és az ECR-ből olvasást.
        - **ECS Cluster & Fargate Task:** Definiálj egy `aws_ecs_cluster`-t és egy `aws_ecs_task_definition`-t. A task definícióban add meg a Docker image URI-ját (az ECR repo URL-jét), a CPU/memória értékeket, a logolást (CloudWatch), és a létrehozott IAM role-t.
        - **CloudWatch Log Group:** Definiálj egy `aws_cloudwatch_log_group`-ot az ECS logoknak.
        - **EventBridge Rule:** Definiálj egy `aws_eventbridge_rule`-t (legyen `schedule_expression`-je, pl. "rate(1 day)") és egy `aws_eventbridge_target`-et, ami az ECS taskot célozza.

---

## 5. Fázis: Telepítés és Futtatás

**Cél:** A teljes rendszer élesítése az AWS-en.

1.  **Docker Image Build & Push:**
    - Jelentkezz be az ECR-be:
      ```bash
      aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.<your-region>.amazonaws.com
      ```
    - Build, tag-eld és push-old az image-et:
      ```bash
      docker build -t <your-ecr-repo-uri>:latest .
      docker push <your-ecr-repo-uri>:latest
      ```

2.  **Infrastruktúra Telepítése:**
    - Navigálj a `terraform` könyvtárba és futtasd:
      ```bash
      terraform init
      terraform plan
      terraform apply --auto-approve
      ```
    - A Terraform `output`-ként írasd ki az S3 bucket nevét, és ezt másold be a `config.yaml`-ba.

3.  **Pipeline Futtatása és Ellenőrzése:**
    - Menj az AWS Console-ba, keresd meg az EventBridge szabályt és indítsd el manuálisan.
    - Pár perc múlva ellenőrizd az S3 bucket-et. Látnod kell az `embeddings/` és `metadata/` mappákban a generált JSON fájlokat.
    - Ellenőrizd a CloudWatch log group-ot a futás logjaiért.

---

## 6. Fázis: Befejező Lépések

**Cél:** A projekt dokumentálása és a végső műtermékek előállítása.

1.  **Példa Kimenetek (`output/`):**
    - Az első sikeres futás után másold a generált `embeddings_...json`, `metadata_...json` fájlokat az `output` könyvtárba. Készíts egy `logs_...txt` fájlt is a CloudWatch logokból.

2.  **`README.md` Megírása:**
    - Hozz létre egy `README.md` fájlt a gyökérkönyvtárban.
    - Írd le benne a projekt célját, az architektúrát, és adj részletes útmutatót a beüzemeléshez (függőségek, környezeti változók) és a futtatáshoz (lokálisan Docker Compose-zal és AWS-en Terraformmal).

Ezzel a lépéssorozattal a projekt teljes mértékben megvalósítható a specifikációnak megfelelően.
