from domain.entities.workflow_definition import WorkflowDefinition
from services.llm_service import AgentName
from services.workflow_handlers.base import WorkflowHandler, WorkflowPostProcessingResult
from utils.const import JOB_MATCH_DIAGNOSIS_WORKFLOW_ID, POSITION_CHANGE_ANALYZE_WORKFLOW_ID, SESSION_START_MESSAGE
from utils.enum import LLMMessageRole


class InitialMenuHandler(WorkflowHandler):
    """
    初期メニューワークフローハンドラ
    ユーザーの選択に応じて起動するエージェントと次ワークフローを決定する
    """

    def __init__(self, workflow_id: str, definition: WorkflowDefinition):
        super().__init__(workflow_id, definition)

    def build_history_to_save(self, structured_answers: dict[str, list[dict]], extra: dict | None = None) -> list[dict]:
        history = [{"role": LLMMessageRole.DEVELOPER, "content": SESSION_START_MESSAGE}]
        history.extend(super().build_history_to_save(structured_answers))
        return history

    async def perform_post_processing(
        self, structured_answers: dict[str, list[dict]]
    ) -> WorkflowPostProcessingResult:
        step1_options = structured_answers.get("1", [])
        selected_value = step1_options[0].get("value") if step1_options else None

        if selected_value == 1:
            return WorkflowPostProcessingResult(
                message=(
                    "ユーザーが「求人検索」を選択しました。"
                    "求人検索に向けて、希望職種・希望年収・希望勤務地のヒアリングを開始してください。"
                ),
                next_agent_name=AgentName.CAREER_ADVISOR,
            )
        elif selected_value == 2:
            return WorkflowPostProcessingResult(
                message="",
                next_agent_name=AgentName.CAREER_ADVISOR,
                next_workflow_id=JOB_MATCH_DIAGNOSIS_WORKFLOW_ID,
            )
        elif selected_value == 3:
            return WorkflowPostProcessingResult(
                message="",
                next_agent_name=AgentName.POSITION_CHANGE_ANALYZE,
                next_workflow_id=POSITION_CHANGE_ANALYZE_WORKFLOW_ID,
            )
        else:
            raise ValueError(f"初期メニューの不明な選択値: {selected_value}")
