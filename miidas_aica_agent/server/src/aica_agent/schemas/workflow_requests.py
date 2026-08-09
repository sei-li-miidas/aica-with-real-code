from typing import Any
from pydantic import BaseModel, Field


class JSONJobMatchDiagnosisSearchOccupationsRequest(BaseModel):
    """適職診断ワークフローの職種検索APIリクエストモデル。"""

    answers: dict[str, Any] = Field(..., description="ステップごとの回答辞書")


class JSONPositionChangeAnalyzeGenerateSummaryRequest(BaseModel):
    """転職理由診断ワークフローの転職軸要約生成APIリクエストモデル。"""

    answers: dict[str, Any] = Field(..., description="ステップごとの回答辞書")
