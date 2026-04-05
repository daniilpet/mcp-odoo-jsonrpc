from typing import Any

from mcp_odoo_jsonrpc.acl.transport import OdooTransport
from mcp_odoo_jsonrpc.config import OdooConfig, TrustMode

# --- Full mode specifications ---

TASK_LIST_SPEC: dict[str, Any] = {
    "stage_id": {"fields": {"display_name": {}}},
    "state": {},
    "name": {},
    "parent_id": {"fields": {"display_name": {}}},
    "project_id": {"fields": {"display_name": {}}},
    "partner_id": {"fields": {"display_name": {}}},
    "milestone_id": {"fields": {"display_name": {}}},
    "tag_ids": {"fields": {"display_name": {}, "color": {}}},
    "date_deadline": {},
    "priority": {},
    "user_ids": {"fields": {"display_name": {}}, "context": {"active_test": False}},
    "subtask_count": {},
    "closed_subtask_count": {},
    "allocated_hours": {},
    "remaining_hours": {},
    "effective_hours": {},
    "progress": {},
    "is_closed": {},
    "color": {},
    "duration_tracking": {},
}

TASK_DETAIL_SPEC: dict[str, Any] = {
    **TASK_LIST_SPEC,
    "description": {},
    "timesheet_ids": {
        "fields": {
            "readonly_timesheet": {},
            "date": {},
            "user_id": {"fields": {}},
            "employee_id": {"fields": {"display_name": {}}},
            "name": {},
            "unit_amount": {},
            "project_id": {"fields": {}},
            "task_id": {"fields": {}},
            "company_id": {"fields": {}},
        },
        "limit": 80,
        "order": "date ASC",
    },
    "total_hours_spent": {},
}

TASK_SAVE_RESULT_SPEC: dict[str, Any] = {
    "stage_id": {"fields": {"display_name": {}}},
    "state": {},
    "name": {},
    "project_id": {"fields": {"display_name": {}}},
    "user_ids": {"fields": {"display_name": {}}, "context": {"active_test": False}},
    "is_closed": {},
    "duration_tracking": {},
}

# --- Restricted mode specifications ---
# Не запрашивают: name, description, partner_id, user_ids, tag_ids,
# parent_id, milestone_id, subtask_count, duration_tracking

TASK_LIST_RESTRICTED_SPEC: dict[str, Any] = {
    "stage_id": {"fields": {"display_name": {}}},
    "state": {},
    "priority": {},
    "date_deadline": {},
    "project_id": {"fields": {}},
    "allocated_hours": {},
    "remaining_hours": {},
    "effective_hours": {},
    "progress": {},
    "is_closed": {},
}

TASK_DETAIL_RESTRICTED_SPEC: dict[str, Any] = {
    **TASK_LIST_RESTRICTED_SPEC,
    "timesheet_ids": {
        "fields": {
            "date": {},
            "unit_amount": {},
        },
        "limit": 80,
        "order": "date ASC",
    },
    "total_hours_spent": {},
}

TASK_SAVE_RESTRICTED_SPEC: dict[str, Any] = {
    "stage_id": {"fields": {"display_name": {}}},
    "state": {},
    "project_id": {"fields": {}},
    "is_closed": {},
}


