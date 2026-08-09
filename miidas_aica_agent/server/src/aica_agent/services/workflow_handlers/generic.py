from domain.entities.workflow_definition import WorkflowDefinition
from services.workflow_handlers.base import WorkflowHandler, WorkflowPostProcessingResult

class GenericWorkflowHandler(WorkflowHandler):
    """
    汎用的ワークフローハンドラ
    """

    def __init__(self, workflow_id: str, definition: WorkflowDefinition):
        super().__init__(workflow_id, definition)

    async def perform_post_processing(self, structured_answers: dict[str, list[dict]]) -> WorkflowPostProcessingResult:
        """
        回答内容を要約してLLMへの指示メッセージを生成する
        """
        user_answers_summary = self.summarize_answers(structured_answers)

        message = f"""
ユーザーがワークフロー「{self._definition.name}」に回答しました。

回答内容の要約:
{user_answers_summary}

これらの回答内容を踏まえて、ユーザーとの対話を継続してください。
"""
        return WorkflowPostProcessingResult(message=message)
