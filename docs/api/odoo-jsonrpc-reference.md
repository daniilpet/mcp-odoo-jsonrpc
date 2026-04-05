# Справочник Odoo JSON-RPC эндпоинтов

## 1 Общие сведения

**Версия Odoo**: 17 (подтверждено).

Odoo не предоставляет публичного REST/GraphQL API. Взаимодействие с системой
осуществляется через внутренний JSON-RPC протокол, используемый веб-клиентом.

Все запросы — `POST`, `Content-Type: application/json`.

> **Odoo 17 vs 16**: Odoo 17 использует `specification` (dict) для описания
> формы ответа вместо `fields` (list) в Odoo <= 16. Все примеры в данном
> документе соответствуют протоколу Odoo 17.

### 1.1 Базовый формат запроса

```json
{
  "id": <int>,
  "jsonrpc": "2.0",
  "method": "call",
  "params": { ... }
}
```

### 1.2 Базовый формат ответа

```json
{
  "jsonrpc": "2.0",
  "id": <int>,
  "result": { ... }
}
```

### 1.3 Аутентификация

Авторизация выполняется через cookie `session_id`.

| Параметр       | Значение                        |
|----------------|---------------------------------|
| Имя cookie     | `session_id`                    |
| Домен          | домен инстанса Odoo             |
| Флаги          | `HttpOnly`, привязка к домену   |
| Время жизни    | определяется сервером Odoo      |

### 1.4 Контекст пользователя

Большинство запросов требуют передачи контекста в `params.kwargs.context`:

```json
{
  "lang": "ru_RU",
  "tz": "Europe/Moscow",
  "uid": <int>,
  "allowed_company_ids": [<int>]
}
```

Значения `uid` и `allowed_company_ids` специфичны для конкретного пользователя
и настраиваются через переменные окружения.

---

## 2 Эндпоинты

### 2.1 Получение информации о пользователе

**URL**: `/web/dataset/call_kw/res.users/search_read`

**Назначение**: проверка валидности сессии и получение данных текущего пользователя.

#### Запрос

```json
{
  "id": 0,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "res.users",
    "method": "search_read",
    "args": [],
    "kwargs": {
      "domain": [["id", "=", 33]],
      "fields": ["is_redirect_home"],
      "context": {
        "lang": "ru_RU",
        "tz": "Europe/Moscow",
        "uid": 33,
        "allowed_company_ids": [4]
      }
    }
  }
}
```

#### Ответ

```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": [
    {
      "id": 33,
      "is_redirect_home": false
    }
  ]
}
```

---

### 2.2 Список задач пользователя

**URL**: `/web/dataset/call_kw/project.task/web_search_read`

**Назначение**: получение списка задач с пагинацией и фильтрацией.

#### Ключевые параметры kwargs

| Параметр        | Тип    | Описание                                      |
|-----------------|--------|-----------------------------------------------|
| `specification` | object | Определяет возвращаемые поля и вложенности    |
| `domain`        | array  | Фильтр в формате Odoo domain                  |
| `offset`        | int    | Смещение для пагинации                        |
| `limit`         | int    | Максимум записей (по умолчанию 80)            |
| `order`         | string | Сортировка                                    |
| `count_limit`   | int    | Лимит подсчёта общего количества              |

#### Формат domain-фильтра

```
["&", ["user_ids", "in", <uid>], ["personal_stage_type_ids", "=", <stage_id>]]
```

#### Запрос

