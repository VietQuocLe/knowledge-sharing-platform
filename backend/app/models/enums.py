from enum import Enum


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class ResourceType(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    PPTX = "PPTX"
    IMAGE = "IMAGE"
    OTHER = "OTHER"


class VisibilityEnum(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class ResourceStatus(str, Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"