import asyncio
import sys
from datetime import date as date_type

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from mcp_odoo_jsonrpc.acl.transport import OdooSessionExpiredError
from mcp_odoo_jsonrpc.config import OdooConfig, OdooSession, TrustMode
from mcp_odoo_jsonrpc.domain.models import Task
from mcp_odoo_jsonrpc.service import OdooTaskService

console = Console()


def _greet(config: OdooConfig) -> None:
    console.print(
        Panel.fit(
            f"[bold green]Добро пожаловать, {config.display_name}![/]\n[dim]{config.base_url}[/]",
            title="[bold]Odoo CLI[/]",
            border_style="green",
        )
    )


def _print_task_table(tasks: list[Task]) -> None:
    table = Table(title=f"Мои задачи ({len(tasks)})", show_lines=False, pad_edge=False)
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Название", min_width=30, max_width=60)
    table.add_column("Проект", style="green", max_width=20)
    table.add_column("Стадия", style="yellow", max_width=15)
    table.add_column("!", justify="center", width=1)
    table.add_column("Дедлайн", style="red", width=10)
    table.add_column("Часы", justify="right", width=10)

    for i, task in enumerate(tasks, 1):
        priority_str = "[bold red]![/]" if task.priority.value == "1" else ""
        deadline_str = str(task.deadline) if task.deadline else ""
        hours_str = (
            f"{task.effective_hours:.1f}/{task.allocated_hours:.1f}"
            if task.allocated_hours > 0
            else ""
        )
        table.add_row(
            str(i),
            str(task.id),
            task.name,
            task.project.name,
            task.stage.name,
            priority_str,
            deadline_str,
            hours_str,
        )

    console.print(table)


def _print_task_detail(task: Task) -> None:
    lines = [f"[bold]{task.name}[/]\n"]
    lines.append(f"Проект: [green]{task.project.name}[/]")
    lines.append(f"Стадия: [yellow]{task.stage.name}[/] | Статус: {task.state.name}")
    lines.append(
        f"Приоритет: {'[bold red]СРОЧНЫЙ[/]' if task.priority.value == '1' else 'обычный'}"
    )
    if task.assignees:
        lines.append(f"Исполнители: {', '.join(u.name for u in task.assignees)}")
    if task.partner:
        lines.append(f"Заказчик: {task.partner.name}")
    if task.deadline:
        lines.append(f"Дедлайн: [red]{task.deadline}[/]")
    if task.allocated_hours > 0:
        lines.append(
            f"Часы: {task.effective_hours:.1f}/{task.allocated_hours:.1f} "
            f"(прогресс {task.progress:.0%})"
        )
    if task.subtask_count > 0:
        lines.append(f"Подзадачи: {task.closed_subtask_count}/{task.subtask_count}")
    if task.description:
        lines.append(f"\n[dim]{task.description}[/]")

    console.print(Panel("\n".join(lines), title=f"[bold]#{task.id}[/]", border_style="blue"))


def _show_task_actions() -> str:
    console.print(
        "\n  [cyan]d[/] — детали  [cyan]t[/] — трудозатраты  "
        "[cyan]l[/] — списать время  [cyan]s[/] — сменить стадию\n"
        "  [cyan]c[/] — комментарий  [cyan]n[/] — заметка  "
        "[cyan]b[/] — назад"
    )
    return Prompt.ask(
        "Действие",
        choices=["d", "t", "l", "s", "c", "n", "b"],
        default="d",
    )


