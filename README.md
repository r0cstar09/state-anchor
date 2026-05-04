# state-anchor

A daily baseline state primer that runs each morning to generate and email a factual reflection about the structural advantages of living in Canada.

## What it does now

- Rotates daily focus across Canada advantage categories (institutions, mobility, finance, infrastructure, etc.).
- Builds a **verified evidence pack** for each run:
  - Curated policy/institution facts from official sources.
  - Dynamic cross-country indicators pulled from the World Bank API.
- Instructs the LLM to:
  - Use only facts from the evidence pack for hard claims.
  - Cite fact IDs inline (for verifiability).
  - Include explicit country/context contrasts.
- Automatically appends verification links to the outgoing email.

## Key files

- `baseline_mailer.py` — prompt assembly, generation, verification-link append, email sending
- `canada_fact_bank.py` — rotating focus logic + source-backed fact bank + World Bank indicator fetch
- `prompt.txt` — strict response format and evidence/citation constraints

## Setup

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up Application Default Credentials (ADC):

   ```bash
   bash <(curl -sSL https://storage.googleapis.com/cloud-samples-data/adc/setup_adc.sh)
   ```

   If the script is interactive or stalls, run:

   ```bash
   gcloud auth application-default login
   gcloud auth login --update-adc
   gcloud config set project <your-project-id>
   gcloud auth application-default set-quota-project <your-project-id>
   gcloud services enable aiplatform.googleapis.com --project <your-project-id>
   ```

3. Copy env template and fill values:

   ```bash
   cp .env.example .env
   ```

## Environment Variables

Required:
- `GOOGLE_CLOUD_PROJECT`
- `ICLOUD_EMAIL`
- `ICLOUD_PASSWORD`
- `EMAIL_RECIPIENT`
- `EMAIL_SMTP_SERVER`
- `EMAIL_SMTP_PORT`

Optional (with defaults):
- `GOOGLE_CLOUD_LOCATION` (default: `us-central1`)
- `VERTEX_MODEL` (default: `gemini-2.5-flash`)
- `VERTEX_MODEL_RESOURCE` (optional full Vertex model resource name; overrides `VERTEX_MODEL` when set)

## Run

```bash
python baseline_mailer.py
```