class OdooProtocol:
    def __init__(self, transport: OdooTransport, config: OdooConfig) -> None:
        self._transport = transport
        self._config = config
        self._trust_mode = config.trust_mode
        self._allowed_projects = config.allowed_project_ids

    @property
    def is_restricted(self) -> bool:
        return self._trust_mode == TrustMode.RESTRICTED

    def _inject_project_filter(self, domain: list[Any]) -> list[Any]:
        if not self._allowed_projects:
            return domain
        project_filter = ["project_id", "in", self._allowed_projects]
        if domain:
            return (
                ["&", project_filter, *domain]
                if len(domain) == 1
                else ["&", project_filter, *domain]
            )
        return [project_filter]

    def _validate_project(self, project_id: int) -> None:
        if self._allowed_projects and project_id not in self._allowed_projects:
            raise PermissionError(
                f"Проект {project_id} не входит в список разрешённых: {self._allowed_projects}. "
                f"Настройте ODOO_ALLOWED_PROJECTS."
            )

    async def validate_session(self) -> dict[str, Any]:
        result = await self._transport.call_kw(
            model="res.users",
            method="search_read",
            args=[],
            kwargs={
                "domain": [["id", "=", self._config.uid]],
                "fields": ["display_name"],
                "context": self._config.context,
            },
        )
        if not result:
            raise RuntimeError(
                f"Пользователь uid={self._config.uid} не найден. Проверьте ODOO_UID."
            )
        return result[0]

    async def search_tasks(
        self,
        domain: list[Any] | None = None,
        limit: int = 80,
        offset: int = 0,
    ) -> dict[str, Any]:
        if domain is None:
            domain = ["&", ["user_ids", "in", self._config.uid], ["state", "!=", "1_done"]]

        domain = self._inject_project_filter(domain)
        spec = TASK_LIST_RESTRICTED_SPEC if self.is_restricted else TASK_LIST_SPEC

        return await self._transport.call_kw(
            model="project.task",
            method="web_search_read",
            args=[],
            kwargs={
                "specification": spec,
                "domain": domain,
                "offset": offset,
                "limit": limit,
                "order": "priority DESC, date_deadline ASC, id DESC",
                "context": self._config.context,
                "count_limit": 10001,
            },
        )

    async def read_task(self, task_id: int) -> dict[str, Any]:
        spec = TASK_DETAIL_RESTRICTED_SPEC if self.is_restricted else TASK_DETAIL_SPEC

        result = await self._transport.call_kw(
            model="project.task",
            method="web_search_read",
            args=[],
            kwargs={
                "specification": spec,
                "domain": [["id", "=", task_id]],
                "limit": 1,
                "context": self._config.context,
                "count_limit": 1,
            },
        )
        records = result.get("records", [])
        if not records:
            raise ValueError(f"Задача с id={task_id} не найдена")

        record = records[0]
        project_data = record.get("project_id")
        if project_data and isinstance(project_data, dict):
            self._validate_project(project_data["id"])
        elif project_data and isinstance(project_data, int):
            self._validate_project(project_data)

        return record

    async def save_task(
        self,
        task_id: int | None,
        values: dict[str, Any],
        specification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if task_id is None and "project_id" in values:
            self._validate_project(values["project_id"])

        ids = [] if task_id is None else [task_id]
        if specification is None:
            specification = (
                TASK_SAVE_RESTRICTED_SPEC if self.is_restricted else TASK_SAVE_RESULT_SPEC
            )

        context = {
            **self._config.context,
            "default_user_ids": [[4, self._config.uid]],
        }

        result = await self._transport.call_kw(
            model="project.task",
            method="web_save",
            args=[ids, values],
            kwargs={
                "context": context,
                "specification": specification,
            },
        )
        if not result:
            raise RuntimeError("web_save вернул пустой результат")
        return result[0]

    async def get_task_stages(self, project_id: int) -> list[dict[str, Any]]:
        self._validate_project(project_id)
        return await self._transport.call_kw(
            model="project.task.type",
            method="search_read",
            args=[],
            kwargs={
                "domain": [["project_ids", "=", project_id]],
                "fields": ["display_name", "fold"],
                "context": self._config.context,
            },
        )

    async def get_messages(
        self,
        task_id: int,
        limit: int = 30,
        after: int = 0,
    ) -> dict[str, Any]:
        if self.is_restricted:
            return {"data": {}, "messages": []}

        return await self._transport.call(
            "/mail/thread/messages",
            {
                "thread_id": task_id,
                "thread_model": "project.task",
                "limit": limit,
                "after": after,
            },
        )

    async def get_thread_data(self, task_id: int) -> dict[str, Any]:
        if self.is_restricted:
            return {}

        return await self._transport.call(
            "/mail/thread/data",
            {
                "request_list": ["attachments", "followers"],
                "thread_id": task_id,
                "thread_model": "project.task",
            },
        )
