# MCP Odoo JSON-RPC

[![CI](https://github.com/daniilpet/mcp-odoo-jsonrpc/actions/workflows/ci.yml/badge.svg)](https://github.com/daniilpet/mcp-odoo-jsonrpc/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)
[![Odoo 17](https://img.shields.io/badge/Odoo-17-blueviolet.svg)](https://www.odoo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Security: detect-secrets](https://img.shields.io/badge/security-detect--secrets-informational.svg)](https://github.com/Yelp/detect-secrets)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-fe5196.svg)](https://conventionalcommits.org)

> MCP-сервер и CLI для управления задачами и трудозатратами
> в Odoo ERP через JSON-RPC протокол.

---

## Что это?

Odoo не предоставляет публичного REST/GraphQL API. Этот инструмент
использует внутренний JSON-RPC протокол веб-клиента **Odoo 17** и
предоставляет два способа доступа:

- **`mcp-odoo-server`** — MCP-сервер для Claude Code и других AI-ассистентов
- **`mcp-odoo-cli`** — интерактивный терминальный клиент для человека

**Scope**: проектные задачи + трудозатраты (timesheets). Другие модули
Odoo (CRM, Sales, Inventory) пока не поддерживаются.

## Быстрый старт

### Установка

```bash
pip install mcp-odoo-jsonrpc
```

### Авторизация

```bash
mcp-odoo-cli login --url https://odoo.example.com
```

Откроется браузер — войдите в Odoo. Сессия сохранится автоматически
в системное хранилище (Windows Credential Manager / macOS Keychain / GNOME Keyring).

### CLI

```bash
mcp-odoo-cli
```

### MCP-сервер (для Claude Code)

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "mcp_odoo_jsonrpc"]
    }
  }
}
```

## Возможности

| Инструмент           | Описание                                     |
|----------------------|----------------------------------------------|
| `list_tasks`         | Получение списка задач пользователя          |
| `get_task`           | Детали задачи с обсуждениями и вложениями    |
| `create_task`        | Создание новой задачи в проекте              |
| `update_task`        | Обновление задачи (название, описание и пр.) |
| `change_task_stage`  | Смена стадии/статуса задачи                  |
| `log_timesheet`      | Списание трудозатрат по задаче               |
| `get_timesheets`     | Получение трудозатрат по задаче              |

## Безопасность

MCP-сервер работает в **restricted mode** по умолчанию — AI видит только
структурные данные без корпоративного контента:

| Режим        | Что видит AI                                    | Активация               |
|--------------|--------------------------------------------------|-------------------------|
| `restricted` | ID, стадия, часы, дедлайн. Без названий и текста | По умолчанию            |
| `full`       | Все данные: названия, описания, сообщения        | `ODOO_TRUST_MODE=full`  |

Дополнительные меры:

- **Фильтр проектов**: `ODOO_ALLOWED_PROJECTS=99,101` — ограничить видимые проекты
- **Secure credentials**: `session_id` хранится в системном keyring, не в plaintext
- **detect-secrets**: pre-commit hook предотвращает случайный коммит секретов
- **CLI**: всегда работает в full mode (пользователь смотрит в свой терминал)

Подробнее: [SECURITY.md](SECURITY.md) | [ADR-005: Модель безопасности](docs/adr/005-security-model.md)

## Конфигурация

### Через CLI (рекомендуется)

```bash
mcp-odoo-cli login --url https://odoo.example.com
```

### Через переменные окружения

| Переменная               | Обязательная | Описание                                      |
|--------------------------|--------------|-----------------------------------------------|
| `ODOO_BASE_URL`          | Да           | Базовый URL инстанса Odoo                     |
| `ODOO_SESSION_ID`        | Да           | Значение cookie `session_id`                  |
| `ODOO_UID`               | Да           | ID пользователя в Odoo                        |
| `ODOO_EMPLOYEE_ID`       | Нет          | ID сотрудника (по умолчанию = UID)            |
| `ODOO_COMPANY_IDS`       | Да           | ID компаний (через запятую)                   |
| `ODOO_TRUST_MODE`        | Нет          | `restricted` (по умолчанию) или `full`        |
| `ODOO_ALLOWED_PROJECTS`  | Нет          | Фильтр проектов (ID через запятую)            |
| `ODOO_LANG`              | Нет          | Язык (по умолчанию: `ru_RU`)                 |
| `ODOO_TZ`                | Нет          | Часовой пояс (по умолчанию: `Europe/Moscow`) |

См. [.env.example](.env.example)

## Архитектура

```
Odoo ERP (JSON-RPC)
     ↑
Anti-Corruption Layer
  ├── Transport   (httpx + session_id cookie)
  ├── Protocol    (JSON-RPC envelope, specifications)
  └── Mapper  (Odoo records ↔ Domain objects)
     ↑
Service Layer (OdooTaskService)
  ├── MCP Server  (строки для AI)
  └── CLI         (rich таблицы для человека)
```

**DDD-паттерн**: Conformist + Anti-Corruption Layer.
Подробнее: [Context Map](docs/architecture/context-map.md) | [Domain Model](docs/architecture/domain-model.md)

## Технологический стек

| Компонент     | Технология                |
|---------------|---------------------------|
| Язык          | Python 3.12+              |
| MCP SDK       | `mcp` v1.12+              |
| HTTP          | `httpx`                   |
| Модели        | `pydantic` v2             |
| TUI           | `rich`                    |
| Credentials   | `keyring`                 |
| Browser auth  | `playwright` (dev)        |
| Lint          | `ruff`                    |
| CI            | GitHub Actions            |
| Odoo          | 17                        |

## Документация

| Документ | Описание |
|----------|----------|
| [Context Map](docs/architecture/context-map.md) | Архитектура и DDD-паттерны |
| [Domain Model](docs/architecture/domain-model.md) | 11 доменных объектов |
| [JSON-RPC Reference](docs/api/odoo-jsonrpc-reference.md) | 9 задокументированных эндпоинтов |
| [ADR](docs/adr/README.md) | 6 архитектурных решений |
| [CONTRIBUTING](CONTRIBUTING.md) | Как внести вклад |
| [SECURITY](SECURITY.md) | Политика безопасности |

## Лицензия

[MIT](LICENSE)
