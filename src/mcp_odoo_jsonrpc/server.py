import re

from mcp.server.fastmcp import FastMCP

from mcp_odoo_jsonrpc.config import OdooConfig
from mcp_odoo_jsonrpc.domain.enums import WikiPageType
from mcp_odoo_jsonrpc.domain.models import Task, WikiPage
from mcp_odoo_jsonrpc.domain.sensitive import is_sensitive
from mcp_odoo_jsonrpc.service import OdooTaskService, OdooWikiService

mcp = FastMCP(
    "Odoo",
    instructions=(
        "MCP-сервер для Odoo ERP. "
        "Позволяет управлять задачами, трудозатратами и wiki-страницами. "
        "Wiki-контент с чувствительными данными (пароли, ключи) цензурируется автоматически."
    ),
)

_service: OdooTaskService | None = None
_wiki_service: OdooWikiService | None = None


def _get_service() -> OdooTaskService:
    global _service
    if _service is None:
        _service = OdooTaskService(OdooConfig.auto())
    return _service


def _get_wiki_service() -> OdooWikiService:
    global _wiki_service
    if _wiki_service is None:
        _wiki_service = OdooWikiService(OdooConfig.auto())
    return _wiki_service


_STRIP_HTML_RE = re.compile(r"<[^>]+>")


def _strip_html(html: str) -> str:
    return _STRIP_HTML_RE.sub("", html).strip()


def _format_wiki_page(page: WikiPage, restricted: bool, sensitive_filter: bool) -> str:
    # Матрица состояний — ADR-009
    # restricted=True  → метаданные, без тела (строки 1-2)
    # restricted=False, sensitive=False → всё (строка 3)
    # restricted=False, sensitive=True  → метаданные + причина цензуры (строка 4)

    sensitive = sensitive_filter and is_sensitive(page.name, page.content)

    lines = [f"# {page.name}"]
    lines.append(f"ID: {page.id} | Тип: {page.type.value}")
    if page.parent_name:
        lines.append(f"Категория: {page.parent_name}")
    if page.write_date:
        lines.append(f"Изменено: {page.write_date:%Y-%m-%d %H:%M}")
    if page.content_uid:
        lines.append(f"Автор: {page.content_uid.name}")
    lines.append(f"Ссылка: odoo://wiki/{page.id}")

    if restricted:
        lines.append("\nВозможно, здесь об этом написано.")
        return "\n".join(lines)

    if sensitive:
        lines.append(
            "\nСодержимое скрыто: обнаружены чувствительные данные "
            "(пароли, ключи доступа или аналогичная информация)."
        )
        return "\n".join(lines)

    if page.content:
        lines.append(f"\n## Содержимое\n{_strip_html(page.content)}")

    if page.history:
        lines.append("\n## История изменений")
        for h in page.history:
            author = h.author.name if h.author else "—"
            date_str = f"{h.create_date:%Y-%m-%d %H:%M}" if h.create_date else "—"
            summary = h.summary or "без описания"
            lines.append(f"- [{date_str}] {author}: {summary}")

    return "\n".join(lines)


def _format_wiki_list(pages: list[WikiPage], restricted: bool) -> str:
    if not pages:
        return "Wiki-страниц не найдено."

    lines = [f"Wiki ({len(pages)}):"]
    for p in pages:
        icon = "📁" if p.type == WikiPageType.CATEGORY else "📄"
        date_str = f" | {p.write_date:%Y-%m-%d}" if p.write_date else ""
        parent = f" | {p.parent_name}" if p.parent_name else ""
        lines.append(f"- {icon} ID {p.id} | {p.name}{parent}{date_str}")
    return "\n".join(lines)


