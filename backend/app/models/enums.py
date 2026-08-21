from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    PREMIUM_USER = "PREMIUM_USER"
    ADMIN = "ADMIN"


class ResourceType(str, Enum):
    EXAM = "EXAM"
    SLIDE = "SLIDE"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    LINK = "LINK"
    AI_ARTIFACT = "AI_ARTIFACT"


class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLIC = "PUBLIC"
    DELETED = "DELETED"
