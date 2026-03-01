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
