from unittest.mock import Mock

import pytest

from domain.entities.agent import Agent
from repositories.prompt_repo import PromptRepository
from utils.log_utils import clear_session_id, set_session_id


@pytest.fixture(autouse=True)
def session_scope():
    """全テストでセッションIDをセットアップする"""
    set_session_id("test-session-id")
    yield
    clear_session_id()


@pytest.fixture
def temp_prompts_dir(tmp_path):
    """一時的なプロンプトディレクトリを作成"""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    return prompts_dir


@pytest.fixture
def create_prompt_file():
    """プロンプトファイルを作成するヘルパー"""

    def _create(directory, agent_id, agent_name, content):
        file_path = directory / f"{agent_id}_{agent_name}.txt"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return _create


@pytest.fixture
def repository(temp_prompts_dir):
    """PromptRepositoryインスタンスを作成"""
    return PromptRepository(str(temp_prompts_dir))


def _create_mock_agent(agent_id, name):
    """Agentモックを作成するヘルパー"""
    agent = Mock(spec=Agent)
    agent.id = agent_id
    agent.name = name
    return agent


@pytest.fixture
def sample_agents():
    """テスト用のAgentエンティティリストを作成"""
    return [
        _create_mock_agent(2, "CareerAdvisor"),
        _create_mock_agent(3, "PositionGuide"),
        _create_mock_agent(5, "PositionChangeAnalyze"),
    ]


