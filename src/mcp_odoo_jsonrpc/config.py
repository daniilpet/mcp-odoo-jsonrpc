import contextlib
import json
import logging
import os
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

SESSION_DIR = Path.home() / ".config" / "odoo-cli"
SESSION_FILE = SESSION_DIR / "session.json"
KEYRING_SERVICE = "odoo-cli"


class TrustMode(StrEnum):
    RESTRICTED = "restricted"
    FULL = "full"


def _keyring_available() -> bool:
    try:
        import keyring

        keyring.get_credential(KEYRING_SERVICE, "test-probe")
        return True
    except Exception:
        return False


def _keyring_set(base_url: str, session_id: str) -> bool:
    try:
        import keyring

        keyring.set_password(KEYRING_SERVICE, base_url, session_id)
        return True
    except Exception:
        logger.warning("keyring недоступен — session_id сохранён в plaintext файле")
        return False


def _keyring_get(base_url: str) -> str | None:
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, base_url)
    except Exception:
        return None


def _keyring_delete(base_url: str) -> None:
    with contextlib.suppress(Exception):
        import keyring

        keyring.delete_password(KEYRING_SERVICE, base_url)


class OdooSession(BaseModel):
    base_url: str
    session_id: str
    uid: int
    employee_id: int
    company_ids: list[int]
    lang: str = "ru_RU"
    tz: str = "Europe/Moscow"
    display_name: str = ""

    def save(self) -> None:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)

        keyring_ok = _keyring_set(self.base_url, self.session_id)

        data = self.model_dump()
        if keyring_ok:
            del data["session_id"]

        SESSION_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls) -> "OdooSession":
        if not SESSION_FILE.exists():
            raise FileNotFoundError(
                f"Сессия не найдена: {SESSION_FILE}\n"
                "Выполните 'mcp-odoo-cli login' для авторизации."
            )
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))

        if "session_id" not in data:
            session_id = _keyring_get(data.get("base_url", ""))
            if not session_id:
                raise RuntimeError(
                    "session_id не найден ни в keyring, ни в session.json.\n"
                    "Выполните 'mcp-odoo-cli login' для повторной авторизации."
                )
            data["session_id"] = session_id

        return cls(**data)

    @classmethod
    def exists(cls) -> bool:
        return SESSION_FILE.exists()

    @classmethod
    def clear(cls) -> None:
        if SESSION_FILE.exists():
            with contextlib.suppress(Exception):
                data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
                _keyring_delete(data.get("base_url", ""))
            SESSION_FILE.unlink()


class OdooEnvConfig(BaseSettings):
    model_config = {"env_prefix": "ODOO_"}

    base_url: str
    session_id: str
    uid: int
    employee_id: int = 0
    company_ids: str = ""
    lang: str = "ru_RU"
    tz: str = "Europe/Moscow"
    trust_mode: str = "restricted"
    allowed_projects: str = ""

    def to_session(self) -> OdooSession:
        cids = [int(c.strip()) for c in self.company_ids.split(",") if c.strip()]
        return OdooSession(
            base_url=self.base_url,
            session_id=self.session_id,
            uid=self.uid,
            employee_id=self.employee_id or self.uid,
            company_ids=cids,
            lang=self.lang,
            tz=self.tz,
        )


def _parse_trust_mode() -> TrustMode:
    raw = os.environ.get("ODOO_TRUST_MODE", "restricted").strip().lower()
    try:
        return TrustMode(raw)
    except ValueError:
        logger.warning("Unknown ODOO_TRUST_MODE=%r, defaulting to restricted", raw)
        return TrustMode.RESTRICTED


def _parse_allowed_projects() -> list[int] | None:
    raw = os.environ.get("ODOO_ALLOWED_PROJECTS", "").strip()
    if not raw:
        return None
    return [int(p.strip()) for p in raw.split(",") if p.strip()]


class OdooConfig:
    def __init__(
        self,
        session: OdooSession,
        trust_mode: TrustMode | None = None,
        allowed_project_ids: list[int] | None = None,
    ) -> None:
        self._session = session
        self._trust_mode = trust_mode if trust_mode is not None else _parse_trust_mode()
        self._allowed_project_ids = (
            allowed_project_ids if allowed_project_ids is not None else _parse_allowed_projects()
        )

    @classmethod
    def from_session_file(
        cls,
        trust_mode_override: TrustMode | None = None,
    ) -> "OdooConfig":
        return cls(
            OdooSession.load(),
            trust_mode=trust_mode_override,
        )

    @classmethod
    def from_env(cls) -> "OdooConfig":
        env_config = OdooEnvConfig()
        trust = TrustMode(env_config.trust_mode) if env_config.trust_mode else TrustMode.RESTRICTED
        projects = [
            int(p.strip()) for p in env_config.allowed_projects.split(",") if p.strip()
        ] or None
        return cls(env_config.to_session(), trust_mode=trust, allowed_project_ids=projects)

    @classmethod
    def auto(cls) -> "OdooConfig":
        if OdooSession.exists():
            return cls.from_session_file()
        return cls.from_env()

    @property
    def trust_mode(self) -> TrustMode:
        return self._trust_mode

    @property
    def is_restricted(self) -> bool:
        return self._trust_mode == TrustMode.RESTRICTED

    @property
    def allowed_project_ids(self) -> list[int] | None:
        return self._allowed_project_ids

    @property
    def base_url(self) -> str:
        return self._session.base_url

    @property
    def session_id(self) -> str:
        return self._session.session_id

    @property
    def uid(self) -> int:
        return self._session.uid

    @property
    def employee_id(self) -> int:
        return self._session.employee_id

    @property
    def display_name(self) -> str:
        return self._session.display_name

    @property
    def allowed_company_ids(self) -> list[int]:
        return self._session.company_ids

    @property
    def context(self) -> dict[str, Any]:
        return {
            "lang": self._session.lang,
            "tz": self._session.tz,
            "uid": self._session.uid,
            "allowed_company_ids": self._session.company_ids,
        }
