from mcp_odoo_jsonrpc.domain.enums import MessageType, TaskPriority, TaskState
from mcp_odoo_jsonrpc.domain.models import Project, Stage, Task


def test_task_state_from_odoo():
    assert TaskState.from_odoo("01_in_progress") == TaskState.IN_PROGRESS
    assert TaskState.from_odoo("1_done") == TaskState.DONE


def test_task_state_unknown_defaults():
    result = TaskState.from_odoo("99_unknown")
    assert result == TaskState.IN_PROGRESS


def test_task_priority_from_odoo():
    assert TaskPriority.from_odoo("0") == TaskPriority.NORMAL
    assert TaskPriority.from_odoo("1") == TaskPriority.URGENT


def test_message_type_from_odoo():
    assert MessageType.from_odoo("notification", True, False) == MessageType.NOTIFICATION
    assert MessageType.from_odoo("comment", False, True) == MessageType.COMMENT
    assert MessageType.from_odoo("comment", True, False) == MessageType.NOTE


def test_task_model():
    task = Task(
        id=1,
        name="Test",
        state=TaskState.IN_PROGRESS,
        priority=TaskPriority.NORMAL,
        stage=Stage(id=1, name="New"),
        project=Project(id=1, name="Test Project"),
    )
    assert task.id == 1
    assert task.is_closed is False
    assert task.timesheets == []
    assert task.messages == []
