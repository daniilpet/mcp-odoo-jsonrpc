# Доменная модель

## 1 Принципы

Доменная модель MCP-сервера — это **чистые объекты**, изолированные
от Odoo через Anti-Corruption Layer. Они не содержат:

- ORM-команд (`[4, id]`, `[6, 0, []]`)
- Odoo-специфичных значений (`false` вместо `None`)
- Вложенных specification-структур
- Контекста пользователя (`uid`, `company_ids`)

Трансляция Odoo-записей в доменные объекты и обратно —
ответственность ACL Domain Translation Layer.

---

## 2 Доменные объекты

### 2.1 Task (Задача)

Центральный объект модели. Агрегирует трудозатраты, сообщения, вложения.

| Поле               | Тип                | Источник Odoo             | Описание                          |
|--------------------|--------------------|---------------------------|-----------------------------------|
| `id`               | `int`              | `id`                      | Уникальный идентификатор          |
| `name`             | `str`              | `name`                    | Название задачи                   |
| `description`      | `str \| None`      | `description`             | Описание (HTML)                   |
| `state`            | `TaskState`        | `state`                   | Логический статус                 |
| `priority`         | `TaskPriority`     | `priority`                | Приоритет                         |
| `stage`            | `Stage`            | `stage_id`                | Текущая стадия (Kanban-колонка)   |
| `project`          | `Project`          | `project_id`              | Проект                            |
| `parent`           | `TaskRef \| None`  | `parent_id`               | Родительская задача (эпик)        |
| `assignees`        | `list[User]`       | `user_ids`                | Исполнители                       |
| `partner`          | `Partner \| None`  | `partner_id`              | Заказчик / контактное лицо        |
| `tags`             | `list[Tag]`        | `tag_ids`                 | Теги                              |
| `milestone`        | `Milestone \| None`| `milestone_id`            | Веха                              |
| `deadline`         | `date \| None`     | `date_deadline`           | Крайний срок                      |
| `is_closed`        | `bool`             | `is_closed`               | Задача закрыта                    |
| `allocated_hours`  | `float`            | `allocated_hours`         | Запланировано часов               |
| `effective_hours`  | `float`            | `effective_hours`         | Фактически затрачено              |
| `remaining_hours`  | `float`            | `remaining_hours`         | Осталось часов                    |
| `progress`         | `float`            | `progress`                | Прогресс (0.0 — 1.0)             |
| `subtask_count`    | `int`              | `subtask_count`           | Количество подзадач               |
| `closed_subtask_count` | `int`          | `closed_subtask_count`    | Закрытых подзадач                 |
| `timesheets`       | `list[Timesheet]`  | `timesheet_ids`           | Трудозатраты (только в get_task)  |
| `messages`         | `list[Message]`    | `/mail/thread/messages`   | Обсуждения (только в get_task)    |
| `attachments`      | `list[Attachment]`  | `/mail/thread/data`       | Вложения (только в get_task)      |
| `duration_tracking`| `dict[int, int]`   | `duration_tracking`       | Секунды по стадиям {stage_id: s}  |

#### TaskState (enum)

| Значение       | Odoo            | Описание     |
|----------------|-----------------|--------------|
| `IN_PROGRESS`  | `01_in_progress`| В работе     |
| `DONE`         | `1_done`        | Завершена    |

> Неизвестные значения `state` от Odoo транслируются как строка
> с логированием предупреждения. Enum расширяется по мере обнаружения.

#### TaskPriority (enum)

| Значение  | Odoo  | Описание |
|-----------|-------|----------|
| `NORMAL`  | `"0"` | Обычный  |
| `URGENT`  | `"1"` | Срочный  |

---

### 2.2 TaskRef (Ссылка на задачу)

Компактная ссылка для parent_id и зависимостей. Не загружает полный объект.

| Поле   | Тип    | Источник Odoo    | Описание            |
|--------|--------|------------------|---------------------|
| `id`   | `int`  | `id`             | ID задачи           |
| `name` | `str`  | `display_name`   | Название            |

---