```json
{
  "id": 7,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "project.task",
    "method": "web_search_read",
    "args": [],
    "kwargs": {
      "specification": {
        "stage_id": { "fields": { "display_name": {} } },
        "state": {},
        "name": {},
        "parent_id": { "fields": { "display_name": {} } },
        "project_id": { "fields": { "display_name": {} } },
        "partner_id": { "fields": { "display_name": {} } },
        "milestone_id": { "fields": { "display_name": {} } },
        "tag_ids": { "fields": { "display_name": {}, "color": {} } },
        "date_deadline": {},
        "priority": {},
        "user_ids": {
          "fields": { "display_name": {} },
          "context": { "active_test": false }
        },
        "subtask_count": {},
        "closed_subtask_count": {},
        "allocated_hours": {},
        "remaining_hours": {},
        "progress": {},
        "color": {},
        "activity_state": {},
        "activity_summary": {},
        "task_properties": {}
      },
      "offset": 0,
      "order": "priority DESC, sequence ASC, state ASC, date_deadline ASC, id DESC",
      "limit": 80,
      "context": {
        "lang": "ru_RU",
        "tz": "Europe/Moscow",
        "uid": 33,
        "allowed_company_ids": [4],
        "all_task": 0,
        "default_user_ids": [[4, 33]],
        "project_kanban": true,
        "default_personal_stage_type_id": 594
      },
      "count_limit": 10001,
      "domain": [
        "&",
        ["user_ids", "in", 33],
        ["personal_stage_type_ids", "=", 594]
      ]
    }
  }
}
```

