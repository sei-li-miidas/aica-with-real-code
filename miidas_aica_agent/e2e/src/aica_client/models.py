from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PageName(StrEnum):
    NONE = ""
    CHAT = "Chat"
    POSITION_DETAIL = "PositionDetail"
    PROFILE_BASIC_INFO = "BasicInfo"
    PROFILE_CARRER = "Carrer"
    PROFILE_EDUCATION = "Education"
    PROFILE_WILL = "Will"


class ChatRequestType(StrEnum):
    START = "start"
    CHAT = "chat"
    RESTART_CHAT = "restart_chat"
    SUMMARIZE_POSITION = "summarize_position"
    JOB_TYPES_SELECTED = "job_types_selected"
    JOB_TYPES_CLEAR = "job_types_clear"
    WORKFLOW_ANSWERS_SUBMITTED = "workflow_answers_submitted"
    WORKFLOW_CANCELLED = "workflow_cancelled"


class ChatResponseType(StrEnum):
    MESSAGE = "message"
    POSITION_SEARCH_RESULT = "position_search_result"
    POSITION_SEARCH_LINK = "position_search_link"
    JOBTYPE_SEARCH_RESULT = "jobtype_search_result"
    WORKFLOW = "workflow"
    ERROR = "error"
    END = "end"


class LLMMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    DEVELOPER = "developer"
    TOOL = "tool"


class SessionStatus(IntEnum):
    ERROR = -1
    CHATTING = 10
    REGISTERING = 100
    APPLYING = 110
    REGISTERED = 200
    APPLIED = 210


class FinishPolicy(StrEnum):
    MAX_ROUNDS = "MAX_ROUNDS"
    APPLY_FINISHED = "APPLY_FINISHED"
    EITHER = "EITHER"


class PositionSelectionStrategy(StrEnum):
    FIRST = "first"
    RANDOM = "random"


class ApplyMode(StrEnum):
    POSITION = "position"
    REGISTRATION_ONLY = "registration_only"
    NONE = "none"


class ChatRequestPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    request_type: ChatRequestType = ChatRequestType.CHAT
    current_page: PageName
    previous_page: PageName | None = None
    message: str | None = None
    position_id: str | None = None
    current_message_id: str | None = None
    is_voice: bool | None = None

    def to_ws_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        return {
            key: value
            for key, value in payload.items()
            if not (isinstance(value, str) and value == "")
        }


class ChatStreamResponseModel(BaseModel):
    session_id: str
    session_status: int | None = None
    request_type: ChatRequestType | None = None
    response_type: ChatResponseType
    role: LLMMessageRole | None = None
    message_id: str
    message: str
    position_id: str | None = None
    is_maintenance: bool = False


class HistoryRecord(BaseModel):
    Role: str | None = None
    Type: str | None = None
    MessageID: str
    Message: Any


class AddressSeed(BaseModel):
    prefecture: str
    city: str


class BasicInfoSeed(BaseModel):
    last_name: str
    first_name: str
    last_name_kana: str
    first_name_kana: str
    email: str
    phone_no: str
    gender: int
    password: str
    birth_year: int
    birth_month: int
    first_language: int = 91
    driver_licence: int = 1
    residence: AddressSeed


class EducationSeed(BaseModel):
    school_type: int
    graduation_year: int
    english_level: int
    school_name: str | None = None
    department_name: str | None = None
    department_id: int | None = None
    professional_training_college_category_name: str | None = None
    professional_training_college_category_id: int | None = None


class CareerSeed(BaseModel):
    exp_company_num: int
    management_exp_term: int
    management_people_num: int | None = None
    company_name: str | None = None
    industry_keyword: str | None = None
    industry_id: int | None = None
    industry_name: str | None = None
    employee_num: int | None = None
    employment_type: int | None = None
    employment_post: int | None = None
    job_type_keyword: str | None = None
    job_type_id: int | None = None
    job_type_name: str | None = None
    job_type_exp_term: int | None = None
    all_career_job_type_exp_term: int | None = None
    income: int | None = None
    join_year: int | None = None
    join_month: int | None = None
    retire_year: int | None = None
    retire_month: int | None = None


class WillSeed(BaseModel):
    will_income: int
    work_addresses: list[AddressSeed]
    will_remote_work: bool = True
    will_job_change_period: int
    will_job_type_keywords: list[str]
    is_rpo_agreement: bool = True


