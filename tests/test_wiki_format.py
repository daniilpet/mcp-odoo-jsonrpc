"""Тесты матрицы состояний _format_wiki_page (ADR-009).

| # | restricted | sensitive | Результат                          |
|---|------------|-----------|-------------------------------------|
| 1 | True       | False     | Метаданные, без тела                |
| 2 | True       | True      | То же (тело никогда не показывается)|
| 3 | False      | False     | Всё: заголовок, тело, история       |
| 4 | False      | True      | Метаданные + причина цензуры        |
"""

from datetime import datetime

from mcp_odoo_jsonrpc.domain.enums import WikiPageType
from mcp_odoo_jsonrpc.domain.models import User, WikiPage, WikiPageHistory
from mcp_odoo_jsonrpc.server import _format_wiki_page


def _make_page(**overrides) -> WikiPage:
    defaults = {
        "id": 52,
        "name": "Настройка CI/CD",
        "type": WikiPageType.CONTENT,
        "parent_id": 44,
        "parent_name": "DevOps",
        "write_date": datetime(2026, 4, 8, 12, 0, 0),
        "create_uid": User(id=1, name="Admin"),
        "content_uid": User(id=1, name="Admin"),
        "content": "<p>Пример настройки пайплайна</p>",
        "content_date": datetime(2026, 4, 8, 12, 0, 0),
        "color": 0,
        "history": [
            WikiPageHistory(
                id=1,
                page_id=52,
                page_name="Настройка CI/CD",
                author=User(id=1, name="Admin"),
                create_date=datetime(2026, 4, 8, 12, 0, 0),
                name="v1",
                summary="Первая версия",
            ),
        ],
    }
    defaults.update(overrides)
    return WikiPage(**defaults)


class TestFormatWikiPageMatrix:
    def test_case1_restricted_safe(self) -> None:
        """Строка 1: restricted + нет чувствительных данных."""
        page = _make_page()
        result = _format_wiki_page(page, restricted=True, sensitive_filter=True)

        assert "Настройка CI/CD" in result
        assert "odoo://wiki/52" in result
        assert "Возможно, здесь об этом" in result
        assert "Пример настройки пайплайна" not in result
        assert "История" not in result

    def test_case2_restricted_sensitive(self) -> None:
        """Строка 2: restricted + чувствительный контент — то же поведение."""
        page = _make_page(
            name="Пароли серверов",
            content="<p>root password: 12345</p>",
        )
        result = _format_wiki_page(page, restricted=True, sensitive_filter=True)

        assert "Пароли серверов" in result
        assert "Возможно, здесь об этом" in result
        assert "12345" not in result
        assert "Содержимое скрыто" not in result

    def test_case3_full_safe(self) -> None:
        """Строка 3: full + нет чувствительных данных — всё видно."""
        page = _make_page()
        result = _format_wiki_page(page, restricted=False, sensitive_filter=True)

        assert "Настройка CI/CD" in result
        assert "Пример настройки пайплайна" in result
        assert "История изменений" in result
        assert "Первая версия" in result
        assert "Содержимое скрыто" not in result
        assert "Возможно, здесь об этом" not in result

    def test_case4_full_sensitive(self) -> None:
        """Строка 4: full + чувствительный контент — цензура."""
        page = _make_page(
            name="Настройка сервера",
            content="<p>password: admin123</p>",
        )
        result = _format_wiki_page(page, restricted=False, sensitive_filter=True)

        assert "Настройка сервера" in result
        assert "Содержимое скрыто" in result
        assert "чувствительные данные" in result
        assert "admin123" not in result
        assert "История" not in result

    def test_filter_disabled_shows_sensitive(self) -> None:
        """Фильтр отключён — чувствительный контент показывается."""
        page = _make_page(
            name="Пароли серверов",
            content="<p>root password: supersecret</p>",
        )
        result = _format_wiki_page(page, restricted=False, sensitive_filter=False)

        assert "supersecret" in result
        assert "Содержимое скрыто" not in result

    def test_sensitive_in_name_only(self) -> None:
        """Чувствительное слово в названии — вся страница скрыта."""
        page = _make_page(
            name="Все пароли команды",
            content="<p>Обычный текст без секретов</p>",
        )
        result = _format_wiki_page(page, restricted=False, sensitive_filter=True)

        assert "Содержимое скрыто" in result
        assert "Обычный текст" not in result

    def test_sensitive_in_content_only(self) -> None:
        """Чувствительное слово только в теле — страница скрыта."""
        page = _make_page(
            name="Настройка инфраструктуры",
            content="<p>Используйте token: abc-123-xyz</p>",
        )
        result = _format_wiki_page(page, restricted=False, sensitive_filter=True)

        assert "Содержимое скрыто" in result
        assert "abc-123-xyz" not in result

    def test_html_stripped_in_full_mode(self) -> None:
        """HTML теги удаляются из контента."""
        page = _make_page(content="<p><strong>Bold</strong> text</p>")
        result = _format_wiki_page(page, restricted=False, sensitive_filter=True)

        assert "Bold text" in result
        assert "<p>" not in result
        assert "<strong>" not in result

    def test_no_content_page(self) -> None:
        """Страница без контента — нет секции содержимого."""
        page = _make_page(content=None, history=[])
        result = _format_wiki_page(page, restricted=False, sensitive_filter=True)

        assert "Содержимое" not in result
        assert "История" not in result