### 2.3 Project (Проект)

| Поле   | Тип    | Источник Odoo    | Описание            |
|--------|--------|------------------|---------------------|
| `id`   | `int`  | `id`             | ID проекта          |
| `name` | `str`  | `display_name`   | Название проекта    |

---

### 2.4 Stage (Стадия)

| Поле     | Тип    | Источник Odoo    | Описание                            |
|----------|--------|------------------|-------------------------------------|
| `id`     | `int`  | `id`             | ID стадии                           |
| `name`   | `str`  | `display_name`   | Название (Новое, В разработке, ...) |
| `folded` | `bool` | `fold`           | Свёрнута в Kanban                   |

---

### 2.5 User (Пользователь)

| Поле   | Тип    | Источник Odoo    | Описание              |
|--------|--------|------------------|-----------------------|
| `id`   | `int`  | `id`             | ID пользователя       |
| `name` | `str`  | `display_name`   | Отображаемое имя      |

---

### 2.6 Partner (Контрагент)

| Поле   | Тип    | Источник Odoo    | Описание              |
|--------|--------|------------------|-----------------------|
| `id`   | `int`  | `id`             | ID партнёра           |
| `name` | `str`  | `display_name`   | Название организации  |

---

### 2.7 Tag (Тег)

| Поле    | Тип    | Источник Odoo    | Описание      |
|---------|--------|------------------|---------------|
| `id`    | `int`  | `id`             | ID тега       |
| `name`  | `str`  | `display_name`   | Название      |
| `color` | `int`  | `color`          | Цвет (0-11)   |

---

### 2.8 Milestone (Веха)

| Поле   | Тип    | Источник Odoo    | Описание      |
|--------|--------|------------------|---------------|
| `id`   | `int`  | `id`             | ID вехи       |
| `name` | `str`  | `display_name`   | Название      |

---

### 2.9 Timesheet (Трудозатраты)

| Поле          | Тип            | Источник Odoo    | Описание                          |
|---------------|----------------|------------------|-----------------------------------|
| `id`          | `int \| None`  | `id`             | ID (None для новых, до сохранения)|
| `date`        | `date`         | `date`           | Дата работы                       |
| `employee`    | `User`         | `employee_id`    | Сотрудник                         |
| `description` | `str`          | `name`           | Описание работы                   |
| `hours`       | `float`        | `unit_amount`    | Затраченное время в часах         |
| `readonly`    | `bool`         | `readonly_timesheet` | Защита от редактирования     |

#### Трансляция в X2M-команды (ACL → Odoo)

| Операция           | Доменный вызов                | X2M-команда                          |
|--------------------|-------------------------------|--------------------------------------|
| Создание           | `Timesheet(id=None, ...)`     | `[0, "virtual_N", {values}]`        |
| Обновление         | `Timesheet(id=40, ...)`       | `[1, 40, {changed_values}]`         |
| Удаление           | удаление по id                | `[2, 40]`                            |

---

### 2.10 Message (Сообщение)

| Поле             | Тип            | Источник Odoo        | Описание                      |
|------------------|----------------|----------------------|-------------------------------|
| `id`             | `int`          | `id`                 | ID сообщения                  |
| `author`         | `User`         | `author` + `res.partner` | Автор                    |
| `body`           | `str`          | `body`               | Содержимое (HTML)             |
| `date`           | `datetime`     | `date`               | Дата и время                  |
| `type`           | `MessageType`  | `message_type` + флаги | Тип сообщения              |
| `tracking`       | `list[FieldChange]` | `trackingValues` | История изменений полей   |

#### MessageType (enum)

| Значение       | Odoo message_type | is_note | is_discussion | Описание              |
|----------------|-------------------|---------|---------------|-----------------------|
| `NOTIFICATION` | `notification`    | true    | false         | Автоуведомление       |
| `COMMENT`      | `comment`         | false   | true          | Комментарий           |
| `NOTE`         | `comment`         | true    | false         | Внутренняя заметка    |

#### FieldChange (изменение поля)

