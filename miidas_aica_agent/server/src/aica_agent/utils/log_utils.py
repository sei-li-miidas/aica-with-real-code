"""
ログに、セッションIDとリクエストIDを出力するため準備
"""

import logging
import os
from typing import Any, Final, Optional
from contextvars import ContextVar
from fastapi import Request

session_id_var: ContextVar[Optional[str]] = ContextVar("Session ID", default=None)
request_id_var: ContextVar[Optional[str]] = ContextVar("Request ID", default=None)

old_factory = logging.getLogRecordFactory()

LOG_MASK: Final[str] = "*****"

# Use set for O(1) lookup instead of list O(n) lookup
KEY_TO_MASK: Final[frozenset[str]] = frozenset(
    {
        "lastname",
        "firstname",
        "lastnamekana",
        "firstnamekana",
        "companyname",
        "email",
        "phoneno",
        "password",
        "last_name",
        "first_name",
        "last_name_kana",
        "first_name_kana",
        "company_name",
        "phone_no",
    }
)


def mask_log_payload(payload: Any) -> Any:
    """機密データをマスクする"""
    if hasattr(payload, "model_dump"):
        # Pydantic BaseModel
        try:
            payload = payload.model_dump()
        except AttributeError:
            # 辞書化に失敗した場合はそのまま続行
            pass

    if isinstance(payload, dict):
        result = {}
        for key, value in payload.items():
            if key.lower() in KEY_TO_MASK:
                result[key] = LOG_MASK
            elif isinstance(value, dict):
                result[key] = mask_log_payload(value)
            elif isinstance(value, (list, tuple)):
                result[key] = type(value)(mask_log_payload(item) for item in value)
            else:
                result[key] = value
        return result

    if isinstance(payload, (list, tuple)):
        return type(payload)(mask_log_payload(item) for item in payload)

    return payload


def record_factory(*args, **kwargs):
    """セッションID、リクエストID追加と機密データマスク処理を行うログレコードファクトリ"""
    record = old_factory(*args, **kwargs)
    record.session_id = session_id_var.get()
    record.request_id = request_id_var.get()
    record.caller = record.pathname + ":" + str(record.lineno)
    if not os.environ.get("NOT_MASK_LOG_PAYLOAD") and record.args:
        record.args = mask_log_payload(record.args)
    return record


def set_session_id(session_id: Optional[str]) -> None:
    session_id_var.set(session_id)


def get_session_id() -> str | None:
    return session_id_var.get()


def clear_session_id() -> None:
    session_id_var.set(None)


def set_request_id(request_id: Optional[str]) -> None:
    request_id_var.set(request_id)


def get_request_id() -> str | None:
    return request_id_var.get()


def clear_request_id() -> None:
    request_id_var.set(None)


def add_tracing_info(request: Request):
    session_id = request.headers.get("X-SESSION-ID")
    set_session_id(session_id)

    request_id = request.headers.get("X-REQUEST-ID")
    set_request_id(request_id)


def clear_tracing_info():
    clear_session_id()
    clear_request_id()
