import json
import logging
import re
from pathlib import Path
from domain.entities.workflow_definition import WorkflowDefinition
from utils.const import LOGGER_PREFIX


class WorkflowDefinitionRepository:
    """ワークフロー定義ファイルを読み込み・管理するリポジトリ"""

    def __init__(self, workflow_dir: str) -> None:
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._workflow_dir = Path(workflow_dir)
        if not self._workflow_dir.exists():
            raise FileNotFoundError(f"ワークフローディレクトリが存在しません: {self._workflow_dir}")

        if not self._workflow_dir.is_dir():
            raise NotADirectoryError(
                f"ワークフローディレクトリがディレクトリではありません: {self._workflow_dir}"
            )

        self._definitions: dict[str, WorkflowDefinition] = {}
        self._validate_all_workflows()

    def _validate_all_workflows(self) -> None:
        """存在するすべてのワークフロー定義をバリデーションし、キャッシュする"""
        for file_path in self._workflow_dir.glob("*.json"):
            workflow_id = file_path.stem
            try:
                self.get_definition(workflow_id)
            except (ValueError, FileNotFoundError) as e:
                raise ValueError(f"ワークフロー '{workflow_id}' のバリデーションに失敗しました: {e}") from e
        self._logger.info("%s 個のワークフロー定義を読み込み、キャッシュしました", len(self._definitions))

    def get_definition(self, workflow_id: str) -> WorkflowDefinition:
        """ワークフロー定義を取得する（キャッシュにあればそれを返し、なければ読み込む）"""
        if workflow_id in self._definitions:
            return self._definitions[workflow_id]
        
        # workflow_id が安全な形式（英数字、アンダースコア、ハイフンのみ）であることを確認
        if not re.match(r"^[a-zA-Z0-9_-]+$", workflow_id):
            raise ValueError(f"不正なワークフローIDです: {workflow_id}")

        file_path = (self._workflow_dir / f"{workflow_id}.json").resolve()

        # 解決後のパスが期待するディレクトリ配下にあるか確認
        if not file_path.is_relative_to(self._workflow_dir.resolve()):
            raise ValueError(f"ディレクトリ外のアクセスを検知しました: {workflow_id}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                definition = WorkflowDefinition.model_validate(data)
                self._definitions[workflow_id] = definition
                return definition
        except FileNotFoundError as e:
            raise FileNotFoundError(f"ワークフロー定義ファイルが見つかりません: {file_path}") from e
        except Exception as e:
            raise ValueError(f"ワークフロー定義の形式が正しくありません: {file_path}") from e
