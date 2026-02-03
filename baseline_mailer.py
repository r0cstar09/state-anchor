#!/usr/bin/env python3
"""
state-anchor: Daily baseline state primer mailer.
Generates a gratitude reflection and emails it.
"""

import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


def _is_heading_line(line):
    """True if this single line looks like a section heading (e.g. **Advantage: ...** or **Clear Advantage:**)."""
    line = line.strip()
    if not line:
        return False
    # Markdown ### heading
    if line.startswith('### '):
        return True
    # Bold-only line that looks like a heading (short, or contains key labels)
    if line.startswith('**') and line.endswith('**') and line.count('**') == 2:
        return True
    if re.match(r'^\*\*(Advantage|Clear Advantage|Structural Importance|Expansion of Future|Contrast with)\b', line, re.I):
        return True
    return False


def _heading_line_to_html(line):
    """Render a single heading line to HTML (strip ### or **)."""
    raw = line.strip()
    if raw.startswith('### '):
        content = raw[4:].strip()
    else:
        content = re.sub(r'^\*\*(.+)\*\*$', r'\1', raw)
    safe = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        '<h3 style="margin: 1.5em 0 0.6em 0; font-size: 1.1em; font-weight: 600;">'
        + safe + '</h3>'
    )


def reflection_to_html(reflection):
    """Convert reflection text to HTML with proper paragraph and heading spacing."""
    blocks = re.split(r'\n\s*\n', reflection)
    html_parts = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = [ln.strip() for ln in block.split('\n') if ln.strip()]
        if not lines:
            continue
        # First line is a heading -> emit as <h3>, then rest as paragraph(s)
        if _is_heading_line(lines[0]):
            html_parts.append(_heading_line_to_html(lines[0]))
            rest = '\n'.join(lines[1:])
            if rest:
                safe = rest.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
                safe = safe.replace('\n', '<br>')
                html_parts.append('<p style="margin: 0 0 1.25em 0;">' + safe + '</p>')
            continue
        # Plain paragraph
        safe = block.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)
        safe = safe.replace('\n', '<br>')
        html_parts.append('<p style="margin: 0 0 1.25em 0;">' + safe + '</p>')
    return '\n'.join(html_parts)


def load_prompt():
    """Load the prompt from prompt.txt"""
    with open('prompt.txt', 'r', encoding='utf-8') as f:
        return f.read().strip()


def generate_reflection(prompt):
    """Generate reflection using Azure OpenAI API"""
    endpoint = os.environ['AZURE_OPENAI_ENDPOINT'].strip('"\'')
    # Ensure endpoint has https:// protocol
    if not endpoint.startswith('http://') and not endpoint.startswith('https://'):
        endpoint = 'https://' + endpoint
    
    client = AzureOpenAI(
        api_key=os.environ['AZURE_OPENAI_API_KEY'].strip('"\''),
        api_version='2024-08-01-preview',
        azure_endpoint=endpoint
    )
    
    response = client.chat.completions.create(
        model=os.environ['AZURE_OPENAI_DEPLOYMENT'].strip('"\''),
        messages=[
            {'role': 'system', 'content': 'You are a calm, factual assistant that helps with grounded reflections.'},
            {'role': 'user', 'content': prompt}
        ],
        max_tokens=700,
        temperature=0.7
    )
    
    reflection = response.choices[0].message.content.strip()
    
    # Cap at 400 words, truncating at paragraph boundaries so spacing is preserved
    paragraphs = re.split(r'\n\s*\n', reflection)
    result = []
    word_count = 0
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        n = len(p.split())
        if word_count + n <= 400:
            result.append(p)
            word_count += n
        elif word_count == 0:
            # first paragraph is over 400 words: truncate by words
            result.append(' '.join(p.split()[:400]))
            word_count = 400
            break
        else:
            break
    reflection = '\n\n'.join(result)
    
    return reflection


def send_email(reflection):
    """Send email via iCloud SMTP"""
    smtp_server = os.environ['EMAIL_SMTP_SERVER'].strip('"\'')
    smtp_port = int(os.environ['EMAIL_SMTP_PORT'])
    
    sender_email = os.environ['ICLOUD_EMAIL'].strip('"\'')
    sender_password = os.environ['ICLOUD_PASSWORD'].strip('"\'')
    recipient_email = os.environ['EMAIL_RECIPIENT'].strip('"\'')
    
    # Convert reflection to HTML with proper paragraph and heading spacing
    reflection_html = reflection_to_html(reflection)
    
    # Create HTML email body with reminder
    html_body = f"""
    <html>
      <head></head>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
          <p style="margin: 0; font-size: 14px; color: #666;">
            <strong>Reminder:</strong> Read this gratitude reflection out loud and feel it.
          </p>
        </div>
        <div style="font-size: 16px; line-height: 1.8;">
          {reflection_html}
        </div>
      </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = 'state-anchor: Daily Baseline State Primer'
    
    msg.attach(MIMEText(html_body, 'html'))
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.set_debuglevel(0)  # Set to 1 for debugging
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


def main():
    """Main execution"""
    prompt = load_prompt()
    reflection = generate_reflection(prompt)
    send_email(reflection)


if __name__ == '__main__':
    main()

