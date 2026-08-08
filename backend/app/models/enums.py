from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    PREMIUM_USER = "PREMIUM_USER"
    ADMIN = "ADMIN"


class ResourceType(str, Enum):
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    LINK = "LINK"
    AI_ARTIFACT = "AI_ARTIFACT"


class VisibilityEnum(str, Enum):
    PRIVATE = "PRIVATE"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLIC = "PUBLIC"


class ResourceStatus(str, Enum):
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    DELETED = "DELETED"