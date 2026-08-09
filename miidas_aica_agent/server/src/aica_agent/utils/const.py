from typing import Final
import re

LOGGER_PREFIX: Final[str] = "aica_agent"

API_PREFIX: Final[str] = "/aica/agent"

APPLY_POSITION_IDS_KEY: Final[str] = "PositionIDs"

MAINTENANCE_MESSAGE: Final[str] = (
    "システムメンテナンスが開始されました。\n"
    "ご迷惑をおかけしますが、しばらく経ってから再度お試しください。"
)

RATE_LIMIT_EXCEEDED_MESSAGE: Final[str] = (
    "ただいまサイトが大変混み合っております。\n"
    "ご迷惑をおかけしますが、時間をあけて再度アクセスしてください。"
)

# ユーザープロフィールバリデーション用
PHONE_PATTERN: Final[re.Pattern] = re.compile(r"^0[0-9]{9,10}$")
PASSWORD_PATTERN: Final[re.Pattern] = re.compile(
    r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,16}$"
)

SESSION_START_MESSAGE: Final[str] = "会話開始"

INITIAL_MENU_WORKFLOW_ID: Final[str] = "initial_menu"
JOB_MATCH_DIAGNOSIS_WORKFLOW_ID: Final[str] = "job_match_diagnosis"
POSITION_CHANGE_ANALYZE_WORKFLOW_ID: Final[str] = "position_change_analyze"

POSITION_SEARCH_FAKE_RESULT: Final[str] = (
    "ポジション検索が実行されました。"
    "ユーザーには別の手段で求人の検索結果を見せていますが、"
    "ユーザーから条件変更や再度見たいとの要望があれば、"
    "検索条件の差異に関わらず、再度このツールを実行してください。"
)


def format_position_search_fake_result(count: int) -> str:
    """ポジション検索のフェイク結果メッセージを生成する（件数付き）。"""
    return (
        f"{count}件の求人が見つかりました。"
        "ユーザーには別の手段で求人の検索結果を見せていますが、"
        "ユーザーから条件変更や再度見たいとの要望があれば、"
        "検索条件の差異に関わらず、再度このツールを実行してください。"
    )


MAIN_CHAT_KEY: Final[str] = "MAIN"