def _format_task(task: Task, restricted: bool) -> str:
    if restricted:
        lines = [
            f"ID: {task.id}",
            f"Стадия: {task.stage.name} | Статус: {task.state.name} "
            f"| Приоритет: {task.priority.name}",
        ]
        if task.deadline:
            lines.append(f"Дедлайн: {task.deadline}")
        if task.allocated_hours > 0:
            lines.append(
                f"Часы: {task.effective_hours:.1f}/{task.allocated_hours:.1f} "
                f"(осталось {task.remaining_hours:.1f}, прогресс {task.progress:.0%})"
            )
        if task.timesheets:
            lines.append(f"\nТрудозатраты: {len(task.timesheets)} записей")
            for ts in task.timesheets:
                lines.append(f"- {ts.date} | {ts.hours:.2f}ч")
        return "\n".join(lines)

    lines = [
        f"# {task.name}",
        f"ID: {task.id} | Проект: {task.project.name} | Стадия: {task.stage.name}",
        f"Статус: {task.state.name} | Приоритет: {task.priority.name}",
    ]
    if task.parent:
        lines.append(f"Родитель: {task.parent.name}")
    if task.assignees:
        lines.append(f"Исполнители: {', '.join(u.name for u in task.assignees)}")
    if task.partner:
        lines.append(f"Заказчик: {task.partner.name}")
    if task.deadline:
        lines.append(f"Дедлайн: {task.deadline}")
    if task.tags:
        lines.append(f"Теги: {', '.join(t.name for t in task.tags)}")
    if task.allocated_hours > 0:
        lines.append(
            f"Часы: {task.effective_hours:.1f}/{task.allocated_hours:.1f} "
            f"(осталось {task.remaining_hours:.1f}, прогресс {task.progress:.0%})"
        )
    if task.subtask_count > 0:
        lines.append(f"Подзадачи: {task.closed_subtask_count}/{task.subtask_count}")
    if task.description:
        lines.append(f"\n## Описание\n{task.description}")
    if task.subtasks:
        lines.append("\n## Подзадачи")
        for st in task.subtasks:
            assignee = ", ".join(u.name for u in st.assignees) if st.assignees else ""
            dl = f" | Дедлайн: {st.deadline}" if st.deadline else ""
            lines.append(
                f"- [{st.id}] {st.name} "
                f"| {st.stage.name} "
                f"| {st.priority.name}{dl}" + (f" | {assignee}" if assignee else "")
            )
    if task.timesheets:
        lines.append("\n## Трудозатраты")
        for ts in task.timesheets:
            lines.append(f"- {ts.date} | {ts.employee.name} | {ts.hours:.2f}ч | {ts.description}")
    if task.messages:
        lines.append("\n## Обсуждения")
        for msg in task.messages:
            author = msg.author.name if msg.author else "Система"
            if msg.body:
                lines.append(f"- [{msg.date:%Y-%m-%d %H:%M}] {author}: {msg.body}")
            for change in msg.tracking:
                lines.append(
                    f"- [{msg.date:%Y-%m-%d %H:%M}] "
                    f"{change.field}: "
                    f"{change.old_value} → {change.new_value}"
                )
    if task.attachments:
        lines.append("\n## Вложения")
        for att in task.attachments:
            lines.append(f"- {att.name} ({att.mimetype}, {att.size} байт)")
    return "\n".join(lines)


# --- Resources (read-only) ---


@mcp.resource("odoo://projects")
async def resource_projects() -> str:
    """Список доступных проектов Odoo."""
    svc = _get_service()
    projects = await svc.list_projects()
    lines = [f"Проекты ({len(projects)}):"]
    for p in projects:
        lines.append(f"- ID {p.id} | {p.name} | {p.task_count} задач")
    return "\n".join(lines)


@mcp.resource("odoo://project/{project_id}/stages")
async def resource_project_stages(project_id: int) -> str:
    """Стадии (Kanban-колонки) проекта."""
    svc = _get_service()
    try:
        stages = await svc.get_task_stages(project_id)
    except PermissionError as e:
        return f"Ошибка доступа: {e}"
    except Exception as e:
        return f"Ошибка: проект {project_id} не найден или недоступен. {e}"
    if not stages:
        return f"Проект {project_id}: стадии не найдены."
    lines = [f"Стадии проекта {project_id}:"]
    for s in stages:
        fold = " (свёрнута)" if s.folded else ""
        lines.append(f"- ID {s.id} | {s.name}{fold}")
    return "\n".join(lines)


@mcp.resource("odoo://project/{project_id}/tags")
async def resource_project_tags(project_id: int) -> str:
    """Теги, доступные в проекте."""
    svc = _get_service()
    try:
        tags = await svc.search_tags(project_id=project_id)
    except PermissionError as e:
        return f"Ошибка доступа: {e}"
    except Exception as e:
        return f"Ошибка: {e}"
    if not tags:
        return f"Проект {project_id}: теги не найдены."
    lines = [f"Теги проекта {project_id}:"]
    for t in tags:
        lines.append(f"- ID {t.id} | {t.name} | цвет {t.color}")
    return "\n".join(lines)


