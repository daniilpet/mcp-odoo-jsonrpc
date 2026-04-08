# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версионирование следует [Semantic Versioning](https://semver.org/lang/ru/).

## [0.3.0] - 2026-04-08

### Added

- Поддержка wiki (`document.page` / EDMS) — чтение, создание, поиск
- 4 MCP tools: `list_wiki_pages`, `get_wiki_page`, `create_wiki_page`,
  `search_wiki`
- 3 MCP resources: `odoo://wiki/categories`,
  `odoo://wiki/category/{id}`, `odoo://wiki/{id}`
- Автоматический фильтр чувствительного контента (пароли, ключи,
  токены) — цензурирует всю страницу при обнаружении (ADR-009)
- `ODOO_WIKI_SENSITIVE_FILTER=off` для отключения фильтра
- Доменные модели: `WikiPage`, `WikiPageHistory`, `WikiPageType`
- `OdooWikiService` — отдельный сервис для wiki-операций
- 52 новых теста (77 всего): sensitive filter, wiki mapper,
  матрица состояний `_format_wiki_page`
- GitHub Actions адаптированы под Git Flow (ci, version-bump,
  changelog-check)
- Защита веток `main` и `develop` (PR required, CI gates)

### Changed

- MCP-сервер переименован: "Odoo Tasks" → "Odoo"
- ADR-009: архитектурное решение по wiki и фильтру

### Fixed

- Обработка `False` вместо пустой строки в `document.page.history`
  (Odoo-специфика)

## [0.2.0] - 2026-04-08

### Added

- Поддержка подзадач (`child_ids`) в `get_task` и вложенных задач
- MCP Resources: `odoo://user/tasks`, `odoo://project/{id}/tasks`,
  `odoo://task/{id}`, `odoo://task/{id}/timesheets`
- Инструмент `post_comment` для комментариев и внутренних заметок
- Поле `allocated_hours` в `update_task`
- Resource `odoo://project/{id}/tags` и инструмент `search_tags`
- Dockerfile для контейнерного запуска MCP-сервера
- 25 unit-тестов для mapper и config (без обращений к продакшену)

### Changed

- ADR-007: отказ от универсального `execute` tool в пользу
  специализированных инструментов
- ADR-008: masked mode с категорийной анонимизацией данных

### Fixed

- Удалён неиспользуемый import `os` в `test_config`
- Форматирование `test_mapper.py` приведено к стандарту ruff

## [0.1.0] - 2026-04-05

### Added

- MCP-сервер с 7 инструментами: list_tasks, get_task, create_task,
  update_task, change_task_stage, log_timesheet, get_timesheets
- Odoo CLI с интерактивным меню и браузерной авторизацией
- Anti-Corruption Layer (ACL) с тремя слоями: Transport, Protocol, Mapper
- Двухуровневая модель безопасности: restricted (по умолчанию) / full
- Фильтрация по проектам через ODOO_ALLOWED_PROJECTS
- Безопасное хранение session_id через системный keyring
- Поддержка Odoo 17 JSON-RPC протокола
- 11 доменных моделей (Pydantic v2)
- 5 архитектурных решений (ADR)
- Справочник из 9 Odoo JSON-RPC эндпоинтов

[0.3.0]: https://github.com/daniilpet/mcp-odoo-jsonrpc/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/daniilpet/mcp-odoo-jsonrpc/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/daniilpet/mcp-odoo-jsonrpc/releases/tag/v0.1.0
