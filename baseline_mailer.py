#!/usr/bin/env python3
"""
state-anchor: Daily baseline state primer mailer.
Generates a factual, source-backed Canada advantage reflection and emails it.
"""

import os
import re
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Sequence

from dotenv import load_dotenv
from openai import AzureOpenAI

from canada_fact_bank import (
    ResolvedFact,
    build_daily_fact_pack,
    choose_daily_focus,
    fact_id_set,
    render_focus_and_evidence,
)

load_dotenv()

MAX_REFLECTION_WORDS = 550
FACT_ID_RE = re.compile(r"\[(F\d{3})\]")


def _is_heading_line(line: str) -> bool:
    """True if this line looks like a section heading."""
    line = line.strip()
    if not line:
        return False
    if line.startswith("### "):
        return True
    if line.startswith("**") and line.endswith("**") and line.count("**") == 2:
        return True
    return bool(
        re.match(
            r"^\*\*(Advantage|Clear Advantage|Structural Importance|Expansion of Future|"
            r"Contrast with|Contrast / What to be grateful for|Trajectory conclusion|"
            r"Fact to retain|Sources \(Fact IDs\)|Verification links)\b",
            line,
            re.I,
        )
    )


def _heading_line_to_html(line: str) -> str:
    """Render a single heading line to HTML (strip ### or **)."""
    raw = line.strip()
    if raw.startswith("### "):
        content = raw[4:].strip()
    else:
        content = re.sub(r"^\*\*(.+)\*\*$", r"\1", raw)
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        '<h3 style="margin: 1.5em 0 0.6em 0; font-size: 1.1em; font-weight: 600;">'
        + safe
        + "</h3>"
    )


def reflection_to_html(reflection: str) -> str:
    """Convert reflection text to HTML with proper paragraph and heading spacing."""
    blocks = re.split(r"\n\s*\n", reflection)
    html_parts = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        if _is_heading_line(lines[0]):
            html_parts.append(_heading_line_to_html(lines[0]))
            rest = "\n".join(lines[1:])
            if rest:
                safe = (
                    rest.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
                safe = safe.replace("\n", "<br>")
                html_parts.append('<p style="margin: 0 0 1.25em 0;">' + safe + "</p>")
            continue
        safe = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
        safe = safe.replace("\n", "<br>")
        html_parts.append('<p style="margin: 0 0 1.25em 0;">' + safe + "</p>")
    return "\n".join(html_parts)


def _truncate_by_words(text: str, max_words: int) -> str:
    """Truncate at paragraph boundaries while preserving formatting blocks."""
    paragraphs = re.split(r"\n\s*\n", text)
    result = []
    word_count = 0
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        n = len(paragraph.split())
        if word_count + n <= max_words:
            result.append(paragraph)
            word_count += n
        elif word_count == 0:
            result.append(" ".join(paragraph.split()[:max_words]))
            break
        else:
            break
    return "\n\n".join(result)


def _extract_cited_fact_ids(text: str, valid_ids: set[str]) -> list[str]:
    seen = []
    for fact_id in FACT_ID_RE.findall(text):
        if fact_id in valid_ids and fact_id not in seen:
            seen.append(fact_id)
    return seen


def _append_verification_links(
    reflection: str, fact_pack: Sequence[ResolvedFact]
) -> str:
    """
    Always append compact source links so every run has verifiable references,
    even if the model forgets the sources block.
    """
    valid_ids = fact_id_set(fact_pack)
    cited_ids = _extract_cited_fact_ids(reflection, valid_ids)
    if not cited_ids:
        cited_ids = [f.fact_id for f in fact_pack[:4]]

    by_id = {f.fact_id: f for f in fact_pack}
    lines = ["**Verification links (auto-added):**", ""]
    for fact_id in cited_ids:
        fact = by_id.get(fact_id)
        if not fact:
            continue
        lines.append(f"- {fact_id}: {' ; '.join(fact.source_urls)}")
    return reflection.rstrip() + "\n\n" + "\n".join(lines)


def load_prompt() -> tuple[str, list[ResolvedFact]]:
    """
    Load base prompt and append daily focus + source-backed evidence pack.
    """
    with open("prompt.txt", "r", encoding="utf-8") as handle:
        base = handle.read().strip()

    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    focus = choose_daily_focus(day_of_year)
    fact_pack = build_daily_fact_pack(
        day_of_year=day_of_year,
        focus_categories=focus["categories"],
        comparison_tags=focus["comparison_tags"],
    )
    focus_and_evidence = render_focus_and_evidence(
        focus_categories=focus["categories"],
        comparison_label=focus["comparison_label"],
        fact_pack=fact_pack,
    )
    return base + "\n\n" + focus_and_evidence, fact_pack


def generate_reflection(prompt: str, fact_pack: Sequence[ResolvedFact]) -> str:
    """Generate reflection using Azure OpenAI API."""
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].strip('"\'')
    if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
        endpoint = "https://" + endpoint

    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"].strip('"\''),
        api_version="2024-08-01-preview",
        azure_endpoint=endpoint,
    )

    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"].strip('"\''),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a calm, factual assistant. "
                    "Never invent numbers, rankings, or policies."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1100,
        temperature=0.35,
    )

    reflection = (response.choices[0].message.content or "").strip()
    if not reflection:
        raise RuntimeError("Model returned empty reflection content.")

    reflection = _truncate_by_words(reflection, MAX_REFLECTION_WORDS)
    reflection = _append_verification_links(reflection, fact_pack)
    return reflection


def send_email(reflection: str) -> None:
    """Send email via SMTP."""
    smtp_server = os.environ["EMAIL_SMTP_SERVER"].strip('"\'')
    smtp_port = int(os.environ["EMAIL_SMTP_PORT"])

    sender_email = os.environ["ICLOUD_EMAIL"].strip('"\'')
    sender_password = os.environ["ICLOUD_PASSWORD"].strip('"\'')
    recipient_email = os.environ["EMAIL_RECIPIENT"].strip('"\'')

    reflection_html = reflection_to_html(reflection)

    html_body = f"""
    <html>
      <head></head>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 680px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
          <p style="margin: 0; font-size: 14px; color: #666;">
            <strong>Reminder:</strong> Read this reflection out loud and anchor to the facts.
          </p>
        </div>
        <div style="font-size: 16px; line-height: 1.8;">
          {reflection_html}
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = "state-anchor: Daily Baseline State Primer"
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.set_debuglevel(0)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


def main() -> None:
    """Main execution."""
    prompt, fact_pack = load_prompt()
    reflection = generate_reflection(prompt, fact_pack)
    send_email(reflection)


if __name__ == "__main__":
    main()

