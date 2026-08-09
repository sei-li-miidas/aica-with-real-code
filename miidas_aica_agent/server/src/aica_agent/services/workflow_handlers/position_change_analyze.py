from domain.entities.workflow_definition import SelectionType, WorkflowDefinition
from services.llm_service import AgentName
from services.position_change_analyze_summary_service import PositionChangeAnalyzeSummaryService
from services.workflow_handlers.base import WorkflowHandler, WorkflowPostProcessingResult
from utils.const import JOB_MATCH_DIAGNOSIS_WORKFLOW_ID
from utils.enum import LLMMessageRole


class PositionChangeAnalyzeHandler(WorkflowHandler):
    """転職理由診断ワークフローハンドラ"""

    SUMMARY_STEP_IDS = ["1", "2", "3", "4"]

    def __init__(
        self,
        workflow_id: str,
        position_change_analyze_summary_svc: PositionChangeAnalyzeSummaryService,
        definition: WorkflowDefinition,
    ):
        super().__init__(workflow_id, definition)
        self._summary_svc = position_change_analyze_summary_svc

    def get_validated_answers_for_summary(self, raw_answers: dict) -> dict[str, list[dict]]:
        """step1〜4のみ抽出してバリデーションした構造化回答を返す。"""
        structured_answers = {}
        for step_id in self.SUMMARY_STEP_IDS:
            if step_id not in raw_answers:
                raise ValueError(
                    f"転職理由診断要約に必要なステップ {step_id} の回答がありません"
                )
            values = raw_answers[step_id]
            if not isinstance(values, list):
                raise ValueError(
                    f"ワークフローID {self.workflow_id}、ステップ{step_id}の回答がリスト形式ではありません"
                )
            structured_answers[step_id] = self.extract_options_by_step(step_id, values)
        return structured_answers

    def build_history_to_save(self, structured_answers: dict[str, list[dict]], extra: dict | None = None) -> list[dict]:
        history = []
        for step_id, options in structured_answers.items():
            question = self.get_question_prompt(step_id)
            step = self._get_step(step_id)
            if step.selection_type == SelectionType.MULTIPLE:
                user_answer = self._format_as_numbered_list(options)
            else:
                _, user_answer = self.get_conversation_pair_from_options(step_id, options)
            history.append({"role": LLMMessageRole.ASSISTANT, "content": question})
            history.append({"role": LLMMessageRole.USER, "content": user_answer if user_answer is not None else "選択なし"})

        extra = extra or {}
        summary = extra.get("summary")
        explanation = extra.get("explanation")
        # 転職軸の要約API で返却する "keywords"（リスト）とは別物。フロント側で keywords を元に
        # 文章化した上で "keyword_suggestion"（文字列）として送られてくる。
        keyword_suggestion = extra.get("keyword_suggestion")

        sections = []
        if summary:
            sections.append(f"【あなたの転職軸】\n{summary}")
        if explanation:
            sections.append(f"【解説】\n{explanation}")
        if keyword_suggestion:
            sections.append(f"【求人を探すポイント】\n{keyword_suggestion}")

        if sections:
            step5_prompt = self.get_question_prompt("5")
            for entry in history:
                if entry["role"] == LLMMessageRole.ASSISTANT and entry["content"] == step5_prompt:
                    entry["content"] = entry["content"] + "\n\n" + "\n\n".join(sections)
                    # message_id に "summary" suffix を付与してもらう（workflow_chat_handler が
                    # message_id = f"wf_{workflow_id}_summary_{batch_id}_{index}" を生成する）。
                    # これにより、転職軸の要約は session_id と message_id の前方一致検索
                    # （message_id LIKE f"wf_{self.workflow_id}_summary_%"）でチャット履歴から抽出できる。
                    entry["message_id_suffix"] = "summary"
                    break
        return history

    def summarize_answers(self, structured_answers: dict[str, list[dict]]) -> str:
        """回答内容を要約したテキストを生成する。複数選択は選択順を優先順位として番号付きで表す。"""
        summary_items = []
        for step_id, options in structured_answers.items():
            question = self.get_question(step_id)
            step = self._get_step(step_id)
            if step.selection_type == SelectionType.MULTIPLE:
                answer_text = self._format_as_numbered_list(options)
            else:
                _, answer_text = self.get_conversation_pair_from_options(step_id, options)
                answer_text = answer_text if answer_text is not None else "選択なし"
            summary_items.append(f"- {question}:\n{answer_text}")

        return "\n\n".join(summary_items)

    def _format_as_numbered_list(self, options: list[dict]) -> str:
        if not options:
            return "選択なし"
        items = []
        for i, opt in enumerate(options, 1):
            label = opt.get("label", "")
            text = opt.get("text")
            if text:
                label = f"{label}\n{text}"
            items.append(f"{i}. {label}")
        return "\n\n".join(items)

    async def generate_llm_summary(self, structured_answers: dict[str, list[dict]]) -> dict:
        """step1〜4の構造化回答を人間が読めるテキストに変換し、LLM要約を生成して返す。"""
        answers_text = self.summarize_answers(structured_answers)
        return await self._summary_svc.generate_summary(answers_text)

    async def perform_post_processing(
        self, structured_answers: dict[str, list[dict]]
    ) -> WorkflowPostProcessingResult:
        """step5の選択値に応じて次エージェント・ワークフローを決定する。"""
        step5_options = structured_answers.get("5", [])
        selected_value = step5_options[0].get("value") if step5_options else None

        if selected_value == 1:
            return WorkflowPostProcessingResult(
                message=(
                    "ユーザーが転職理由診断を完了し、「求人を探す」を選択しました。"
                    "ユーザーの転職軸を踏まえて、求人検索に向けたヒアリングを開始してください。"
                    "また、必要に応じて求人検索のポイントを検索条件に含めることを提案してください。"
                ),
                next_agent_name=AgentName.CAREER_ADVISOR,
            )

        if selected_value == 2:
            return WorkflowPostProcessingResult(
                message="",
                next_agent_name=AgentName.CAREER_ADVISOR,
                next_workflow_id=JOB_MATCH_DIAGNOSIS_WORKFLOW_ID,
            )

        if selected_value == 3:
            return WorkflowPostProcessingResult(
                message=(
                    "ユーザーが転職理由診断を完了し、「会員登録して転職活動を始める」を選択しました。"
                    "`form_registration` を実行し、会員登録フォームを表示してください。"
                ),
                next_agent_name=AgentName.CAREER_ADVISOR,
            )

        if selected_value == 4:
            free_text = step5_options[0].get("text", "") if step5_options else ""
            message = "ユーザーが転職理由診断を完了しました。"
            if free_text:
                message += f"\nユーザーが「その他」として次のように入力しました：「{free_text}」\nこの内容を踏まえてフォローアップ会話を行ってください。"
            else:
                message += "\nユーザーが「その他」を選択しました。ご要望を確認してください。"
            return WorkflowPostProcessingResult(
                message=message,
                next_agent_name=AgentName.POSITION_CHANGE_ANALYZE,
            )

        raise ValueError(f"転職理由診断step5の不明な選択値: {selected_value}")
