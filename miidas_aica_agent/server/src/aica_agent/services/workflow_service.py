import asyncio
from typing import cast
from domain.entities.workflow_definition import WorkflowDefinition
from repositories.api_repo import AICAAPIRepository
from repositories.workflow_repo import WorkflowRepository
from repositories.workflow_definition_repo import WorkflowDefinitionRepository
from services.base_service import BaseService
from services.position_change_analyze_summary_service import PositionChangeAnalyzeSummaryService
from services.workflow_handlers.base import WorkflowHandler, WorkflowPostProcessingResult
from services.workflow_handlers.job_match_diagnosis import JobMatchDiagnosisHandler
from services.workflow_handlers.position_change_analyze import PositionChangeAnalyzeHandler
from services.workflow_handlers.generic import GenericWorkflowHandler
from services.workflow_handlers.initial_menu import InitialMenuHandler
from utils.const import INITIAL_MENU_WORKFLOW_ID, JOB_MATCH_DIAGNOSIS_WORKFLOW_ID, POSITION_CHANGE_ANALYZE_WORKFLOW_ID

class WorkflowService(BaseService):
    def __init__(
        self,
        aica_api_repository: AICAAPIRepository,
        workflow_repository: WorkflowRepository,
        workflow_definition_repository: WorkflowDefinitionRepository,
        position_change_analyze_summary_svc: PositionChangeAnalyzeSummaryService,
    ):
        super().__init__()

        self._aica_api_repository = aica_api_repository
        self._workflow_repository = workflow_repository
        self._workflow_definition_repository = workflow_definition_repository
        self._position_change_analyze_summary_svc = position_change_analyze_summary_svc

    def _get_handler(self, workflow_id: str) -> WorkflowHandler:
        """workflow_idに応じたハンドラを返す"""
        definition = self.get_definition(workflow_id)

        if workflow_id == INITIAL_MENU_WORKFLOW_ID:
            return InitialMenuHandler(workflow_id, definition)

        if workflow_id == JOB_MATCH_DIAGNOSIS_WORKFLOW_ID:
            return JobMatchDiagnosisHandler(
                workflow_id, self._aica_api_repository, definition
            )

        if workflow_id == POSITION_CHANGE_ANALYZE_WORKFLOW_ID:
            return PositionChangeAnalyzeHandler(
                workflow_id, self._position_change_analyze_summary_svc, definition
            )

        # デフォルトは汎用ハンドラ
        return GenericWorkflowHandler(workflow_id, definition)

    def exists_definition(self, workflow_id: str) -> bool:
        """ワークフロー定義が存在するか確認する"""
        try:
            self.get_definition(workflow_id)
            return True
        except (ValueError, FileNotFoundError):
            return False

    def get_definition(self, workflow_id: str) -> WorkflowDefinition:
        """ワークフロー定義を取得する"""
        return self._workflow_definition_repository.get_definition(workflow_id)

    async def process_workflow_submission(
        self,
        workflow_id: str,
        answers: dict,
        extra: dict | None = None,
    ) -> tuple[WorkflowPostProcessingResult, list[dict]]:
        """回答の保存、対話履歴の生成、ワークフロー固有の後処理を実行する"""
        handler = self._get_handler(workflow_id)

        structured_answers = handler.get_validated_structured_answers(answers)

        # 保存に必要な項目（label, value, text）のみを抽出
        validated_answers = {}
        for step_id, options in structured_answers.items():
            valid_options = []
            for opt in options:
                # 必須の label, value に加え、text があれば含める
                extracted = {"label": opt.get("label"), "value": opt.get("value")}
                if "text" in opt:
                    extracted["text"] = opt["text"]
                valid_options.append(extracted)
            validated_answers[step_id] = valid_options

        await asyncio.to_thread(
            self._workflow_repository.save_workflow_answer, workflow_id, validated_answers
        )

        # 対話履歴の生成
        history_to_save = handler.build_history_to_save(structured_answers, extra=extra)

        # ワークフロー固有の後処理を実行して、結果を取得
        post_result = await handler.perform_post_processing(structured_answers)

        return post_result, history_to_save

    async def search_job_match_diagnosis_occupations(
        self,
        answers: dict,
    ) -> list[dict]:
        """仕事の性質に基づく適職診断ワークフローの回答を元に職種を検索する"""
        handler = cast(JobMatchDiagnosisHandler, self._get_handler(JOB_MATCH_DIAGNOSIS_WORKFLOW_ID))

        structured_answers = handler.get_validated_answers_for_search(answers)

        job_nature_prefs = handler.get_job_nature_prefs(structured_answers)

        results = await handler.search_job_match_diagnosis_occupations(job_nature_prefs)

        return results

    async def generate_position_change_analyze_summary(self, answers: dict) -> dict:
        """転職理由診断ワークフローのstep1〜4の回答から転職軸の要約を生成する"""
        handler = cast(
            PositionChangeAnalyzeHandler,
            self._get_handler(POSITION_CHANGE_ANALYZE_WORKFLOW_ID),
        )

        structured_answers = handler.get_validated_answers_for_summary(answers)

        return await handler.generate_llm_summary(structured_answers)
