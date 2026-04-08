from datetime import date, datetime
from typing import Any

from mcp_odoo_jsonrpc.domain.enums import MessageType, TaskPriority, TaskState, WikiPageType
from mcp_odoo_jsonrpc.domain.models import (
    Attachment,
    FieldChange,
    Message,
    Milestone,
    Partner,
    Project,
    Stage,
    Subtask,
    Tag,
    Task,
    TaskRef,
    Timesheet,
    User,
    WikiPage,
    WikiPageHistory,
)


def _parse_date(value: Any) -> date | None:
    if not value or value is False:
        return None
    raw = str(value).strip()
    if " " in raw:
        raw = raw.split(" ")[0]
    return date.fromisoformat(raw)


def _parse_datetime(value: Any) -> datetime | None:
    if not value or value is False:
        return None
    return datetime.fromisoformat(value)


def _parse_ref(value: Any, cls: type) -> Any | None:
    if not value or value is False:
        return None
    return cls(id=value["id"], name=value.get("display_name", ""))


def _parse_ref_list(values: Any, cls: type) -> list:
    if not values or values is False:
        return []
    return [cls(id=v["id"], name=v.get("display_name", "")) for v in values]


def translate_task(record: dict[str, Any]) -> Task:
    tags = []
    for t in record.get("tag_ids") or []:
        tags.append(Tag(id=t["id"], name=t.get("display_name", ""), color=t.get("color", 0)))

    timesheets = []
    for ts in record.get("timesheet_ids") or []:
        employee_data = ts.get("employee_id")
        employee = (
            User(id=employee_data["id"], name=employee_data.get("display_name", ""))
            if employee_data and employee_data is not False
            else User(id=0, name="Unknown")
        )
        timesheets.append(
            Timesheet(
                id=ts.get("id"),
                date=date.fromisoformat(ts["date"]),
                employee=employee,
                description=ts.get("name", ""),
                hours=ts.get("unit_amount", 0.0),
                readonly=ts.get("readonly_timesheet", False),
            )
        )

    subtasks = []
    for child in record.get("child_ids") or []:
        subtasks.append(
            Subtask(
                id=child["id"],
                name=child.get("name", ""),
                state=TaskState.from_odoo(child.get("state", "01_in_progress")),
                stage=_parse_ref(child.get("stage_id"), Stage) or Stage(id=0, name="Unknown"),
                priority=TaskPriority.from_odoo(child.get("priority", "0")),
                assignees=_parse_ref_list(child.get("user_ids"), User),
                deadline=_parse_date(child.get("date_deadline")),
                allocated_hours=child.get("allocated_hours", 0.0),
                effective_hours=child.get("effective_hours", 0.0),
                progress=child.get("progress", 0.0),
            )
        )

    duration_tracking = {}
    raw_tracking = record.get("duration_tracking")
    if raw_tracking and isinstance(raw_tracking, dict):
        duration_tracking = {int(k): int(v) for k, v in raw_tracking.items()}

    return Task(
        id=record["id"],
        name=record.get("name", ""),
        description=record.get("description") or None,
        state=TaskState.from_odoo(record.get("state", "01_in_progress")),
        priority=TaskPriority.from_odoo(record.get("priority", "0")),
        stage=_parse_ref(record.get("stage_id"), Stage) or Stage(id=0, name="Unknown"),
        project=_parse_ref(record.get("project_id"), Project) or Project(id=0, name="Unknown"),
        parent=_parse_ref(record.get("parent_id"), TaskRef),
        assignees=_parse_ref_list(record.get("user_ids"), User),
        partner=_parse_ref(record.get("partner_id"), Partner),
        tags=tags,
        milestone=_parse_ref(record.get("milestone_id"), Milestone),
        deadline=_parse_date(record.get("date_deadline")),
        is_closed=record.get("is_closed", False),
        allocated_hours=record.get("allocated_hours", 0.0),
        effective_hours=record.get("effective_hours", 0.0),
        remaining_hours=record.get("remaining_hours", 0.0),
        progress=record.get("progress", 0.0),
        subtask_count=record.get("subtask_count", 0),
        closed_subtask_count=record.get("closed_subtask_count", 0),
        subtasks=subtasks,
        duration_tracking=duration_tracking,
        timesheets=timesheets,
    )


