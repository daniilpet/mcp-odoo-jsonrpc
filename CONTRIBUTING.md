# Contributing

MCP-сервер и CLI для управления задачами и трудозатратами
в Odoo ERP через JSON-RPC протокол.

## Scope

Текущий scope: **проектные задачи + трудозатраты** для Odoo 17.
Другие модули Odoo (CRM, Sales, Inventory) пока не поддерживаются.

## Подготовка окружения

```bash
git clone https://github.com/daniilpet/mcp-odoo-jsonrpc.git
cd mcp-odoo-jsonrpc
pip install -e ".[dev]"
pre-commit install
playwright install chromium  # для браузерной авторизации
```

### Pre-commit hooks

Проект использует [pre-commit](https://pre-commit.com/) со следующими проверками:

| Hook | Назначение |
|------|-----------|
| `ruff` | Линтинг Python-кода |
| `ruff-format` | Автоформатирование |
| `commitizen` | Валидация формата коммитов |
| `detect-secrets` | Предотвращение коммита секретов |
| `check-yaml`, `check-toml` | Валидация конфигов |
| `end-of-file-fixer`, `trailing-whitespace` | Нормализация файлов |

## Git Flow

Проект следует модели ветвления [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/).

### Ветки

| Ветка | Назначение |
|-------|-----------|
| `main` | Только релизный код, каждый коммит — тег версии |
| `develop` | Интеграционная ветка, сюда вливаются feature-ветки |
| `feature/*` | Новая функциональность (от `develop`) |
| `fix/*` | Исправление багов (от `develop`) |
| `release/*` | Подготовка релиза (от `develop`, мержится в `main` и `develop`) |
| `hotfix/*` | Срочные исправления (от `main`, мержится в `main` и `develop`) |
| `docs/*` | Изменения документации (от `develop`) |

### Порядок работы

1. Создать ветку от `develop`:
   ```bash
   git checkout develop
   git checkout -b feature/my-feature
   ```
2. Реализовать изменения, убедиться что `ruff check src/` проходит
3. Запустить тесты: `pytest`
4. Отправить ветку и создать Pull Request в `develop`

## Коммиты

Формат [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <описание на русском языке>
```

Типы: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

Примеры:
```
feat(acl): добавить поддержку project.milestone
fix(mapper): обработать отсутствующий employee_id в timesheets
docs(adr): ADR-009 — стратегия кэширования сессий
```

## Архитектура

Проект следует DDD с паттерном Conformist + Anti-Corruption Layer:

```
ACL Transport (httpx) -> ACL Protocol (JSON-RPC) -> ACL Mapper -> Domain Models
                                                                        |
                                                            MCP Server / CLI
```

Подробнее: [Context Map](docs/architecture/context-map.md) |
[Domain Model](docs/architecture/domain-model.md)

## Добавление нового эндпоинта Odoo

1. Перехватить запрос/ответ через Odoo DevTools или `dev/capture.py`
2. Задокументировать в `docs/api/odoo-jsonrpc-reference.md`
3. Добавить спецификации в `acl/protocol.py`
4. Добавить маппер в `acl/mapper.py`
5. При необходимости — доменную модель в `domain/models.py`
6. Добавить MCP tool в `server.py` и CLI команду в `cli.py`
7. Написать тесты

## Тестирование

```bash
pytest                    # все тесты
pytest tests/unit/        # только unit-тесты
ruff check src/           # линтинг
```

Тесты не должны обращаться к реальному инстансу Odoo.

## Безопасность

- Не логировать и не выводить значения `session_id`
- Соблюдать `TrustMode.RESTRICTED` — restricted-спецификации
  не должны запрашивать чувствительные поля
- Новые инструменты обязаны поддерживать оба режима (restricted / full)
- См. [ADR-005](docs/adr/005-security-model.md)

## Code of Conduct

См. [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
