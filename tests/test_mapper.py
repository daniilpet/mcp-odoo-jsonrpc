from mcp_odoo_jsonrpc.acl.mapper import (
    translate_attachments,
    translate_messages,
    translate_stage,
    translate_task,
)
from mcp_odoo_jsonrpc.domain.enums import TaskPriority, TaskState


def _make_record(**overrides):
    base = {
        "id": 100,
        "name": "Test Task",
        "state": "01_in_progress",
        "priority": "0",
        "stage_id": {"id": 1, "display_name": "New"},
        "project_id": {"id": 10, "display_name": "Project A"},
        "is_closed": False,
        "allocated_hours": 0.0,
        "effective_hours": 0.0,
        "remaining_hours": 0.0,
        "progress": 0.0,
        "subtask_count": 0,
        "closed_subtask_count": 0,
    }
    base.update(overrides)
    return base


def test_translate_task_minimal():
    task = translate_task(_make_record())
    assert task.id == 100
    assert task.name == "Test Task"
    assert task.state == TaskState.IN_PROGRESS
    assert task.priority == TaskPriority.NORMAL
    assert task.stage.name == "New"
    assert task.project.name == "Project A"


def test_translate_task_with_parent():
    task = translate_task(_make_record(
        parent_id={"id": 50, "display_name": "Epic"}
    ))
    assert task.parent is not None
    assert task.parent.id == 50
    assert task.parent.name == "Epic"


def test_translate_task_false_values():
    task = translate_task(_make_record(
        parent_id=False,
        partner_id=False,
        milestone_id=False,
        date_deadline=False,
        description=False,
    ))
    assert task.parent is None
    assert task.partner is None
    assert task.milestone is None
    assert task.deadline is None
    assert task.description is None


def test_translate_task_with_tags():
    task = translate_task(_make_record(
        tag_ids=[
            {"id": 1, "display_name": "Urgent", "color": 4},
            {"id": 2, "display_name": "Bug", "color": 1},
        ]
    ))
    assert len(task.tags) == 2
    assert task.tags[0].name == "Urgent"
    assert task.tags[0].color == 4


def test_translate_task_with_assignees():
    task = translate_task(_make_record(
        user_ids=[
            {"id": 33, "display_name": "Ivan"},
            {"id": 34, "display_name": "Maria"},
        ]
    ))
    assert len(task.assignees) == 2
    assert task.assignees[0].name == "Ivan"


def test_translate_task_with_timesheets():
    task = translate_task(_make_record(
        timesheet_ids=[
            {
                "id": 1,
                "date": "2026-04-01",
                "employee_id": {"id": 89, "display_name": "Ivan"},
                "name": "commit abc - fix bug",
                "unit_amount": 2.5,
                "readonly_timesheet": False,
            },
        ]
    ))
    assert len(task.timesheets) == 1
    assert task.timesheets[0].hours == 2.5
    assert task.timesheets[0].employee.name == "Ivan"


def test_translate_task_with_subtasks():
    task = translate_task(_make_record(
        child_ids=[
            {
                "id": 200,
                "name": "Subtask 1",
                "state": "01_in_progress",
                "stage_id": {"id": 1, "display_name": "New"},
                "priority": "1",
                "user_ids": [{"id": 33, "display_name": "Ivan"}],
                "allocated_hours": 3.0,
                "effective_hours": 1.0,
                "progress": 0.33,
            },
        ]
    ))
    assert len(task.subtasks) == 1
    assert task.subtasks[0].name == "Subtask 1"
    assert task.subtasks[0].priority == TaskPriority.URGENT


def test_translate_task_date_with_time():
    task = translate_task(_make_record(
        date_deadline="2026-02-16 14:00:00"
    ))
    assert task.deadline is not None
    assert str(task.deadline) == "2026-02-16"


def test_translate_task_duration_tracking():
    task = translate_task(_make_record(
        duration_tracking={"902": 261659, "903": 196593}
    ))
    assert task.duration_tracking == {902: 261659, 903: 196593}


def test_translate_stage():
    stage = translate_stage({"id": 5, "display_name": "Done", "fold": True})
    assert stage.id == 5
    assert stage.name == "Done"
    assert stage.folded is True


def test_translate_messages():
    raw = {
        "data": {
            "mail.message": [
                {
                    "id": 100,
                    "author": {"id": 176, "type": "partner"},
                    "body": "<p>Hello</p>",
                    "date": "2026-04-04 20:35:09",
                    "message_type": "comment",
                    "is_note": False,
                    "is_discussion": True,
                    "trackingValues": [],
                },
            ],
            "res.partner": [
                {"id": 176, "name": "Ivan", "userId": 33},
            ],
        },
        "messages": [100],
    }
    messages = translate_messages(raw)
    assert len(messages) == 1
    assert messages[0].body == "<p>Hello</p>"
    assert messages[0].author.name == "Ivan"


def test_translate_messages_empty():
    messages = translate_messages({"data": {}, "messages": []})
    assert messages == []


def test_translate_attachments():
    raw = {
        "ir.attachment": [
            {
                "id": 1,
                "name": "doc.pdf",
                "mimetype": "application/pdf",
                "file_size": 12345,
                "access_token": "abc123",
            },
        ],
    }
    attachments = translate_attachments(raw)
    assert len(attachments) == 1
    assert attachments[0].name == "doc.pdf"
    assert attachments[0].size == 12345


def test_translate_attachments_empty():
    assert translate_attachments({}) == []