@mcp.resource("odoo://task/{task_id}")
async def resource_task(task_id: int) -> str:
    """Данные задачи (read-only)."""
    svc = _get_service()
    try:
        task = await svc.get_task(task_id)
    except (ValueError, PermissionError) as e:
        return f"Ошибка: {e}"
    return _format_task(task, restricted=svc.is_restricted)


@mcp.resource("odoo://task/{task_id}/timesheets")
async def resource_task_timesheets(task_id: int) -> str:
    """Трудозатраты задачи (read-only)."""
    svc = _get_service()
    try:
        task = await svc.get_timesheets(task_id)
    except (ValueError, PermissionError) as e:
        return f"Ошибка: {e}"
    restricted = svc.is_restricted
    lines = [
        f"Трудозатраты по "
        f"{'ID ' + str(task.id) if restricted else '[' + str(task.id) + '] ' + task.name}",
        f"Часы: {task.effective_hours:.1f}/{task.allocated_hours:.1f}"
        f" | Прогресс: {task.progress:.0%}",
    ]
    if not task.timesheets:
        lines.append("Записей нет.")
    else:
        for ts in task.timesheets:
            if restricted:
                lines.append(f"- {ts.date} | {ts.hours:.2f}ч")
            else:
                lines.append(
                    f"- {ts.date} | {ts.employee.name} | {ts.hours:.2f}ч | {ts.description}"
                )
    return "\n".join(lines)


# --- Tools (read-write) ---


@mcp.tool()
async def list_tasks(
    project_id: int | None = None,
    include_closed: bool = False,
    limit: int = 40,
) -> str:
    """Получить список задач текущего пользователя.

    Args:
        project_id: Фильтр по проекту (None — все проекты)
        include_closed: Включать закрытые задачи
        limit: Максимум задач (по умолчанию 40)
    """
    svc = _get_service()
    restricted = svc.is_restricted
    tasks, total = await svc.list_tasks(
        project_id=project_id, include_closed=include_closed, limit=limit
    )

    lines = [f"Найдено задач: {total} (показано {len(tasks)})"]
    for t in tasks:
        deadline_str = f" | Дедлайн: {t.deadline}" if t.deadline else ""
        hours_str = (
            f" | {t.effective_hours:.1f}/{t.allocated_hours:.1f}ч" if t.allocated_hours > 0 else ""
        )
        if restricted:
            lines.append(
                f"\n- **ID {t.id}**\n"
                f"  Стадия: {t.stage.name} "
                f"| Приоритет: {t.priority.name}"
                f"{deadline_str}{hours_str}"
            )
        else:
            lines.append(
                f"\n- **[{t.id}] {t.name}**\n"
                f"  Проект: {t.project.name} "
                f"| Стадия: {t.stage.name} "
                f"| Приоритет: {t.priority.name}"
                f"{deadline_str}{hours_str}"
            )

    return "\n".join(lines)


@mcp.tool()
async def get_task(task_id: int) -> str:
    """Получить детали задачи с обсуждениями, трудозатратами и вложениями.

    Args:
        task_id: ID задачи в Odoo
    """
    svc = _get_service()
    task = await svc.get_task(task_id)
    return _format_task(task, restricted=svc.is_restricted)


@mcp.tool()
async def create_task(
    name: str,
    project_id: int,
    description: str | None = None,
    assignee_ids: list[int] | None = None,
) -> str:
    """Создать новую задачу в проекте.

    Args:
        name: Название задачи
        project_id: ID проекта
        description: Описание задачи (HTML или текст)
        assignee_ids: ID исполнителей (по умолчанию — текущий пользователь)
    """
    svc = _get_service()
    task = await svc.create_task(
        name=name, project_id=project_id, description=description, assignee_ids=assignee_ids
    )
    if svc.is_restricted:
        return f"Задача создана: ID {task.id} | Стадия: {task.stage.name}"
    return (
        f"Задача создана: [{task.id}] {task.name}\n"
        f"Проект: {task.project.name} "
        f"| Стадия: {task.stage.name}"
    )


