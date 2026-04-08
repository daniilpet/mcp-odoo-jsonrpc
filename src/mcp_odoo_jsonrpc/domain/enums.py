import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class TaskState(StrEnum):
    IN_PROGRESS = "01_in_progress"
    CHANGES_REQUESTED = "02_changes_requested"
    APPROVED = "03_approved"
    CANCELLED = "04_cancelled"
    WAITING = "04_waiting_normal"
    DONE = "1_done"
    CANCELED = "1_canceled"

    @classmethod
    def from_odoo(cls, value: str) -> "TaskState":
        for member in cls:
            if member.value == value:
                return member
        logger.warning("Unknown TaskState: %r — defaulting to IN_PROGRESS", value)
        return cls.IN_PROGRESS


class TaskPriority(StrEnum):
    NORMAL = "0"
    URGENT = "1"

    @classmethod
    def from_odoo(cls, value: str) -> "TaskPriority":
        for member in cls:
            if member.value == value:
                return member
        logger.warning("Unknown TaskPriority: %r — defaulting to NORMAL", value)
        return cls.NORMAL


class MessageType(StrEnum):
    NOTIFICATION = "notification"
    COMMENT = "comment"
    NOTE = "note"

    @classmethod
    def from_odoo(cls, message_type: str, is_note: bool, is_discussion: bool) -> "MessageType":
        if message_type == "notification":
            return cls.NOTIFICATION
        if message_type == "comment" and is_note and not is_discussion:
            return cls.NOTE
        if message_type == "comment" and is_discussion:
            return cls.COMMENT
        logger.warning(
            "Unknown MessageType: type=%r, is_note=%s, is_discussion=%s"
            " — defaulting to NOTIFICATION",
            message_type,
            is_note,
            is_discussion,
        )
        return cls.NOTIFICATION


class WikiPageType(StrEnum):
    CATEGORY = "category"
    CONTENT = "content"

    @classmethod
    def from_odoo(cls, value: str) -> "WikiPageType":
        for member in cls:
            if member.value == value:
                return member
        logger.warning("Unknown WikiPageType: %r — defaulting to CONTENT", value)
        return cls.CONTENT