async def _task_context_loop(task: Task, svc: OdooTaskService) -> None:
    console.print(f"\n[bold]Выбрана:[/] [cyan]#{task.id}[/] {task.name}")

    while True:
        action = _show_task_actions()

        if action == "b":
            break

        if action == "d":
            full_task = await svc.get_task(task.id)
            _print_task_detail(full_task)

        elif action == "t":
            t = await svc.get_timesheets(task.id)
            console.print(
                f"\nЗапланировано: {t.allocated_hours:.1f}ч | "
                f"Затрачено: {t.effective_hours:.1f}ч | "
                f"Осталось: {t.remaining_hours:.1f}ч"
            )
            if not t.timesheets:
                console.print("[dim]Записей нет.[/]")
            else:
                table = Table(show_lines=False)
                table.add_column("Дата", style="cyan")
                table.add_column("Сотрудник")
                table.add_column("Часы", justify="right", style="green")
                table.add_column("Описание")
                for ts in t.timesheets:
                    table.add_row(str(ts.date), ts.employee.name, f"{ts.hours:.2f}", ts.description)
                console.print(table)

        elif action == "l":
            hours = float(Prompt.ask("Часы"))
            description = Prompt.ask("Описание")
            log_date = Prompt.ask("Дата", default=date_type.today().isoformat())
            updated = await svc.log_timesheet(task.id, hours, description, log_date)
            console.print(f"[green]Списано {hours:.2f}ч.[/] Итого: {updated.effective_hours:.1f}ч")

        elif action == "s":
            stages = await svc.get_task_stages(task.project.id)
            console.print(f"\nТекущая стадия: [yellow]{task.stage.name}[/]\n")
            for i, s in enumerate(stages, 1):
                marker = " [bold green]◄[/]" if s.id == task.stage.id else ""
                console.print(f"  [cyan]{i}[/] — {s.name}{marker}")

            raw = Prompt.ask("Номер стадии", default="b")
            if raw.strip().lower() == "b":
                continue
            try:
                idx = int(raw)
                if 1 <= idx <= len(stages):
                    updated = await svc.change_task_stage(task.id, stages[idx - 1].id)
                    task = task.model_copy(update={"stage": updated.stage})
                    console.print(f"[green]Стадия изменена:[/] {updated.stage.name}")
                else:
                    console.print("[red]Неверный номер[/]")
            except ValueError:
                console.print("[red]Введите номер стадии[/]")

        elif action in ("c", "n"):
            internal = action == "n"
            label = "Заметка (внутренняя)" if internal else "Комментарий"
            body = Prompt.ask(label)
            if body.strip():
                msg = await svc.post_comment(task.id, body, internal=internal)
                msg_id = msg.get("id", "?")
                console.print(f"[green]{label} #{msg_id} добавлен[/]")
            else:
                console.print("[dim]Пустой текст, отмена[/]")


async def _tasks_loop(svc: OdooTaskService) -> None:
    tasks: list[Task] = []

    while True:
        if not tasks:
            console.print("\n[dim]Загрузка задач...[/]")
            tasks, _ = await svc.list_tasks(limit=50)
            _print_task_table(tasks)

        console.print("\n  [cyan]#[/] — выбрать задачу  [cyan]r[/] — обновить  [cyan]b[/] — назад")
        raw = Prompt.ask("Ввод", default="b")

        if raw.strip().lower() == "b":
            break
        if raw.strip().lower() == "r":
            tasks = []
            continue

        try:
            num = int(raw)
            task = None
            if 1 <= num <= len(tasks):
                task = tasks[num - 1]
            else:
                task = next((t for t in tasks if t.id == num), None)
            if task:
                await _task_context_loop(task, svc)
                tasks = []
            else:
                console.print(f"[red]Задача {num} не найдена. Введите # строки или Odoo ID.[/]")
        except ValueError:
            console.print("[red]Введите номер задачи, 'r' или 'b'[/]")


async def _run_cli() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        from mcp_odoo_jsonrpc.auth import browser_login

        base_url = None
        for i, arg in enumerate(sys.argv[2:], start=2):
            if arg == "--url" and i + 1 < len(sys.argv):
                base_url = sys.argv[i + 1]
                break
            if arg.startswith("--url="):
                base_url = arg.split("=", 1)[1]
                break
            if arg.startswith("http"):
                base_url = arg
                break

        if not base_url:
            base_url = Prompt.ask("URL Odoo", default="https://odoo.example.com")

        await browser_login(base_url)
        return

    if not OdooSession.exists():
        console.print("[red]Сессия не найдена.[/] Выполните: [bold]mcp-odoo-cli login[/]")
        sys.exit(1)

    config = OdooConfig.from_session_file(trust_mode_override=TrustMode.FULL)
    svc = OdooTaskService(config)

    try:
        await svc.validate_session()
    except OdooSessionExpiredError:
        console.print("[red]Сессия истекла.[/] Выполните: [bold]mcp-odoo-cli login[/]")
        OdooSession.clear()
        sys.exit(1)

    _greet(config)

    try:
        while True:
            console.print("\n[bold]Разделы:[/]  [cyan]1[/] — Задачи  [cyan]q[/] — Выход")
            choice = Prompt.ask("Раздел", choices=["1", "q"], default="1")
            if choice == "q":
                console.print("[dim]До свидания![/]")
                break
            if choice == "1":
                await _tasks_loop(svc)
    except KeyboardInterrupt:
        console.print("\n[dim]До свидания![/]")
    finally:
        await svc.close()


def main() -> None:
    asyncio.run(_run_cli())


if __name__ == "__main__":
    main()
