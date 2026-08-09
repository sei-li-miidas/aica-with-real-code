from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from utils.const import LOGGER_PREFIX
from utils.enum import LLMMessageRole
from domain.entities.workflow_definition import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowOptionItem,
    WorkflowCategoryOption,
    SelectionType,
)


@dataclass
class WorkflowPostProcessingResult:
    """ワークフロー後処理の結果を表すデータクラス"""
    message: str
    selected_jobtypes: list[str] | None = None
    next_agent_name: str | None = None
    next_workflow_id: str | None = None


class WorkflowHandler(ABC):
    DEFAULT_CONVERSATION_DELIMITER = "\n\n"

    def __init__(self, workflow_id: str, definition: WorkflowDefinition):
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self.workflow_id = workflow_id
        self._definition = definition

    def get_validated_structured_answers(self, raw_answers: dict) -> dict[str, list[dict]]:
        """バリデーション済みの構造化された回答を返す"""
        return self._get_structured_answers(raw_answers)

    def _get_structured_answers(self, raw_answers: dict) -> dict[str, list[dict]]:
        """
        ワークフロー定義に存在するユーザーの回答を、
        辞書形式（キー: ステップID、値: 有効な選択肢オブジェクトのリスト）で抽出する。
        """
        structured_answers = {}
        for step_id, values in raw_answers.items():
            step_id_str = str(step_id)
            if not isinstance(values, list):
                raise ValueError(f"ワークフローID {self.workflow_id}、ステップ{step_id_str}の回答がリスト形式ではありません")

            valid_options = self.extract_options_by_step(step_id_str, values)
            if valid_options:
                structured_answers[step_id_str] = valid_options

        return structured_answers

    def extract_options_by_step(self, step_id: str | int, raw_values: list) -> list[dict]:
        """指定されたステップIDの回答リストから、定義に存在する選択肢を抽出して構造化する"""
        step = self._get_step(step_id)
        option_map = {}
        for opt in step.options:
            if isinstance(opt, WorkflowOptionItem):
                option_map[str(opt.value)] = opt
            elif isinstance(opt, WorkflowCategoryOption):
                for item in opt.items:
                    option_map[str(item.value)] = item

        valid_options = []
        for item in raw_values:
            if not isinstance(item, dict):
                raise ValueError(
                    f"ワークフロー回答の形式エラー: ワークフローID {self.workflow_id}、ステップID {step_id} の回答が辞書形式ではありません: {item}"
                )

            value = str(item.get("value"))
            match = option_map.get(value)
            if match:
                # モデルから辞書に変換し、自由入力がある場合は追加
                final_opt = match.model_dump(by_alias=True)
                # 自由入力が許可されている場合のみ text を含める
                if "text" in item and match.allow_free_text:
                    final_opt["text"] = item["text"]
                valid_options.append(final_opt)
            else:
                self._logger.warning(
                    "ワークフロー回答のバリデーションエラー: ワークフローID %s、ステップID %s に値 '%s' が定義されていません",
                    self.workflow_id,
                    step_id,
                    value,
                )

        # 単一選択制約のチェック: selection_type が single の場合に複数回答を拒否
        if step.selection_type == SelectionType.SINGLE and len(valid_options) > 1:
            raise ValueError(
                f"ワークフローID {self.workflow_id}、ステップID {step_id} は単一選択ですが、複数の回答が送信されました"
            )

        return valid_options

    def _get_step(self, step_id: int | str) -> WorkflowStep:
        """ステップIDに一致するステップオブジェクトを取得する"""
        for step in self._definition.steps:
            if str(step.id) == str(step_id):
                return step

        raise ValueError(f"ステップID `{step_id}` がワークフロー `{self.workflow_id}` に存在しません")

    def get_question(self, step_id: int | str) -> str:
        """ステップIDから質問文を取得する"""
        return self._get_step(step_id).question

    def get_question_prompt(self, step_id: int | str) -> str:
        """ステップIDからシステム側の発言用プロンプトを取得する"""
        return self._get_step(step_id).question_prompt

    def get_conversation_pair_from_options(
        self,
        step_id: int | str,
        valid_options: list[dict],
        delimiter: str | None = None
    ) -> tuple[str, str | None]:
        """システムの発言と、ユーザーの回答ラベルのペアを返す。有効な回答がない場合は回答としてNoneを返す"""
        question = self.get_question_prompt(step_id)
        if not valid_options:
            return question, None

        if delimiter is None:
            delimiter = self.DEFAULT_CONVERSATION_DELIMITER

        labels = []
        for opt in valid_options:
            label = opt.get("label")
            text = opt.get("text")
            if text:
                label = f"{label}\n{text}"
            labels.append(label)

        user_answer = delimiter.join(labels)
        return question, user_answer

    def summarize_answers(self, structured_answers: dict[str, list[dict]]) -> str:
        """回答内容を要約したテキストを生成する"""
        summary_items = []
        for step_id, options in structured_answers.items():
            question = self.get_question(step_id)
            labels = []
            for opt in options:
                label = opt["label"]
                text = opt.get("text")
                if text:
                    label = f"{label}（{text}）"
                labels.append(label)

            joined_labels = "、".join(labels) if labels else "選択なし"
            summary_items.append(f"- {question}: {joined_labels}")

        return "\n".join(summary_items)

    def build_history_to_save(self, structured_answers: dict[str, list[dict]], extra: dict | None = None) -> list[dict]:
        """ワークフローの質問・回答ペアからチャット履歴保存用リストを生成する"""
        history = []
        for step_id, options in structured_answers.items():
            q, a = self.get_conversation_pair_from_options(step_id, options)
            history.append({"role": LLMMessageRole.ASSISTANT, "content": q})
            history.append({"role": LLMMessageRole.USER, "content": a if a is not None else "選択なし"})
        return history

    @abstractmethod
    async def perform_post_processing(self, structured_answers: dict[str, list[dict]]) -> WorkflowPostProcessingResult:
        """
        回答保存後の後処理を実行し、結果を返す。
        selected_jobtypes に値がある場合、呼び出し元が求人検索ツールをエージェントに追加する。
        """
        pass
