from pydantic import BaseModel, Field, ConfigDict
from enum import StrEnum


class SelectionType(StrEnum):
    SINGLE = "single"
    MULTIPLE = "multiple"


class DisplayType(StrEnum):
    MODAL = "modal"
    INLINE = "inline"


class WorkflowOptionItem(BaseModel):
    label: str
    value: int
    allow_free_text: bool = Field(alias="allowFreeText")
    job_nature: str | None = Field(None, alias="jobNature")
    description: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class WorkflowCategoryOption(BaseModel):
    id: str
    name: str
    items: list[WorkflowOptionItem]


class WorkflowStep(BaseModel):
    id: int
    question: str # LLMへの指示・ユーザー向けの質問文
    question_prompt: str = Field(alias="questionPrompt") # チャット履歴として残す際にLLMが発話しているように見せるための自然な文章（こちらをユーザー向けに使用する場合もあり）
    selection_type: SelectionType = Field(alias="selectionType")
    options: list[WorkflowCategoryOption] | list[WorkflowOptionItem]

    model_config = ConfigDict(populate_by_name=True)


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    display_type: DisplayType = Field(alias="displayType")
    steps: list[WorkflowStep] = Field(min_length=1)

    model_config = ConfigDict(populate_by_name=True)
