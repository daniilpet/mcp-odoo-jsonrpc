import re

SENSITIVE_PATTERNS: list[str] = [
    "password",
    "passwords",
    "пароль",
    "пароли",
    "парол",
    "доступ",
    "credentials",
    "secret",
    "token",
    r"api\.key",
    r"ssh\.key",
    r"private\.key",
]

_SENSITIVE_RE = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)


def is_sensitive(name: str, content: str | None = None) -> bool:
    if _SENSITIVE_RE.search(name):
        return True
    return bool(content and _SENSITIVE_RE.search(content))