class RunHints(BaseModel):
    auto_apply_position: bool = True
    apply_mode: ApplyMode = ApplyMode.POSITION
    position_selection: PositionSelectionStrategy = PositionSelectionStrategy.FIRST
    position_detail_turns: int = 2


class HeadlessPersonaSeed(BaseModel):
    terms_of_use_agreed: bool = True
    basic_info: BasicInfoSeed
    education: EducationSeed
    career: CareerSeed
    will: WillSeed
    run_hints: RunHints = Field(default_factory=RunHints)


@dataclass
class ResponseExchange:
    events: list[ChatStreamResponseModel]
    first_msg_duration: float
    total_duration: float

    @property
    def last_event(self) -> ChatStreamResponseModel:
        return self.events[-1]

    @property
    def response_type(self) -> ChatResponseType:
        for event in self.events:
            if event.response_type not in (
                ChatResponseType.END,
                ChatResponseType.ERROR,
            ):
                return event.response_type
        return self.last_event.response_type

    @property
    def message(self) -> str:
        return "".join(
            event.message
            for event in self.events
            if event.response_type not in (ChatResponseType.END,)
        )

    @property
    def session_id(self) -> str:
        return self.last_event.session_id

    @property
    def session_status(self) -> SessionStatus:
        status = self.last_event.session_status
        if status is None:
            return SessionStatus.CHATTING
        try:
            return SessionStatus(status)
        except ValueError:
            return SessionStatus.CHATTING

    @property
    def request_type(self) -> ChatRequestType | None:
        return self.last_event.request_type

    @property
    def position_id(self) -> str | None:
        return self.last_event.position_id

    @property
    def is_maintenance(self) -> bool:
        return any(event.is_maintenance for event in self.events)


@dataclass
class HeadlessState:
    session_id: str = ""
    session_status: SessionStatus = SessionStatus.CHATTING
    current_page: PageName = PageName.CHAT
    main_history: list[dict[str, Any]] = field(default_factory=list)
    position_histories: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    positions: dict[str, dict[str, Any]] = field(default_factory=dict)
    search_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    search_links: dict[str, dict[str, Any]] = field(default_factory=dict)
    search_ready: bool = False
    jobtype_groups: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    active_tool_name: str = ""
    current_search_filters: dict[str, Any] = field(default_factory=dict)
    salary: int = 0
    position_keyword: str = ""
    residence: str = ""
    residence_prefecture_name: str = ""
    residence_city_name: str = ""
    commuting_areas: list[dict[str, Any]] = field(default_factory=list)
    work_locations: list[dict[str, Any]] = field(default_factory=list)
    remote_work_possible: bool | None = None
    other_filters: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    selected_filter_options: dict[str, dict[str, list[str]]] = field(
        default_factory=dict
    )
    same_other_filter_jobtypes: dict[str, list[str]] = field(default_factory=dict)
    applied_positions: set[str] = field(default_factory=set)
    loaded_profile_sections: set[str] = field(default_factory=set)
    saved_profile: dict[str, Any] | None = None
    terms_of_use_agreed: bool = True
    last_agent_message: str = ""
    pending_position_search_result: dict[str, Any] | None = None
    pending_position_search_link: dict[str, Any] | None = None
    pending_jobtype_search: dict[str, Any] | None = None
    pending_workflow: dict[str, Any] | None = None
    active_position_id: str | None = None
    main_history_restored: bool = False
    restored_position_histories: set[str] = field(default_factory=set)
    reconnect_count: int = 0
    registration_finished: bool = False
    application_finished: bool = False
    search_flow_completed: bool = False
    round_count: int = 0
    finish_reason: str = ""


@dataclass
class FilterStateSnapshot:
    active_tool_name: str
    jobtype_groups: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    salary: int = 0
    position_keyword: str = ""
    residence_prefecture_name: str = ""
    residence_city_name: str = ""
    commuting_areas: list[dict[str, Any]] = field(default_factory=list)
    work_locations: list[dict[str, Any]] = field(default_factory=list)
    remote_work_possible: bool | None = None
    other_filters: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    selected_filter_options: dict[str, dict[str, list[str]]] = field(
        default_factory=dict
    )
    same_other_filter_jobtypes: dict[str, list[str]] = field(default_factory=dict)
