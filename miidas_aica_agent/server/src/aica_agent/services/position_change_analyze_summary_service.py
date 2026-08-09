import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from services.base_service import BaseService
from utils.enum import LLMMessageRole


class PositionChangeAnalyzeSummaryService(BaseService):
    def __init__(self, model_list: list[dict[str, Any]]) -> None:
        super().__init__()
        summary_models = [
            model
            for model in model_list
            if "position_change_analyze_summary" in model["use_for"]
        ]
        if not summary_models:
            raise ValueError(
                "転職理由診断要約用の position_change_analyze_summary モデルが定義されていません"
            )
        if len(summary_models) > 1:
            self.logger.warning("複数の転職理由診断要約モデルが定義されています")

        self._model = summary_models[0]
        if "model" not in self._model:
            raise ValueError("position_change_analyze_summary モデル名が定義されていません")

        prompt_path = (
            Path(__file__).resolve().parent.parent
            / "files"
            / "prompts"
            / "8_PositionChangeAnalyzeSummary.txt"
        )
        schema_path = (
            Path(__file__).resolve().parent.parent
            / "files"
            / "prompts"
            / "8_PositionChangeAnalyzeSummary.schema.json"
        )
        self._prompt_template = prompt_path.read_text(encoding="utf-8")
        self._schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self._openai_client = AsyncOpenAI()

    async def generate_summary(self, answers_text: str) -> dict:
        """step1〜4の回答を受け取り転職軸の要約を生成する。失敗時は例外を raise する。"""
        system_message = self._prompt_template.replace("{answers_text}", answers_text)

        model_name = self._model["model"]
        model_settings = self._model.get("model_settings", {})

        response = await self._openai_client.responses.create(
            model=model_name,
            input=[
                {
                    "type": "message",
                    "role": LLMMessageRole.DEVELOPER,
                    "content": [{"type": "input_text", "text": system_message}],
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "position_change_analyze_summary",
                    "strict": True,
                    "schema": self._schema,
                }
            },
            **model_settings,
        )

        if not response.output_text:
            raise RuntimeError("転職理由診断要約の生成に失敗しました: 応答が空です")

        return json.loads(response.output_text)
