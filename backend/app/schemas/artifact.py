from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.models.enums import ArtifactType


class QuizOption(BaseModel):
    key: Literal["A", "B", "C", "D"]
    text: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[QuizOption] = Field(..., min_length=4, max_length=4)
    correct_answer: Literal["A", "B", "C", "D"]
    explanation: str

    @model_validator(mode="after")
    def validate_options_keys(self) -> "QuizQuestion":
        keys = {opt.key for opt in self.options}
        if keys != {"A", "B", "C", "D"}:
            raise ValueError("Quiz options must contain exactly the keys: A, B, C, D")
        return self


class QuizContentPayload(BaseModel):
    title: str
    questions: List[QuizQuestion]


class QuizGenerateRequest(BaseModel):
    selected_asset_ids: List[int] = Field(..., min_length=1)
    num_questions: int = Field(default=5, ge=1, le=20)


class ArtifactSummaryResponse(BaseModel):
    id: int
    notebook_id: int
    user_id: int
    title: str
    artifact_type: ArtifactType
    metadata_: dict = Field(default_factory=dict, alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_metadata(cls, data: any) -> any:
        if not isinstance(data, dict) and hasattr(data, "metadata_"):
            res = {
                "id": data.id,
                "notebook_id": data.notebook_id,
                "user_id": data.user_id,
                "title": data.title,
                "artifact_type": data.artifact_type,
                "metadata": data.metadata_,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
            if "content" in cls.model_fields and hasattr(data, "content"):
                res["content"] = data.content
            return res
        return data

    @computed_field
    def total_items(self) -> int:
        return self.metadata_.get("num_questions", 0)


class ArtifactDetailResponse(ArtifactSummaryResponse):
    content: QuizContentPayload

    @computed_field
    def total_items(self) -> int:
        if self.content and self.content.questions:
            return len(self.content.questions)
        return 0