@mcp.tool()
async def update_task(
    task_id: int,
    name: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    deadline: str | None = None,
    allocated_hours: float | None = None,
    assignee_ids: list[int] | None = None,
    tag_ids: list[int] | None = None,
) -> str:
    """Обновить существующую задачу.

    Args:
        task_id: ID задачи
        name: Новое название
        description: Новое описание
        priority: Приоритет ("0" — обычный, "1" — срочный)
        deadline: Дедлайн (формат YYYY-MM-DD или None для сброса)
        allocated_hours: Запланированные часы (например 5.0, 9.0)
        assignee_ids: Новый список исполнителей (заменяет текущих)
        tag_ids: Новый список тегов (заменяет текущие)
    """
    svc = _get_service()
    task = await svc.update_task(
        task_id=task_id,
        name=name,
        description=description,
        priority=priority,
        deadline=deadline,
        allocated_hours=allocated_hours,
        assignee_ids=assignee_ids,
        tag_ids=tag_ids,
    )
    if svc.is_restricted:
        return f"Задача обновлена: ID {task.id} | Стадия: {task.stage.name}"
    return (
        f"Задача обновлена: [{task.id}] {task.name}\n"
        f"Стадия: {task.stage.name} "
        f"| Статус: {task.state.name}"
    )


@mcp.tool()
async def change_task_stage(task_id: int, stage_id: int) -> str:
    """Сменить стадию задачи (Kanban-колонку).

    Args:
        task_id: ID задачи
        stage_id: ID новой стадии
    """
    svc = _get_service()
    task = await svc.change_task_stage(task_id=task_id, stage_id=stage_id)
    if svc.is_restricted:
        return f"Стадия изменена: ID {task.id} | Новая стадия: {task.stage.name}"
    return (
        f"Стадия изменена: [{task.id}] {task.name}\n"
        f"Новая стадия: {task.stage.name} "
        f"| Статус: {task.state.name}"
    )


@mcp.tool()
async def log_timesheet(
    task_id: int,
    hours: float,
    description: str,
    log_date: str | None = None,
) -> str:
    """Списать трудозатраты по задаче.

    Args:
        task_id: ID задачи
        hours: Количество часов (например 0.5, 1.0, 2.5)
        description: Описание выполненной работы
        log_date: Дата списания (YYYY-MM-DD, по умолчанию — сегодня)
    """
    svc = _get_service()
    task = await svc.log_timesheet(
        task_id=task_id, hours=hours, description=description, log_date=log_date
    )
    if svc.is_restricted:
        return (
            f"Трудозатраты списаны: {hours:.2f}ч на ID {task.id}\n"
            f"Итого: {task.effective_hours:.1f}ч"
        )
    return (
        f"Трудозатраты списаны: {hours:.2f}ч "
        f"на [{task.id}] {task.name}\n"
        f"Дата: {log_date or 'сегодня'} "
        f"| Описание: {description}\n"
        f"Итого: {task.effective_hours:.1f}ч"
    )


@mcp.tool()
async def post_comment(
    task_id: int,
    body: str,
    internal: bool = False,
) -> str:
    """Оставить комментарий к задаче.

    Args:
        task_id: ID задачи
        body: Текст комментария
        internal: Внутренняя заметка (True) или публичный комментарий (False)
    """
    svc = _get_service()
    msg = await svc.post_comment(task_id=task_id, body=body, internal=internal)
    msg_id = msg.get("id", "?")
    note_type = "Заметка" if internal else "Комментарий"
    return f"{note_type} #{msg_id} добавлен к задаче {task_id}"


