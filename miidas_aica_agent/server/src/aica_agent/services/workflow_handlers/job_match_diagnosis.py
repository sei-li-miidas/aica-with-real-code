from domain.entities.workflow_definition import WorkflowDefinition
from services.workflow_handlers.base import WorkflowHandler, WorkflowPostProcessingResult
from repositories.api_repo import AICAAPIRepository
from fastapi import status

class JobMatchDiagnosisHandler(WorkflowHandler):
    """
    仕事の性質に基づく適職診断ワークフローハンドラ
    """
    PREFERENCE_WANTED = "やりたい"
    PREFERENCE_UNWANTED = "避けたい"
    MIN_NATURE_SCORE = 3.0
    MIN_JOB_TYPE_SCORE = 0.4
    DEFAULT_CONVERSATION_DELIMITER = "、"

    def __init__(self, workflow_id: str, aica_api_repo: AICAAPIRepository, definition: WorkflowDefinition):
        super().__init__(workflow_id, definition)
        self._aica_api_repo = aica_api_repo

    def get_validated_answers_for_search(self, raw_answers: dict) -> dict[str, list[dict]]:
        """職種検索に必要なステップ（1, 2）の抽出とバリデーションを行う"""
        structured_answers = {}
        for step_id in ["1", "2"]:
            if step_id in raw_answers:
                structured_answers[step_id] = self.extract_options_by_step(step_id, raw_answers[step_id])

        self.validate_job_nature_steps(structured_answers)
        return structured_answers

    def get_validated_structured_answers(self, raw_answers: dict) -> dict[str, list[dict]]:
        """全ステップ（1, 2, 3）の抽出とバリデーションを行う"""
        # 仕事の性質（ステップ1, 2）の抽出とバリデーション
        structured_answers = self.get_validated_answers_for_search(raw_answers)

        # 職種（ステップ3）のバリデーションと追加
        structured_answers["3"] = self.validate_job_type_step(raw_answers)

        return structured_answers

    def validate_job_nature_steps(self, structured_answers: dict[str, list[dict]]) -> None:
        """ステップ1とステップ2のバリデーションと整合性チェックを行う"""
        step1_options = structured_answers.get("1", [])
        if len(step1_options) < 3 or len(step1_options) > 5:
            raise ValueError(f"ステップ1は3〜5つ選択してください (現在の選択数: {len(step1_options)})")

        step2_options = structured_answers.get("2", [])
        if len(step2_options) > 5:
            raise ValueError(f"ステップ2は最大5つまで選択してください (現在の選択数: {len(step2_options)})")

        # ステップ1とステップ2の重複チェック
        if step1_options and step2_options:
            step1_values = {str(opt["value"]) for opt in step1_options}

            # ステップ1に含まれる値をステップ2から除外
            valid_step2_options = [
                opt for opt in step2_options if str(opt["value"]) not in step1_values
            ]

            if len(valid_step2_options) != len(step2_options):
                self._logger.warning(
                    "ワークフロー回答の整合性エラー: ワークフローID %s, ステップ1で選択された値がステップ2でも選択されています。重複を除外します。",
                    self.workflow_id
                )

            structured_answers["2"] = valid_step2_options

    def validate_job_type_step(self, raw_answers: dict) -> list[dict]:
        """ステップ3のバリデーションを行い、構造化データを返す"""
        step3_raw_values = raw_answers.get("3")

        if not step3_raw_values or not isinstance(step3_raw_values, list) or len(step3_raw_values) < 1:
            raise ValueError("ステップ3は1つ以上選択してください")

        valid_step3_options = []
        for item in step3_raw_values:
            if not isinstance(item, dict):
                raise ValueError(f"ワークフロー回答の形式エラー: ワークフローID {self.workflow_id}, ステップID 3 の回答が辞書形式ではありません: {item}")

            valid_step3_options.append({
                "label": item.get("label", ""),
                "value": item.get("value", "")
            })

        return valid_step3_options

    async def perform_post_processing(self, structured_answers: dict[str, list[dict]]) -> WorkflowPostProcessingResult:
        """
        回答内容を要約してLLMへの指示メッセージを生成し、選択された職種名を返す
        """
        user_answers_summary = self.summarize_answers(structured_answers)

        # LLM向けのメッセージを生成
        message = f"""
ユーザーが回答した「やりたい」もしくは「やりたくない」仕事の性質に基づいて適職を検索し、その中から気になる職種を選択してもらいました。

ユーザーの回答内容:
{user_answers_summary}

ユーザーが興味を持った職種を踏まえて、具体的な求人提案について自然に対話を開始してください。
"""

        # ステップ3で選択された職種名を抽出する
        step3_options = structured_answers.get("3", [])
        jobtypes = [
            item.get("label", "").strip()
            for item in step3_options
            if isinstance(item, dict) and item.get("label", "").strip()
        ]
        selected_jobtypes = jobtypes if jobtypes else None

        return WorkflowPostProcessingResult(message=message, selected_jobtypes=selected_jobtypes)

    def get_job_nature_prefs(self, structured_answers: dict[str, list[dict]]) -> list[dict]:
        """構造化された回答から、職種検索APIに必要なJobNaturePreferencesを生成する"""
        job_nature_prefs = []
        for step_id, options in structured_answers.items():
            preference = None
            if str(step_id) == "1":
                preference = self.PREFERENCE_WANTED
            elif str(step_id) == "2":
                preference = self.PREFERENCE_UNWANTED

            if preference:
                for opt in options:
                    nature = opt.get("jobNature")
                    if nature:
                        job_nature_prefs.append({
                            "JobNature": nature,
                            "Preference": preference
                        })
        return job_nature_prefs

    async def search_job_match_diagnosis_occupations(self, job_nature_prefs: list[dict]) -> list[dict]:
        """仕事の性質に基づいた職種検索APIを実行する"""
        path = "jobtype/search/nature"
        payload = {
            "JobNaturePreferences": job_nature_prefs,
            "MinNatureScore": self.MIN_NATURE_SCORE,
            "MinJobTypeScore": self.MIN_JOB_TYPE_SCORE,
        }
        status_code, result = await self._aica_api_repo.post(
            path,
            json=payload,
        )

        if status_code != status.HTTP_200_OK:
            self._logger.error("職種検索APIリクエスト失敗: %s, %s", status_code, result)
            raise RuntimeError(f"職種検索APIリクエストに失敗しました (status_code: {status_code}, result: {result})")

        formatted_results = []
        if isinstance(result, list):
            for item in result:
                formatted_results.append({
                    "ID": item.get("ID"),
                    "職種名": item.get("Name"),
                    "職種説明": item.get("Description")
                })

        return formatted_results
