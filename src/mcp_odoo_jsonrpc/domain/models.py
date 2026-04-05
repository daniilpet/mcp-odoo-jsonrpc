from datetime import date, datetime

from pydantic import BaseModel, Field

from mcp_odoo_jsonrpc.domain.enums import MessageType, TaskPriority, TaskState


class Project(BaseModel, frozen=True):
    id: int
    name: str


class Stage(BaseModel, frozen=True):
    id: int
    name: str
    folded: bool = False


class User(BaseModel, frozen=True):
    id: int
    name: str


class Partner(BaseModel, frozen=True):
    id: int
    name: str


class Tag(BaseModel, frozen=True):
    id: int
    name: str
    color: int = 0


class Milestone(BaseModel, frozen=True):
    id: int
    name: str


class TaskRef(BaseModel, frozen=True):
    id: int
    name: str


class Timesheet(BaseModel, frozen=True):
    id: int | None = None
    date: date
    employee: User
    description: str
    hours: float
    readonly: bool = False


class FieldChange(BaseModel, frozen=True):
    field: str
    field_name: str
    old_value: str
    new_value: str


class Message(BaseModel, frozen=True):
    id: int
    author: User | None = None
    body: str
    date: datetime
    type: MessageType
    tracking: list[FieldChange] = Field(default_factory=list)


class Attachment(BaseModel, frozen=True):
    id: int
    name: str
    mimetype: str
    size: int
    access_token: str


class Task(BaseModel, frozen=True):
    id: int
    name: str
    description: str | None = None
    state: TaskState
    priority: TaskPriority
    stage: Stage
    project: Project
    parent: TaskRef | None = None
    assignees: list[User] = Field(default_factory=list)
    partner: Partner | None = None
    tags: list[Tag] = Field(default_factory=list)
    milestone: Milestone | None = None
    deadline: date | None = None
    is_closed: bool = False
    allocated_hours: float = 0.0
    effective_hours: float = 0.0
    remaining_hours: float = 0.0
    progress: float = 0.0
    subtask_count: int = 0
    closed_subtask_count: int = 0
    duration_tracking: dict[int, int] = Field(default_factory=dict)
    timesheets: list[Timesheet] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