| Поле        | Тип    | Источник Odoo         | Описание          |
|-------------|--------|-----------------------|-------------------|
| `field`     | `str`  | `changedField`        | Название поля (UI)|
| `field_name`| `str`  | `fieldName`           | Техническое имя   |
| `old_value` | `str`  | `oldValue.value`      | Старое значение   |
| `new_value` | `str`  | `newValue.value`      | Новое значение    |

---

### 2.11 Attachment (Вложение)

| Поле          | Тип    | Источник Odoo    | Описание                   |
|---------------|--------|------------------|-----------------------------|
| `id`          | `int`  | `id`             | ID вложения                 |
| `name`        | `str`  | `name`           | Имя файла                   |
| `mimetype`    | `str`  | `mimetype`       | MIME-тип                     |
| `size`        | `int`  | `file_size`      | Размер в байтах              |
| `access_token`| `str`  | `access_token`   | Токен для скачивания         |

#### URL для скачивания

```
{ODOO_BASE_URL}/web/content/{id}?access_token={access_token}
```

---

## 3 Карта трансляции ACL

### 3.1 Odoo → Domain (чтение)

```
Odoo record                    Domain object
─────────────────────────────  ──────────────────────
false                      →   None
{"id": N, "display_name": S} → ValueObject(id=N, name=S)
"01_in_progress"           →   TaskState.IN_PROGRESS
"1_done"                   →   TaskState.DONE
"0"                        →   TaskPriority.NORMAL
"1"                        →   TaskPriority.URGENT
"2026-03-31"               →   date(2026, 3, 31)
"2026-04-04 20:35:09"      →   datetime(2026, 4, 4, 20, 35, 9)
[{...}, {...}]             →   list[ValueObject]
```

### 3.2 Domain → Odoo (запись)

```
Domain value                   Odoo format
─────────────────────────────  ──────────────────────
None                       →   false
TaskState.IN_PROGRESS      →   "01_in_progress"
date(2026, 3, 31)          →   "2026-03-31"
User(id=33)                →   33  (int, в args)
User(id=33)                →   [4, 33]  (link, в Many2many)
Timesheet(id=None, ...)    →   [0, "virtual_N", {values}]
Timesheet(id=40, ...)      →   [1, 40, {changed_values}]
```

---

## 4 Маппинг инструментов на доменные объекты

### 4.1 list_tasks

**Вход**: фильтры (TBD)
**Выход**: `list[Task]` (без timesheets, messages, attachments)

Поля Task заполняются из `web_search_read`. Вложенные коллекции
(timesheets, messages, attachments) — пустые, загружаются только в `get_task`.

### 4.2 get_task

**Вход**: `task_id: int`
**Выход**: `Task` (полный, с timesheets, messages, attachments)

Три HTTP-запроса к Odoo:
1. `project.task/web_save` с полной specification (включая timesheet_ids)
2. `/mail/thread/messages` для сообщений
3. `/mail/thread/data` для вложений

Результаты агрегируются в один объект Task.

### 4.3 create_task

**Вход**: `name: str`, `project_id: int`, опционально description, assignee_ids, и пр.
**Выход**: `Task` (созданная задача)

### 4.4 update_task

**Вход**: `task_id: int`, изменяемые поля
**Выход**: `Task` (обновлённая задача)

### 4.5 change_task_stage

**Вход**: `task_id: int`, `stage_id: int`
**Выход**: `Task` (задача с новой стадией)

Перед сменой стадии ACL может запросить `project.task.type/search_read`
для валидации допустимости перехода.

### 4.6 log_timesheet

**Вход**: `task_id: int`, `hours: float`, `description: str`, опционально `date: date`
**Выход**: `Task` (с обновлёнными трудозатратами)

ACL транслирует в `web_save` с X2M-командой `[0, virtual_id, values]`.

### 4.7 get_timesheets

**Вход**: `task_id: int`
**Выход**: `list[Timesheet]` + агрегаты (effective_hours, remaining_hours, progress)

Реализуется через `web_search_read` или `web_save` с specification
содержащей `timesheet_ids`.
