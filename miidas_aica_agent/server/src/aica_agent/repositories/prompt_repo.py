import logging
from pathlib import Path

from domain.entities.agent import Agent
from utils.const import LOGGER_PREFIX


class PromptRepository:
    """エージェントプロンプトをファイルから読み込むリポジトリ"""

    def __init__(self, prompts_dir: str) -> None:
        """
        PromptRepositoryを初期化する

        Args:
            prompts_dir: プロンプトファイルが格納されているディレクトリのパス

        Raises:
            FileNotFoundError: プロンプトディレクトリが存在しない場合
        """
        self.logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._prompts_dir = Path(prompts_dir)
        self._cache: dict[tuple[int, str], str] = {}

        if not self._prompts_dir.exists():
            raise FileNotFoundError(
                f"プロンプトディレクトリが存在しません: {self._prompts_dir}"
            )

        if not self._prompts_dir.is_dir():
            raise NotADirectoryError(
                f"プロンプトパスがディレクトリではありません: {self._prompts_dir}"
            )

        self.logger.info(
            "PromptRepositoryを初期化しました。ディレクトリ: %s", self._prompts_dir
        )

    def get_prompt(self, agent_id: int, agent_name: str) -> str:
        """
        エージェントのプロンプトをファイルから読み込む

        Args:
            agent_id: エージェントID
            agent_name: エージェント名

        Returns:
            プロンプト内容

        Raises:
            FileNotFoundError: プロンプトファイルが存在しない場合
            ValueError: プロンプトファイルが空（または空白のみ）の場合、またはファイルがUTF-8でデコードできない場合
        """
        cache_key = (agent_id, agent_name)

        # キャッシュがある場合は返す
        if cache_key in self._cache:
            self.logger.debug(
                "キャッシュからプロンプトを取得: エージェント %s (%s)",
                agent_id,
                agent_name,
            )
            return self._cache[cache_key]

        # ファイルパスを構築: {id}_{name}.txt
        file_path = self._prompts_dir / f"{agent_id}_{agent_name}.txt"

        if not file_path.exists():
            raise FileNotFoundError(
                f"プロンプトファイルが見つかりません: エージェント {agent_id} ({agent_name}): {file_path}"
            )

        # UTF-8エンコーディングでファイルから読み込む
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                prompt = f.read()
        except UnicodeDecodeError as e:
            raise ValueError(
                f"プロンプトファイルのデコードに失敗しました: エージェント {agent_id} ({agent_name}): {file_path}. "
                f"ファイルがUTF-8エンコードされていることを確認してください。"
            ) from e

        # プロンプトが空でないことを検証
        if not prompt.strip():
            raise ValueError(
                f"プロンプトファイルが空です: エージェント {agent_id} ({agent_name}): {file_path}"
            )

        # キャッシュに保存
        self._cache[cache_key] = prompt
        self.logger.info(
            "プロンプトを正常に読み込みました: エージェント %s (%s) from %s",
            agent_id,
            agent_name,
            file_path,
        )

        return prompt

    def validate_all_prompts(self, agents: list[Agent]) -> None:
        """
        指定されたエージェントのプロンプトファイルが全て存在することを検証する
        起動時のフェイルファストチェック

        Args:
            agents: 検証するエージェントのリスト

        Raises:
            FileNotFoundError: プロンプトファイルが欠落している場合
        """
        missing_files = []

        for agent in agents:
            file_path = self._prompts_dir / f"{agent.id}_{agent.name}.txt"
            if not file_path.exists():
                missing_files.append(f"{agent.id}_{agent.name}.txt")

        if missing_files:
            raise FileNotFoundError(
                f"プロンプトファイルが見つかりません: {', '.join(missing_files)}. "
                f"期待される場所: {self._prompts_dir}"
            )

        self.logger.info("%s個のプロンプトファイルの存在を確認しました", len(agents))
