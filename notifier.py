"""Optional email notifier for failed compliance checks."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage



def send_failure_email(subject: str, body: str, recipient: str) -> None:
    """Send a failure notification email using SMTP environment variables.

    Required env vars:
    - SMTP_HOST
    - SMTP_PORT
    - SMTP_USER
    - SMTP_PASS
    - SMTP_FROM
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM")

    if not all([host, user, password, sender, recipient]):
        raise ValueError("SMTP configuration is incomplete. Set SMTP_* env vars and recipient.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(message)
