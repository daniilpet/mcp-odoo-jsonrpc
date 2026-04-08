import pytest

from mcp_odoo_jsonrpc.domain.sensitive import is_sensitive


class TestIsSensitive:
    @pytest.mark.parametrize(
        "name",
        [
            "Пароли серверов",
            "Серверные password",
            "CREDENTIALS для CI",
            "API.key от Stripe",
            "SSH.key доступ",
            "Private.key сертификат",
            "TOKEN аутентификации",
            "SECRET для JWT",
            "Пароль от WiFi",
            "Доступ к серверу",
        ],
    )
    def test_sensitive_name_detected(self, name: str) -> None:
        assert is_sensitive(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "Архитектура проекта",
            "ADR-001: Выбор языка",
            "Настройка CI/CD",
            "Описание API endpoints",
            "Руководство пользователя",
        ],
    )
    def test_safe_name_not_detected(self, name: str) -> None:
        assert is_sensitive(name) is False

    def test_sensitive_content_detected(self) -> None:
        assert is_sensitive("Настройка сервера", "Вот пароль: 12345") is True

    def test_sensitive_content_english(self) -> None:
        assert is_sensitive("Server Setup", "password: admin123") is True

    def test_safe_content_not_detected(self) -> None:
        assert is_sensitive("Настройка сервера", "Установите nginx и настройте proxy") is False

    def test_none_content_safe(self) -> None:
        assert is_sensitive("Обычная страница", None) is False

    def test_empty_content_safe(self) -> None:
        assert is_sensitive("Обычная страница", "") is False

    def test_case_insensitive(self) -> None:
        assert is_sensitive("PASSWORD MANAGEMENT") is True
        assert is_sensitive("Парол от базы") is True
