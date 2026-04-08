import re

SENSITIVE_PATTERNS: list[str] = [
    "password",
    "passwords",
    "пароль",
    "пароли",
    "парол",
    "credentials",
    "secret",
    "token",
    r"api[\.\-_]key",
    r"ssh[\.\-_]key",
    r"private[\.\-_]key",
    r"данные\s+для\s+входа",
    r"учётные\s+данные",
    r"ключ\s+доступа",
]

_SENSITIVE_RE = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)


def is_sensitive(name: str, content: str | None = None) -> bool:
    if _SENSITIVE_RE.search(name):
        return True
    return bool(content and _SENSITIVE_RE.search(content))
