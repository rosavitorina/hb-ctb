import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_email(to_address: str, subject: str, body: str, *, from_address: str | None = None) -> bool:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip() or "587")
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    sender = (from_address or os.getenv("SMTP_FROM", "").strip() or "noreply@example.com").strip()

    if not host:
        logger.warning("Email delivery is not configured; SMTP_HOST is missing")
        return False

    try:
        with smtplib.SMTP(host, port) as server:
            if os.getenv("EMAIL_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}:
                server.starttls()
            if username and password:
                server.login(username, password)
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = to_address
            message.set_content(body)
            server.send_message(message)
    except Exception:
        logger.exception("Email delivery failed for %s", to_address)
        return False

    return True


def send_invite_email(email: str, invite_code: str) -> bool:
    subject = "Your HB-CTB invite code"
    body = (
        "Welcome to HB-CTB.\n\n"
        f"Your invite code is: {invite_code}\n\n"
        "This code expires in 72 hours and can only be used once with this email address.\n"
    )
    return send_email(email, subject, body)


def send_generic_invite_email(email: str, invite_code: str, *, app_name: str = "HB Consultas") -> bool:
    subject = "Você foi convidado para HB Consultas"
    body = (
        f"Você foi convidado para {app_name}.\n\n"
        f"Utilize esta chave para fazer uma conta: {invite_code}\n\n"
        "Se você não reconhece esta solicitação, pode ignorar este e-mail."
    )
    return send_email(email, subject, body)


def send_registration_email(email: str) -> bool:
    subject = "Your HB-CTB account is ready"
    body = (
        "Your account has been created successfully.\n\n"
        "You can sign in with your email and password to access your saved market workspace.\n"
    )
    return send_email(email, subject, body)
