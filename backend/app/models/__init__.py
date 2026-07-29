from app.models.base import Base

from app.models.user import User
from app.models.department import Department
from app.models.subject import Subject
from app.models.learning_resource import LearningResource

__all__ = [
    "Base",
    "User",
    "Department",
    "Subject",
    "LearningResource",
]