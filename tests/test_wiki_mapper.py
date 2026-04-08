from mcp_odoo_jsonrpc.acl.mapper import translate_wiki_history, translate_wiki_page
from mcp_odoo_jsonrpc.domain.enums import WikiPageType


def _make_wiki_record(**overrides):
    base = {
        "id": 52,
        "name": "ADR-1: О продукте",
        "display_name": "ADR-1: О продукте",
        "type": "content",
        "color": 0,
        "write_date": "2026-02-06 14:20:37",
        "parent_id": {"id": 44, "display_name": "Architecture Decision Records"},
        "create_uid": {"id": 33, "display_name": "Даниил Петрянкин"},
        "content_uid": {"id": 33, "display_name": "Даниил Петрянкин"},
    }
    base.update(overrides)
    return base


class TestTranslateWikiPage:
    def test_basic_fields(self) -> None:
        record = _make_wiki_record()
        page = translate_wiki_page(record)
        assert page.id == 52
        assert page.name == "ADR-1: О продукте"
        assert page.type == WikiPageType.CONTENT
        assert page.parent_id == 44
        assert page.parent_name == "Architecture Decision Records"
        assert page.color == 0

    def test_category_type(self) -> None:
        record = _make_wiki_record(type="category", name="EDMS")
        page = translate_wiki_page(record)
        assert page.type == WikiPageType.CATEGORY

    def test_no_parent(self) -> None:
        record = _make_wiki_record(parent_id=False)
        page = translate_wiki_page(record)
        assert page.parent_id is None
        assert page.parent_name is None

    def test_parent_as_int(self) -> None:
        record = _make_wiki_record(parent_id=44)
        page = translate_wiki_page(record)
        assert page.parent_id == 44
        assert page.parent_name is None

    def test_content_present(self) -> None:
        record = _make_wiki_record(content="<p>Hello</p>")
        page = translate_wiki_page(record)
        assert page.content == "<p>Hello</p>"

    def test_content_absent(self) -> None:
        record = _make_wiki_record()
        page = translate_wiki_page(record)
        assert page.content is None

    def test_create_uid(self) -> None:
        record = _make_wiki_record()
        page = translate_wiki_page(record)
        assert page.create_uid is not None
        assert page.create_uid.id == 33
        assert page.create_uid.name == "Даниил Петрянкин"

    def test_content_uid_false(self) -> None:
        record = _make_wiki_record(content_uid=False)
        page = translate_wiki_page(record)
        assert page.content_uid is None

    def test_write_date_parsed(self) -> None:
        record = _make_wiki_record()
        page = translate_wiki_page(record)
        assert page.write_date is not None
        assert page.write_date.year == 2026
        assert page.write_date.month == 2

    def test_history_translation(self) -> None:
        record = _make_wiki_record(
            history_ids=[
                {
                    "id": 326,
                    "create_date": "2026-02-06 14:20:37",
                    "name": "autogen",
                    "summary": "Обновлённая документация",
                    "create_uid": {"id": 33, "display_name": "Даниил Петрянкин"},
                },
                {
                    "id": 325,
                    "create_date": "2026-02-06 14:15:54",
                    "name": "autogen",
                    "summary": "Первая версия",
                    "create_uid": {"id": 33, "display_name": "Даниил Петрянкин"},
                },
            ]
        )
        page = translate_wiki_page(record)
        assert len(page.history) == 2
        assert page.history[0].id == 326
        assert page.history[0].summary == "Обновлённая документация"
        assert page.history[1].id == 325

    def test_empty_history(self) -> None:
        record = _make_wiki_record(history_ids=[])
        page = translate_wiki_page(record)
        assert page.history == []


class TestTranslateWikiHistory:
    def test_basic_history(self) -> None:
        record = {
            "id": 326,
            "page_id": {"id": 52, "display_name": "ADR-1"},
            "create_uid": {"id": 33, "display_name": "Даниил Петрянкин"},
            "create_date": "2026-02-06 14:20:37",
            "name": "autogen",
            "summary": "Обновление",
        }
        h = translate_wiki_history(record)
        assert h.id == 326
        assert h.page_id == 52
        assert h.page_name == "ADR-1"
        assert h.author is not None
        assert h.author.id == 33
        assert h.summary == "Обновление"

    def test_page_id_as_int(self) -> None:
        record = {
            "id": 1,
            "page_id": 52,
            "create_uid": False,
            "create_date": False,
            "name": "",
            "summary": "",
        }
        h = translate_wiki_history(record)
        assert h.page_id == 52
        assert h.page_name == ""
        assert h.author is None
