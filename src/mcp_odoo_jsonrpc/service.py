from datetime import date
from typing import Any

from mcp_odoo_jsonrpc.acl.mapper import (
    translate_attachments,
    translate_messages,
    translate_stage,
    translate_task,
)
from mcp_odoo_jsonrpc.acl.protocol import (
    TASK_DETAIL_RESTRICTED_SPEC,
    TASK_DETAIL_SPEC,
    OdooProtocol,
)
from mcp_odoo_jsonrpc.acl.transport import OdooTransport
from mcp_odoo_jsonrpc.config import OdooConfig
from mcp_odoo_jsonrpc.domain.models import Project, Stage, Task


class OdooTaskService:
    def __init__(self, config: OdooConfig) -> None:
        self._config = config
        self._transport = OdooTransport(config)
        self._protocol = OdooProtocol(self._transport, config)

    @property
    def config(self) -> OdooConfig:
        return self._config

    @property
    def is_restricted(self) -> bool:
        return self._config.is_restricted

    async def validate_session(self) -> dict[str, Any]:
        return await self._protocol.validate_session()

    async def list_projects(self) -> list[Project]:
        raw = await self._protocol.list_projects()
        return [
            Project(
                id=r["id"],
                name=r.get("display_name", ""),
                task_count=r.get("task_count", 0),
            )
            for r in raw
        ]

    async def list_tasks(
        self,
        project_id: int | None = None,
        include_closed: bool = False,
        limit: int = 40,
    ) -> tuple[list[Task], int]:
        domain_parts: list[Any] = [["user_ids", "in", self._config.uid]]
        if not include_closed:
            domain_parts.append(["state", "!=", "1_done"])
        if project_id is not None:
            domain_parts.append(["project_id", "=", project_id])

        if len(domain_parts) > 1:
            domain: list[Any] = []
            for _ in range(len(domain_parts) - 1):
                domain.append("&")
            domain.extend(domain_parts)
        else:
            domain = domain_parts

        result = await self._protocol.search_tasks(domain=domain, limit=limit)
        records = result.get("records", [])
        total = result.get("length", 0)
        tasks = [translate_task(r) for r in records]
        return tasks, total

    async def get_task(self, task_id: int) -> Task:
        record = await self._protocol.read_task(task_id)
        task = translate_task(record)

        raw_messages = await self._protocol.get_messages(task_id)
        messages = translate_messages(raw_messages)

        raw_thread = await self._protocol.get_thread_data(task_id)
        attachments = translate_attachments(raw_thread)

        return task.model_copy(update={"messages": messages, "attachments": attachments})

    async def create_task(
        self,
        name: str,
        project_id: int,
        description: str | None = None,
        assignee_ids: list[int] | None = None,
    ) -> Task:
        values: dict[str, Any] = {
            "display_name": name,
            "project_id": project_id,
        }
        if description is not None:
            values["description"] = description
        if assignee_ids:
            values["user_ids"] = [[4, uid] for uid in assignee_ids]
        else:
            values["user_ids"] = [[4, self._config.uid]]

        record = await self._protocol.save_task(task_id=None, values=values)
        return translate_task(record)

    async def update_task(
        self,
        task_id: int,
        name: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        deadline: str | None = None,
        allocated_hours: float | None = None,
        assignee_ids: list[int] | None = None,
        tag_ids: list[int] | None = None,
    ) -> Task:
        values: dict[str, Any] = {}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description
        if priority is not None:
            values["priority"] = priority
        if deadline is not None:
            values["date_deadline"] = deadline
        if allocated_hours is not None:
            values["allocated_hours"] = allocated_hours
        if assignee_ids is not None:
            values["user_ids"] = [[6, 0, assignee_ids]]
        if tag_ids is not None:
            values["tag_ids"] = [[6, 0, tag_ids]]

        if not values:
            raise ValueError("Не указано ни одного поля для обновления")

        record = await self._protocol.save_task(task_id=task_id, values=values)
        return translate_task(record)

    async def change_task_stage(self, task_id: int, stage_id: int) -> Task:
        record = await self._protocol.save_task(
            task_id=task_id,
            values={"stage_id": stage_id},
        )
        return translate_task(record)

    async def get_task_stages(self, project_id: int) -> list[Stage]:
        raw = await self._protocol.get_task_stages(project_id)
        return [translate_stage(s) for s in raw]

    async def log_timesheet(
        self,
        task_id: int,
        hours: float,
        description: str,
        log_date: str | None = None,
    ) -> Task:
        ts_date = log_date or date.today().isoformat()

        timesheet_values = {
            "date": ts_date,
            "user_id": self._config.uid,
            "employee_id": self._config.employee_id,
            "name": description,
            "unit_amount": hours,
            "task_id": task_id,
        }

        spec = TASK_DETAIL_RESTRICTED_SPEC if self.is_restricted else TASK_DETAIL_SPEC

        record = await self._protocol.save_task(
            task_id=task_id,
            values={"timesheet_ids": [[0, f"virtual_{task_id}", timesheet_values]]},
            specification=spec,
        )
        return translate_task(record)

    async def post_comment(
        self,
        task_id: int,
        body: str,
        internal: bool = False,
    ) -> dict:
        subtype = "mail.mt_note" if internal else "mail.mt_comment"
        msg_type = "comment"
        result = await self._protocol.post_message(
            task_id=task_id,
            body=body,
            message_type=msg_type,
            subtype=subtype,
        )
        messages = result.get("mail.message", [])
        if messages:
            return messages[0]
        return result

    async def get_timesheets(self, task_id: int) -> Task:
        record = await self._protocol.read_task(task_id)
        return translate_task(record)

    async def close(self) -> None:
        await self._transport.close()