def translate_stage(record: dict[str, Any]) -> Stage:
    return Stage(
        id=record["id"],
        name=record.get("display_name", ""),
        folded=record.get("fold", False),
    )


def translate_messages(
    raw: dict[str, Any],
) -> list[Message]:
    data = raw.get("data", {})
    raw_messages = data.get("mail.message", [])
    partners = {p["id"]: p for p in data.get("res.partner", [])}

    messages = []
    for msg in raw_messages:
        author = None
        author_ref = msg.get("author")
        if author_ref and isinstance(author_ref, dict):
            partner_id = author_ref.get("id")
            partner_data = partners.get(partner_id, {})
            author = User(
                id=partner_data.get("userId", partner_id),
                name=partner_data.get("name", ""),
            )

        tracking = []
        for tv in msg.get("trackingValues") or []:
            tracking.append(
                FieldChange(
                    field=tv.get("changedField", ""),
                    field_name=tv.get("fieldName", ""),
                    old_value=str(tv.get("oldValue", {}).get("value", "")),
                    new_value=str(tv.get("newValue", {}).get("value", "")),
                )
            )

        messages.append(
            Message(
                id=msg["id"],
                author=author,
                body=msg.get("body", ""),
                date=datetime.fromisoformat(msg["date"]),
                type=MessageType.from_odoo(
                    msg.get("message_type", "notification"),
                    msg.get("is_note", False),
                    msg.get("is_discussion", False),
                ),
                tracking=tracking,
            )
        )

    return messages


def translate_attachments(raw: dict[str, Any]) -> list[Attachment]:
    attachments = []
    for att in raw.get("ir.attachment", []):
        attachments.append(
            Attachment(
                id=att["id"],
                name=att.get("name", ""),
                mimetype=att.get("mimetype", "application/octet-stream"),
                size=att.get("file_size", 0),
                access_token=att.get("access_token", ""),
            )
        )
    return attachments


def translate_wiki_history(record: dict[str, Any]) -> WikiPageHistory:
    page_ref = record.get("page_id")
    page_id = 0
    page_name = ""
    if page_ref and page_ref is not False:
        if isinstance(page_ref, dict):
            page_id = page_ref.get("id", 0)
            page_name = page_ref.get("display_name", "")
        elif isinstance(page_ref, int):
            page_id = page_ref

    return WikiPageHistory(
        id=record["id"],
        page_id=page_id,
        page_name=page_name,
        author=_parse_ref(record.get("create_uid"), User),
        create_date=_parse_datetime(record.get("create_date")),
        name=record.get("name", ""),
        summary=record.get("summary", ""),
    )


def translate_wiki_page(record: dict[str, Any]) -> WikiPage:
    parent_ref = record.get("parent_id")
    parent_id = None
    parent_name = None
    if parent_ref and parent_ref is not False:
        if isinstance(parent_ref, dict):
            parent_id = parent_ref.get("id")
            parent_name = parent_ref.get("display_name")
        elif isinstance(parent_ref, int):
            parent_id = parent_ref

    history = []
    for h in record.get("history_ids") or []:
        history.append(translate_wiki_history(h))

    return WikiPage(
        id=record["id"],
        name=record.get("name", ""),
        type=WikiPageType.from_odoo(record.get("type", "content")),
        parent_id=parent_id,
        parent_name=parent_name,
        write_date=_parse_datetime(record.get("write_date")),
        create_uid=_parse_ref(record.get("create_uid"), User),
        content_uid=_parse_ref(record.get("content_uid"), User),
        content=record.get("content") or None,
        content_date=_parse_datetime(record.get("content_date")),
        color=record.get("color", 0),
        history=history,
    )
