from enum import Enum


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class ResourceType(str, Enum):
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    LINK = "LINK"
    AI_ARTIFACT = "AI_ARTIFACT"


class VisibilityEnum(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class ResourceStatus(str, Enum):
    PUBLISHED = "PUBLISHED"
    DELETED = "DELETED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"