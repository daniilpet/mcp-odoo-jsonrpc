from mcp.server.fastmcp import FastMCP

from mcp_odoo_jsonrpc.config import OdooConfig
from mcp_odoo_jsonrpc.domain.models import Task
from mcp_odoo_jsonrpc.service import OdooTaskService

mcp = FastMCP(
    "Odoo Tasks",
    instructions=(
        "MCP-сервер для управления задачами в Odoo ERP. "
        "Позволяет просматривать, создавать и обновлять задачи, "
        "менять стадии и списывать трудозатраты."
    ),
)

_service: OdooTaskService | None = None


def _get_service() -> OdooTaskService:
    global _service
    if _service is None:
        _service = OdooTaskService(OdooConfig.auto())
    return _service


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
