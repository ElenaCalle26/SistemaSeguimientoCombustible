"""Optional SMTP alerts. Demo @fueltrack.local accounts are never recipients."""
from email.message import EmailMessage
import smtplib

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .email_policy import is_deliverable_email, split_recipient_list
from .models import User, Vehicle


def collect_alert_recipients(db: Session, settings: Settings, institution_id) -> list[str]:
    recipients: list[str] = []
    for raw in (
        settings.alert_recipient,
        settings.alert_admin_email,
        settings.alert_supervisor_email,
    ):
        recipients.extend(split_recipient_list(raw))

    users = db.scalars(
        select(User).where(
            User.is_active.is_(True),
            User.role.in_(("ADMIN", "SUPERVISOR")),
        )
    ).all()
    for user in users:
        if not is_deliverable_email(user.email):
            continue
        if user.role == "ADMIN":
            recipients.append(user.email)
        elif institution_id and user.institution_id == institution_id:
            recipients.append(user.email)

    unique: list[str] = []
    seen: set[str] = set()
    for email in recipients:
        key = email.lower()
        if key in seen or not is_deliverable_email(email):
            continue
        seen.add(key)
        unique.append(email)
    return unique


def send_priority_alert(settings: Settings, vehicle: Vehicle, reasons: list[str], recipients: list[str]) -> None:
    if not settings.smtp_host or not recipients:
        return
    message = EmailMessage()
    message["Subject"] = f"FuelTrack: alerta prioritaria para {vehicle.plate}"
    message["From"] = settings.smtp_user or "fueltrack@localhost"
    message["To"] = ", ".join(recipients)
    message.set_content(
        "Alerta sintética de FuelTrack (requiere revisión humana, no es una sanción):\n"
        + "\n".join(reasons)
    )
    try:
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=12)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12)
        with server:
            if settings.smtp_use_starttls and not settings.smtp_use_ssl:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        # SMTP is optional and must never make a fuel operation fail.
        return