class TestInit:
    """__init__メソッドのテスト"""

    def test_initializes_successfully_with_valid_directory(self, temp_prompts_dir):
        """有効なディレクトリパスでの初期化が成功すること"""
        repo = PromptRepository(str(temp_prompts_dir))

        assert repo._prompts_dir == temp_prompts_dir
        assert isinstance(repo._cache, dict)
        assert len(repo._cache) == 0

    def test_raises_file_not_found_error_when_directory_does_not_exist(self, tmp_path):
        """存在しないディレクトリパスでFileNotFoundErrorが発生すること"""
        nonexistent_dir = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError) as exc_info:
            PromptRepository(str(nonexistent_dir))

        assert "プロンプトディレクトリが存在しません" in str(exc_info.value)
        assert str(nonexistent_dir) in str(exc_info.value)

    def test_raises_not_a_directory_error_when_path_is_file(self, tmp_path):
        """ディレクトリではないパスでNotADirectoryErrorが発生すること"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(NotADirectoryError) as exc_info:
            PromptRepository(str(file_path))

        assert "プロンプトパスがディレクトリではありません" in str(exc_info.value)
        assert str(file_path) in str(exc_info.value)


class TestGetPrompt:
    """get_promptメソッドのテスト"""

    def test_reads_and_returns_prompt_from_file(
        self, repository, temp_prompts_dir, create_prompt_file
    ):
        """ファイルからプロンプトを正しく読み込んで返すこと"""
        content = "これはテスト用のプロンプトです"
        create_prompt_file(temp_prompts_dir, 2, "CareerAdvisor", content)

        result = repository.get_prompt(2, "CareerAdvisor")

        assert result == content

    def test_caches_prompt_after_first_read(
        self, repository, temp_prompts_dir, create_prompt_file
    ):
        """2回目以降の読み込みでキャッシュが使用されること"""
        content = "キャッシュテスト"
        file_path = create_prompt_file(temp_prompts_dir, 2, "CareerAdvisor", content)

        # 1回目: ファイルから読み込み
        result1 = repository.get_prompt(2, "CareerAdvisor")
        assert result1 == content

        # キャッシュにデータが保存されていることを確認
        cache_key = (2, "CareerAdvisor")
        assert cache_key in repository._cache
        assert repository._cache[cache_key] == content

        # ファイルを削除
        file_path.unlink()

        # 2回目: キャッシュから読み込み（ファイルが無くても成功）
        result2 = repository.get_prompt(2, "CareerAdvisor")
        assert result2 == content

    def test_raises_file_not_found_error_when_prompt_file_missing(self, repository):
        """プロンプトファイルが存在しない場合にFileNotFoundErrorが発生すること"""
        with pytest.raises(FileNotFoundError) as exc_info:
            repository.get_prompt(99, "NonExistent")

        assert "プロンプトファイルが見つかりません" in str(exc_info.value)
        assert "エージェント 99 (NonExistent)" in str(exc_info.value)
        assert "99_NonExistent.txt" in str(exc_info.value)

    def test_raises_value_error_for_empty_prompt_file(
        self, repository, temp_prompts_dir, create_prompt_file
    ):
        """空のプロンプトファイルでValueErrorが発生すること"""
        create_prompt_file(temp_prompts_dir, 3, "EmptyPrompt", "")

        with pytest.raises(ValueError) as exc_info:
            repository.get_prompt(3, "EmptyPrompt")

        assert "プロンプトファイルが空です" in str(exc_info.value)
        assert "エージェント 3 (EmptyPrompt)" in str(exc_info.value)

    def test_raises_value_error_for_whitespace_only_prompt_file(
        self, repository, temp_prompts_dir, create_prompt_file
    ):
        """空白のみのプロンプトファイルでValueErrorが発生すること"""
        create_prompt_file(temp_prompts_dir, 4, "WhitespacePrompt", "   \n\t  \n  ")

        with pytest.raises(ValueError) as exc_info:
            repository.get_prompt(4, "WhitespacePrompt")

        assert "プロンプトファイルが空です" in str(exc_info.value)
        assert "エージェント 4 (WhitespacePrompt)" in str(exc_info.value)

    @pytest.mark.parametrize(
        "content",
        [
            "日本語のプロンプトです",
            "こんにちは、世界！",
            "漢字、ひらがな、カタカナ、ABC、123",
            "転職アドバイザーのプロンプト\n複数行のテキスト",
        ],
    )
    def test_handles_japanese_characters_in_prompt(
        self, repository, temp_prompts_dir, create_prompt_file, content
    ):
        """UTF-8エンコードされた日本語が正しく読み込まれること"""
        create_prompt_file(temp_prompts_dir, 4, "JapaneseTest", content)

        result = repository.get_prompt(4, "JapaneseTest")

        assert result == content

    def test_raises_value_error_for_non_utf8_file(self, repository, temp_prompts_dir):
        """UTF-8以外でエンコードされたファイルでValueErrorが発生すること"""
        # Shift-JISでエンコードされたファイルを作成
        file_path = temp_prompts_dir / "5_InvalidEncoding.txt"
        # UTF-8でデコードできないバイトシーケンスを書き込む
        with open(file_path, "wb") as f:
            f.write(b"\x82\xa0\x82\xa2\x82\xa4")  # Shift-JISで「あいう」

        with pytest.raises(ValueError) as exc_info:
            repository.get_prompt(5, "InvalidEncoding")

        # エラーメッセージに必要な情報が含まれることを確認
        error_message = str(exc_info.value)
        assert "プロンプトファイルのデコードに失敗しました" in error_message
        assert "エージェント 5 (InvalidEncoding)" in error_message
        assert "5_InvalidEncoding.txt" in error_message
        assert "UTF-8エンコードされていることを確認してください" in error_message

        # 元の例外がUnicodeDecodeErrorであることを確認
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, UnicodeDecodeError)

    def test_handles_multiple_agents_with_separate_cache_keys(
        self, repository, temp_prompts_dir, create_prompt_file
    ):
        """複数の異なるエージェントのプロンプトが正しくキャッシュされること"""
        create_prompt_file(temp_prompts_dir, 1, "Agent1", "Prompt 1")
        create_prompt_file(temp_prompts_dir, 2, "Agent2", "Prompt 2")
        create_prompt_file(temp_prompts_dir, 3, "Agent3", "Prompt 3")

        result1 = repository.get_prompt(1, "Agent1")
        result2 = repository.get_prompt(2, "Agent2")
        result3 = repository.get_prompt(3, "Agent3")

        assert result1 == "Prompt 1"
        assert result2 == "Prompt 2"
        assert result3 == "Prompt 3"

        # 全てがキャッシュに保存されていること
        assert len(repository._cache) == 3
        assert (1, "Agent1") in repository._cache
        assert (2, "Agent2") in repository._cache
        assert (3, "Agent3") in repository._cache


class TestValidateAllPrompts:
    """validate_all_promptsメソッドのテスト"""

    def test_succeeds_when_all_prompt_files_exist(
        self, repository, temp_prompts_dir, create_prompt_file, sample_agents
    ):
        """全てのプロンプトファイルが存在する場合に成功すること"""
        for agent in sample_agents:
            create_prompt_file(
                temp_prompts_dir, agent.id, agent.name, f"Prompt for {agent.name}"
            )

        # 例外が発生しないことを確認
        repository.validate_all_prompts(sample_agents)

    def test_raises_file_not_found_error_when_any_file_missing(
        self, repository, temp_prompts_dir, create_prompt_file, sample_agents
    ):
        """1つでもファイルが欠けている場合にFileNotFoundErrorが発生すること"""
        # 最初の2つだけ作成（3つ目は作成しない）
        create_prompt_file(temp_prompts_dir, 2, "CareerAdvisor", "Prompt 1")
        create_prompt_file(temp_prompts_dir, 3, "PositionGuide", "Prompt 2")

        with pytest.raises(FileNotFoundError) as exc_info:
            repository.validate_all_prompts(sample_agents)

        error_message = str(exc_info.value)
        assert "プロンプトファイルが見つかりません" in error_message
        assert "5_PositionChangeAnalyze.txt" in error_message

    def test_reports_multiple_missing_files(self, repository, sample_agents):
        """複数のファイルが欠けている場合、全てリストされること"""
        # ファイルを1つも作成しない
        with pytest.raises(FileNotFoundError) as exc_info:
            repository.validate_all_prompts(sample_agents)

        error_message = str(exc_info.value)
        assert "2_CareerAdvisor.txt" in error_message
        assert "3_PositionGuide.txt" in error_message
        assert "5_PositionChangeAnalyze.txt" in error_message

    def test_handles_empty_agent_list(self, repository):
        """エージェントリストが空の場合に正常に処理されること"""
        # 例外が発生しないことを確認
        repository.validate_all_prompts([])

    def test_error_message_includes_expected_directory_path(
        self, repository, temp_prompts_dir, sample_agents
    ):
        """エラーメッセージに期待されるディレクトリパスが含まれること"""
        with pytest.raises(FileNotFoundError) as exc_info:
            repository.validate_all_prompts(sample_agents)

        error_message = str(exc_info.value)
        assert "期待される場所:" in error_message
        assert str(temp_prompts_dir) in error_message


class TestCacheVerification:
    """キャッシュ動作の検証テスト"""

    def test_cache_persists_after_file_deletion(
        self, repository, temp_prompts_dir, create_prompt_file
    ):
        """キャッシュ後にファイルを削除しても、キャッシュから読み込めること"""
        content = "Test prompt"
        file_path = create_prompt_file(temp_prompts_dir, 1, "Agent1", content)

        # 1回目: ファイルから読み込み
        result1 = repository.get_prompt(1, "Agent1")
        assert result1 == content

        # キャッシュを確認
        assert (1, "Agent1") in repository._cache

        # ファイルを削除
        file_path.unlink()

        # 2回目: キャッシュから読み込み（ファイルが無くても成功）
        result2 = repository.get_prompt(1, "Agent1")
        assert result2 == content