#### Ответ (фрагмент)

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "length": 18,
    "records": [
      {
        "id": 763,
        "stage_id": { "id": 902, "display_name": "Новое" },
        "state": "01_in_progress",
        "name": "Безопасность и разграничение доступа",
        "parent_id": { "id": 723, "display_name": "[ЭПИК] Example Project" },
        "project_id": { "id": 99, "display_name": "Example Project" },
        "partner_id": false,
        "milestone_id": false,
        "tag_ids": [],
        "date_deadline": false,
        "priority": "0",
        "user_ids": [
          { "id": 33, "display_name": "Ivan" }
        ],
        "subtask_count": 0,
        "closed_subtask_count": 0,
        "allocated_hours": 0.0,
        "remaining_hours": 0.0,
        "progress": 0.0
      }
    ]
  }
}
```

#### Известные значения полей

| Поле       | Значения                                                      |
|------------|---------------------------------------------------------------|
| `state`    | `01_in_progress` — другие значения требуют исследования       |
| `priority` | `"0"` — обычный, `"1"` — срочный                             |

#### Стадии задач (project.task.type)

Стадии специфичны для каждого проекта. Пример для проекта R&amp;D (id=99):

| ID  | Название        | Описание                      |
|-----|-----------------|-------------------------------|
| 902 | Новое           | Начальная стадия              |
| 903 | В разработке    | Задача в работе               |
| 905 | Тестирование    | На проверке / тестировании    |
| 904 | Готов к приемке  | Ожидает приёмки заказчиком    |
| 921 | Закрыто         | Задача завершена              |
| 922 | Отложено        | Задача приостановлена         |

> **Важно**: ID стадий различаются между инстансами Odoo.
> MCP-сервер должен получать стадии динамически через
> `project.task.type/search_read`.

---

### 2.3 Создание задачи

**URL**: `/web/dataset/call_kw/project.task/web_save`

**Назначение**: создание новой задачи в проекте.

#### Запрос

Первый аргумент `args[0]` — пустой массив `[]` (создание новой записи).

```json
{
  "id": 19,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "project.task",
    "method": "web_save",
    "args": [
      [],
      {
        "display_name": "Название задачи",
        "project_id": 99,
        "user_ids": [[4, 33]],
        "company_id": false,
        "description": false
      }
    ],
    "kwargs": {
      "context": {
        "lang": "ru_RU",
        "tz": "Europe/Moscow",
        "uid": 33,
        "allowed_company_ids": [4],
        "default_user_ids": [[4, 33]],
        "default_personal_stage_type_id": 594
      },
      "specification": {}
    }
  }
}
```

#### Ответ

```json
{
  "jsonrpc": "2.0",
  "id": 19,
  "result": [{ "id": 1228 }]
}
```

#### Семантика команд Many2many (user_ids, tag_ids)

| Команда      | Формат           | Описание                              |
|--------------|------------------|---------------------------------------|
| `[4, id]`    | Link             | Связать существующую запись           |
| `[3, id]`    | Unlink           | Отвязать запись                       |
| `[6, 0, []]` | Replace          | Заменить все связи                    |

---

### 2.4 Обновление задачи

**URL**: `/web/dataset/call_kw/project.task/web_save`

**Назначение**: обновление существующей задачи.

#### Запрос

Первый аргумент `args[0]` — массив с ID задачи `[1228]`.

```json
{
  "id": 32,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "project.task",
    "method": "web_save",
    "args": [
      [1228],
      {
        "name": "[ЗАДАЧА 1228] Новое название задачи"
      }
    ],
    "kwargs": {
      "context": {
        "lang": "ru_RU",
        "tz": "Europe/Moscow",
        "uid": 33,
        "allowed_company_ids": [4],
        "default_user_ids": [[4, 33]]
      },
      "specification": {
        "stage_id": { "fields": { "display_name": {} } },
        "state": {},
        "name": {},
        "project_id": { "fields": { "display_name": {} } },
        "user_ids": {
          "fields": { "display_name": {} },
          "context": { "active_test": false }
        },
        "description": {}
      }
    }
  }
}
```

#### Ответ

Возвращает полный объект задачи с полями, указанными в `specification`.

---

### 2.5 Сообщения и история задачи

**URL**: `/mail/thread/messages`

**Назначение**: получение обсуждений, комментариев и истории изменений задачи.

#### Запрос

```json
{
  "id": 33,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "thread_id": 1228,
    "thread_model": "project.task",
    "limit": 30,
    "after": 0
  }
}
```

| Параметр       | Тип    | Описание                                   |
|----------------|--------|---------------------------------------------|
| `thread_id`    | int    | ID задачи                                   |
| `thread_model` | string | Всегда `"project.task"`                     |
| `limit`        | int    | Количество сообщений                        |
| `after`        | int    | ID сообщения для пагинации (0 — с начала)   |

#### Ответ (структура)

```json
{
  "jsonrpc": "2.0",
  "id": 33,
  "result": {
    "data": {
      "mail.message": [
        {
          "id": 12806,
          "author": { "id": 176, "type": "partner" },
          "body": "",
          "date": "2026-04-04 20:35:09",
          "is_discussion": false,
          "is_note": true,
          "message_type": "notification",
          "trackingValues": [
            {
              "changedField": "Заголовок",
              "fieldName": "name",
              "fieldType": "char",
              "newValue": { "value": "Новое значение" },
              "oldValue": { "value": "Старое значение" }
            }
          ]
        }
      ],
      "res.partner": [
        {
          "id": 176,
          "name": "Ivan Ivanov",
          "userId": 33
        }
      ]
    },
    "messages": [12806]
  }
}
```

#### Типы сообщений

| `message_type`  | `is_note` | `is_discussion` | Назначение                  |
|-----------------|-----------|------------------|-----------------------------|
| `notification`  | true      | false            | Автоматические уведомления  |
| `comment`       | false     | true             | Комментарии пользователей   |
| `comment`       | true      | false            | Внутренние заметки          |

---

### 2.6 Получение доступных стадий проекта

**URL**: `/web/dataset/call_kw/project.task.type/search_read`

**Назначение**: получение списка стадий (Kanban-колонок) для проекта.
Необходимо для валидации перед сменой стадии задачи.

#### Запрос

```json
{
  "id": 33,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "project.task.type",
    "method": "search_read",
    "args": [],
    "kwargs": {
      "domain": ["|", ["id", "=", 905], ["project_ids", "=", 99]],
      "fields": ["display_name", "fold"],
      "context": {
        "lang": "ru_RU",
        "tz": "Europe/Moscow",
        "uid": 33,
        "allowed_company_ids": [4]
      }
    }
  }
}
```

**Семантика domain-фильтра**:
- `["project_ids", "=", <project_id>]` — стадии, привязанные к проекту
- `["id", "=", <stage_id>]` — конкретная стадия (для включения текущей)
- Оператор `"|"` — логическое ИЛИ

#### Ответ

```json
{
  "jsonrpc": "2.0",
  "id": 33,
  "result": [
    { "id": 902, "display_name": "Новое", "fold": false },
    { "id": 903, "display_name": "В разработке", "fold": false },
    { "id": 905, "display_name": "Тестирование", "fold": false },
    { "id": 904, "display_name": "Готов к приемке", "fold": false },
    { "id": 921, "display_name": "Закрыто", "fold": false },
    { "id": 922, "display_name": "Отложено", "fold": false }
  ]
}
```

#### Поля стадии

| Поле           | Тип    | Описание                                        |
|----------------|--------|-------------------------------------------------|
| `id`           | int    | ID стадии                                       |
| `display_name` | string | Отображаемое название                           |
| `fold`         | bool   | Свёрнута ли колонка в Kanban (архивные стадии)  |

---

### 2.7 Смена стадии задачи

**URL**: `/web/dataset/call_kw/project.task/web_save`

**Назначение**: перемещение задачи между стадиями (Kanban-колонками).

Смена стадии — это `web_save` с полем `stage_id`. Odoo веб-клиент
перед сохранением выполняет `onchange` для валидации, но для
программного вызова достаточно `web_save`.

#### Протокол смены стадии (как делает веб-клиент)

```
1. onchange    — валидация (необязательно для MCP)
2. web_save    — сохранение нового stage_id
```

#### Запрос

```json
{
  "id": 35,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "project.task",
    "method": "web_save",
    "args": [
      [1203],
      {
        "stage_id": 905,
        "state": "01_in_progress"
      }
    ],
    "kwargs": {
      "context": {
        "lang": "ru_RU",
        "tz": "Europe/Moscow",
        "uid": 33,
        "allowed_company_ids": [4],
        "default_user_ids": [[4, 33]]
      },
      "specification": {
        "stage_id": { "fields": { "display_name": {} } },
        "state": {},
        "name": {},
        "project_id": { "fields": { "display_name": {} } }
      }
    }
  }
}
```

#### Ответ (фрагмент)

```json
{
  "jsonrpc": "2.0",
  "id": 35,
  "result": [
    {
      "id": 1203,
      "stage_id": { "id": 905, "display_name": "Тестирование" },
      "state": "01_in_progress",
      "name": "[ЗАДАЧА 1203] Функциональные предложения по доработке 2",
      "duration_tracking": {
        "902": 261659,
        "903": 196593,
        "905": 0
      }
    }
  ]
}
```

#### Поле duration_tracking

Содержит время пребывания задачи в каждой стадии (в секундах).
Ключ — ID стадии, значение — количество секунд.

```json
{
  "902": 261659,
  "903": 196593,
  "905": 0
}
```

---

### 2.8 Трудозатраты (Timesheets)

#### Архитектурное открытие

Трудозатраты в Odoo 17 **не имеют отдельного CRUD-эндпоинта**.
Они создаются, читаются и обновляются исключительно через родительскую
запись `project.task/web_save` с использованием X2M-команд в поле
`timesheet_ids`.

Это означает:
- `log_timesheet` = `web_save` задачи с X2M-командой CREATE в `timesheet_ids`
- `get_timesheets` = `web_save` или `web_search_read` задачи с `timesheet_ids` в specification

#### Чтение трудозатрат (specification)

```json
{
  "timesheet_ids": {
    "fields": {
      "readonly_timesheet": {},
      "date": {},
      "user_id": { "fields": {} },
      "employee_id": { "fields": { "display_name": {} } },
      "name": {},
      "unit_amount": {},
      "project_id": { "fields": {} },
      "task_id": { "fields": {} },
      "company_id": { "fields": {} }
    },
    "limit": 40,
    "order": "date ASC"
  },
  "effective_hours": {},
  "subtask_effective_hours": {},
  "total_hours_spent": {},
  "remaining_hours": {}
}
```

#### Создание трудозатрат (X2M-команда CREATE)

**URL**: `/web/dataset/call_kw/project.task/web_save`

Трудозатраты создаются через X2M-команду `[0, virtual_id, values]`
в поле `timesheet_ids` при сохранении задачи.

```json
{
  "id": 36,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "project.task",
    "method": "web_save",
    "args": [
      [1205],
      {
        "timesheet_ids": [
          [0, "virtual_597", {
            "date": "2026-03-31",
            "user_id": 33,
            "employee_id": 89,
            "name": "Тестирование Mayan EDMS на стенде заказчика",
            "unit_amount": 0.25,
            "project_id": 99,
            "task_id": 1205
          }],
          [0, "virtual_599", {
            "date": "2026-03-31",
            "user_id": 33,
            "employee_id": 89,
            "name": "Настройка СЭД и конфигурация документов",
            "unit_amount": 0.25,
            "project_id": 99,
            "task_id": 1205
          }]
        ]
      }
    ],
    "kwargs": {
      "context": {
        "lang": "ru_RU",
        "tz": "Europe/Moscow",
        "uid": 33,
        "allowed_company_ids": [4],
        "default_project_id": 99
      },
      "specification": {
        "timesheet_ids": {
          "fields": {
            "date": {}, "employee_id": { "fields": { "display_name": {} } },
            "name": {}, "unit_amount": {}
          },
          "limit": 40, "order": "date ASC"
        },
        "effective_hours": {},
        "total_hours_spent": {},
        "remaining_hours": {}
      }
    }
  }
}
```

#### X2M-команды для timesheet_ids

| Команда                        | Формат                              | Описание                    |
|--------------------------------|-------------------------------------|-----------------------------|
| CREATE                         | `[0, "virtual_NNN", {values}]`      | Создать новую запись        |
| UPDATE                         | `[1, real_id, {values}]`            | Обновить существующую       |
| DELETE                         | `[2, real_id]`                      | Удалить запись              |
| LINK                           | `[4, real_id]`                      | Связать существующую        |
| UNLINK ALL                     | `[5]`                               | Отвязать все                |
| REPLACE                        | `[6, 0, [id1, id2, ...]]`          | Заменить все связи          |

> **virtual_NNN** — клиентский временный ID. После сохранения сервер
> возвращает реальные ID в ответе.

#### Ответ (фрагмент)

```json
{
  "jsonrpc": "2.0",
  "id": 36,
  "result": [
    {
      "id": 1205,
      "timesheet_ids": [
        {
          "id": 45,
          "date": "2026-03-31",
          "employee_id": { "id": 89, "display_name": "Ivan" },
          "name": "Тестирование Mayan EDMS на стенде заказчика",
          "unit_amount": 0.25
        },
        {
          "id": 46,
          "date": "2026-03-31",
          "employee_id": { "id": 89, "display_name": "Ivan" },
          "name": "Настройка СЭД и конфигурация документов",
          "unit_amount": 0.25
        }
      ],
      "effective_hours": 0.5,
      "total_hours_spent": 0.5,
      "remaining_hours": 8.5
    }
  ]
}
```

#### Поля трудозатрат

| Поле                | Тип    | Описание                                  |
|---------------------|--------|-------------------------------------------|
| `id`                | int    | ID записи (реальный, после сохранения)    |
| `date`              | string | Дата (формат `YYYY-MM-DD`)               |
| `employee_id`       | object | Сотрудник                                 |
| `name`              | string | Описание работы (у команды: хеш коммита)  |
| `unit_amount`       | float  | Затраченное время в часах                 |
| `readonly_timesheet`| bool   | Защита от редактирования                  |

#### Агрегаты по задаче

| Поле                      | Описание                                     |
|---------------------------|----------------------------------------------|
| `effective_hours`         | Суммарные часы по задаче                     |
| `subtask_effective_hours` | Часы по подзадачам                           |
| `total_hours_spent`       | Общее время (задача + подзадачи)             |
| `remaining_hours`         | Осталось (allocated_hours - effective_hours)  |
| `allocated_hours`         | Запланировано часов                          |
| `progress`                | Прогресс (0.0 — 1.0, = effective/allocated)  |

---

### 2.9 Метаданные задачи (вложения, подписчики, активности)

**URL**: `/mail/thread/data`

**Назначение**: получение вложений, подписчиков, активностей и
предложенных получателей для задачи. Дополняет `/mail/thread/messages`.

#### Запрос

```json
{
  "id": 37,
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "request_list": [
      "activities",
      "attachments",
      "followers",
      "scheduledMessages",
      "suggestedRecipients"
    ],
    "thread_id": 1205,
    "thread_model": "project.task"
  }
}
```

#### Ответ (структура)

```json
{
  "jsonrpc": "2.0",
  "id": 37,
  "result": {
    "ir.attachment": [
      {
        "id": 2417,
        "name": "image.png",
        "mimetype": "image/png",
        "file_size": 107000,
        "access_token": "aa804d65-...",
        "checksum": "..."
      }
    ],
    "mail.followers": [
      {
        "id": 1234,
        "partner_id": { "id": 176, "display_name": "Ivan Ivanov" },
        "email": "user@example.com"
      }
    ],
    "activities": [],
    "scheduledMessages": [],
    "suggestedRecipients": [...]
  }
}
```

---

## 3 Известные знач��ния поля state

| Значение                | Описание              | Контекст                     |
|-------------------------|-----------------------|------------------------------|
| `01_in_progress`        | �� работе              | Задача активна               |
| `02_changes_requested`  | Запрошены изменения   | Возврат на доработку         |
| `03_approved`           | Одобрена              | Прошла проверку              |
| `04_cancelled`          | Отменена              | Отменена до завершения       |
| `04_waiting_normal`     | Ожидание              | Заблокирована / в очереди    |
| `1_done`                | Завершена             | Задача закрыта               |
| `1_canceled`            | Отменена (финал)      | Окончательная отмена         |

> Поле `state` связано с `stage_id`, но не тождественно ему:
> `stage_id` — Kanban-колонка, `state` — логический статус.

---

## 4 Сводная таблица эндпоинтов

| # | URL | Назначение | MCP-инструмент |
|---|-----|------------|----------------|
| 2.1 | `/web/dataset/call_kw/res.users/search_read` | Валидация сессии | (внутренний) |
| 2.2 | `/web/dataset/call_kw/project.task/web_search_read` | Список задач | `list_tasks` |
| 2.3 | `/web/dataset/call_kw/project.task/web_save` | Создание задачи | `create_task` |
| 2.4 | `/web/dataset/call_kw/project.task/web_save` | Обновление задачи | `update_task` |
| 2.5 | `/mail/thread/messages` | Сообщения задачи | `get_task` |
| 2.6 | `/web/dataset/call_kw/project.task.type/search_read` | Стадии проекта | `change_task_stage` |
| 2.7 | `/web/dataset/call_kw/project.task/web_save` | Смена стадии | `change_task_stage` |
| 2.8 | `/web/dataset/call_kw/project.task/web_save` | Трудозатраты (CRUD) | `log_timesheet`, `get_timesheets` |
| 2.9 | `/mail/thread/data` | Вложения, подписчики | `get_task` |

---

## 5 Особенности протокола

### 5.1 Нестабильность интерфейса

JSON-RPC эндпоинты Odoo являются **внутренним протоколом веб-клиента**,
а не публичным API. Это означает:

- Структура запросов может измениться при обновлении Odoo
- Поля в `specification` могут быть добавлены или удалены
- Формат ответов не гарантирован между версиями

### 5.2 Формат `false` вместо `null`

Odoo возвращает `false` вместо `null`/`None` для пустых значений:

```json
{ "partner_id": false, "milestone_id": false, "description": false }
```

### 5.3 Идентификатор запроса

Поле `id` в JSON-RPC запросе — произвольное целое число для корреляции
запрос-ответ. Сервер возвращает то же значение в ответе.
