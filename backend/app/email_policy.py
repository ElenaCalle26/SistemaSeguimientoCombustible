"""Account emails: deliverable addresses plus reserved @fueltrack.local demos."""
from email_validator import EmailNotValidError, validate_email

DEMO_EMAIL_DOMAIN = "fueltrack.local"


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def is_demo_email(value: str) -> bool:
    email = normalize_email(value)
    return email.endswith(f"@{DEMO_EMAIL_DOMAIN}")


def is_deliverable_email(value: str) -> bool:
    """True only for real inboxes. Demo .local addresses are never mailed."""
    email = normalize_email(value)
    if not email or is_demo_email(email):
        return False
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def parse_account_email(value: str) -> str:
    """Accept Gmail/real domains and synthetic @fueltrack.local demo users."""
    email = normalize_email(value)
    local_part, separator, domain = email.partition("@")
    if not separator or not local_part or not domain or " " in email:
        raise ValueError("Correo no válido")
    if domain == DEMO_EMAIL_DOMAIN:
        if any(char in local_part for char in " <>,"):
            raise ValueError("Correo no válido")
        return email
    try:
        return validate_email(email, check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise ValueError("Correo no válido") from exc


def split_recipient_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.replace(";", ",").split(",") if item.strip()]
