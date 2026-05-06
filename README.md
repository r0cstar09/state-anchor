# state-anchor

A daily baseline state primer that runs each morning to generate and email a factual, positive reflection grounded in:
- structural advantages of living in Canada, and
- personal strategic traits that can be leveraged right now.

## What it does now

- Rotates daily focus across Canada advantage categories (institutions, mobility, finance, infrastructure, etc.).
- Builds a **verified evidence pack** for each run:
  - Curated policy/institution facts from official sources.
  - Dynamic cross-country indicators pulled from the World Bank API.
- Builds a rotating **personal trait pack** from your strategic profile (systems thinking, leverage mindset, adaptability, execution, etc.).
- Instructs the LLM to:
  - Use only facts from the evidence pack for hard claims.
  - Cite fact IDs inline (for verifiability).
  - Include explicit country/context contrasts for the Canada section.
  - Include concrete leverage actions for selected personal traits.
- Automatically appends verification links to the outgoing email.

## Key files

- `baseline_mailer.py` — prompt assembly, generation, verification-link append, email sending
- `canada_fact_bank.py` — rotating focus logic + source-backed fact bank + World Bank indicator fetch
- `personal_trait_bank.py` — rotating trait selection and trait-pack rendering
- `prompt.txt` — strict response format for combined Canada + personal-trait grounding

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

## GitHub Actions (ADC)

GitHub-hosted runners do not have local ADC by default.  
To run this project in Actions, add these repository secrets:

- `GCP_SA_KEY`: JSON key for a service account with Vertex AI access
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION` (optional; defaults to `us-central1`)
- `VERTEX_MODEL` (optional; defaults to `gemini-2.5-flash`)
- `VERTEX_MODEL_RESOURCE` (optional)
- `ICLOUD_EMAIL`
- `ICLOUD_PASSWORD`
- `EMAIL_RECIPIENT`
- `EMAIL_SMTP_SERVER`
- `EMAIL_SMTP_PORT`

Minimum service account IAM roles:
- `roles/aiplatform.user`
- `roles/serviceusage.serviceUsageConsumer`

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