@mcp.tool()
async def get_timesheets(task_id: int) -> str:
    """Получить трудозатраты по задаче.

    Args:
        task_id: ID задачи
    """
    svc = _get_service()
    task = await svc.get_timesheets(task_id)
    restricted = svc.is_restricted

    if restricted:
        lines = [
            f"Трудозатраты по ID {task.id}",
            f"Запланировано: {task.allocated_hours:.1f}ч "
            f"| Затрачено: {task.effective_hours:.1f}ч "
            f"| Осталось: {task.remaining_hours:.1f}ч "
            f"| Прогресс: {task.progress:.0%}",
        ]
        if not task.timesheets:
            lines.append("\nЗаписей нет.")
        else:
            lines.append("")
            for ts in task.timesheets:
                lines.append(f"- {ts.date} | {ts.hours:.2f}ч")
    else:
        lines = [
            f"Трудозатраты по [{task.id}] {task.name}",
            f"Запланировано: {task.allocated_hours:.1f}ч "
            f"| Затрачено: {task.effective_hours:.1f}ч "
            f"| Осталось: {task.remaining_hours:.1f}ч "
            f"| Прогресс: {task.progress:.0%}",
        ]
        if not task.timesheets:
            lines.append("\nЗаписей нет.")
        else:
            lines.append("")
            for ts in task.timesheets:
                lines.append(
                    f"- {ts.date} | {ts.employee.name} | {ts.hours:.2f}ч | {ts.description}"
                )

    return "\n".join(lines)


# --- Wiki Resources (read-only) ---


@mcp.resource("odoo://wiki/categories")
async def resource_wiki_categories() -> str:
    """Корневые категории wiki (document.page)."""
    svc = _get_wiki_service()
    try:
        pages = await svc.list_pages(parent_id=None)
    except Exception as e:
        return f"Ошибка: модуль wiki (document.page) недоступен. {e}"
    categories = [p for p in pages if p.type == WikiPageType.CATEGORY]
    return _format_wiki_list(categories, restricted=svc.is_restricted)


@mcp.resource("odoo://wiki/category/{category_id}")
async def resource_wiki_category(category_id: int) -> str:
    """Содержимое категории wiki — подкатегории и страницы."""
    svc = _get_wiki_service()
    try:
        pages = await svc.list_pages(parent_id=category_id)
    except Exception as e:
        return f"Ошибка: {e}"
    return _format_wiki_list(pages, restricted=svc.is_restricted)


@mcp.resource("odoo://wiki/{page_id}")
async def resource_wiki_page(page_id: int) -> str:
    """Содержимое wiki-страницы (с учётом режима доверия и фильтра)."""
    svc = _get_wiki_service()
    try:
        page = await svc.get_page(page_id)
    except (ValueError, Exception) as e:
        return f"Ошибка: {e}"
    return _format_wiki_page(
        page,
        restricted=svc.is_restricted,
        sensitive_filter=svc.sensitive_filter_enabled,
    )


# --- Wiki Tools ---


@mcp.tool()
async def list_wiki_pages(parent_id: int | None = None) -> str:
    """Получить список wiki-страниц и категорий.

    Args:
        parent_id: ID родительской категории (None — корневые)
    """
    svc = _get_wiki_service()
    try:
        pages = await svc.list_pages(parent_id=parent_id)
    except Exception as e:
        return f"Ошибка: модуль wiki (document.page) недоступен. {e}"
    return _format_wiki_list(pages, restricted=svc.is_restricted)


@mcp.tool()
async def get_wiki_page(page_id: int) -> str:
    """Получить содержимое wiki-страницы.

    Чувствительный контент (пароли, ключи) цензурируется автоматически.

    Args:
        page_id: ID wiki-страницы
    """
    svc = _get_wiki_service()
    page = await svc.get_page(page_id)
    return _format_wiki_page(
        page,
        restricted=svc.is_restricted,
        sensitive_filter=svc.sensitive_filter_enabled,
    )


@mcp.tool()
async def create_wiki_page(
    name: str,
    parent_id: int,
    content: str | None = None,
) -> str:
    """Создать wiki-страницу в указанной категории.

    Args:
        name: Название страницы
        parent_id: ID родительской категории
        content: Содержимое (HTML или текст, необязательно)
    """
    svc = _get_wiki_service()
    page = await svc.create_page(name=name, parent_id=parent_id, content=content)
    return (
        f"Wiki-страница создана: [{page.id}] {page.name}\n"
        f"Категория: {page.parent_name or parent_id}"
    )


@mcp.tool()
async def search_wiki(query: str) -> str:
    """Поиск wiki-страниц по названию.

    Args:
        query: Поисковый запрос (часть названия)
    """
    svc = _get_wiki_service()
    try:
        pages = await svc.search_pages(query=query)
    except Exception as e:
        return f"Ошибка: {e}"
    return _format_wiki_list(pages, restricted=svc.is_restricted)
