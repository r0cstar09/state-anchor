#!/usr/bin/env python3
"""
state-anchor: Daily baseline state primer mailer.
Generates a gratitude reflection and emails it.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


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
        max_tokens=450,
        temperature=0.7
    )
    
    reflection = response.choices[0].message.content.strip()
    
    # Ensure output is around 350 words
    words = reflection.split()
    if len(words) > 350:
        reflection = ' '.join(words[:350])
    
    return reflection


def send_email(reflection):
    """Send email via iCloud SMTP"""
    smtp_server = os.environ['EMAIL_SMTP_SERVER'].strip('"\'')
    smtp_port = int(os.environ['EMAIL_SMTP_PORT'])
    
    sender_email = os.environ['ICLOUD_EMAIL'].strip('"\'')
    sender_password = os.environ['ICLOUD_PASSWORD'].strip('"\'')
    recipient_email = os.environ['EMAIL_RECIPIENT'].strip('"\'')
    
    # Convert reflection to HTML (preserve line breaks)
    reflection_html = reflection.replace('\n', '<br>')
    
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

