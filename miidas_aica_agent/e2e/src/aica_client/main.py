import argparse
import asyncio
import datetime
import os
import re
from pathlib import Path
from typing import Any

import yaml

from client.e2e_client import E2EClient
from models import FinishPolicy, HeadlessPersonaSeed
from repositories.llm_repo import LLMRepository

stats = {"conversations": []}


def parse_args():
    """
    コマンドライン引数を解析して返す。

    Returns:
        argparse.Namespace: 解析済み引数
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-mode",
        choices=["DEBUG", "TEST"],
        help="Override RUN_MODE from environment/config.",
    )
    return parser.parse_args()


def _runtime_value(config: dict, key: str, default):
    """
    設定のruntime セクションから値を取得し、未設定・空値の場合はデフォルト値を返す。

    Args:
        config (dict): 設定辞書
        key (str): 取得するキー名
        default: 未設定・空値の場合に返すデフォルト値

    Returns:
        Any: 取得した値、またはデフォルト値
    """
    runtime = config.get("runtime", {})
    value = runtime.get(key, default)
    if value in (None, "", "null", "None"):
        return default
    return value


def load_config():
    """
    config.ymlから設定を読み込んで、環境変数の差し替えを行います。

    Returns:
        dict: 設定
    """
    with open("config.yml", "r") as f:
        content = f.read()
    content = re.sub(r"\$\{(\w+)\}", lambda m: os.getenv(m.group(1), ""), content)
    return yaml.safe_load(content)


def load_personas(persona_location, persona_included=None, persona_excluded=None):
    """
    ペルソナ読み込み

    Args:
        persona_location (str): ペルソナの保存先
        persona_included (list, optional): 利用対象
        persona_excluded (list, optional): 除外対象。persona_includedが定義された場合、無視

    Returns:
        list: ペルソナのリスト。利用対象のmax_roundsが定義された場合、それも入っている。
    """
    personas = []
    persona_dir = Path(persona_location)
    excluded_names = {p["name"] for p in persona_excluded or []}

    if persona_included:
        for persona_config in persona_included:
            name = persona_config["name"]
            markdown_path = persona_dir / f"{name}.md"
            sidecar_path = persona_dir / f"{name}.yml"
            if markdown_path.exists() and sidecar_path.exists():
                with open(markdown_path, "r") as f:
                    content = f.read().strip()
                with open(sidecar_path, "r") as f:
                    sidecar = HeadlessPersonaSeed.model_validate(yaml.safe_load(f))
                max_rounds = persona_config.get("max_rounds")
                personas.append((content, sidecar, max_rounds, name))
            else:
                print(
                    f"ペルソナまたはsidecarが存在しない: {markdown_path}, {sidecar_path}"
                )
                return []
    else:
        for markdown_path in sorted(persona_dir.glob("*.md")):
            name = markdown_path.stem
            if name not in excluded_names:
                sidecar_path = persona_dir / f"{name}.yml"
                if not sidecar_path.exists():
                    print(f"sidecarが存在しない: {sidecar_path}")
                    return []
                with open(markdown_path, "r") as f:
                    content = f.read().strip()
                with open(sidecar_path, "r") as f:
                    sidecar = HeadlessPersonaSeed.model_validate(yaml.safe_load(f))
                personas.append((content, sidecar, None, name))

    return personas


def load_client_system_prompt(prompt_path: str) -> str:
    """
    クライアント用システムプロンプトをファイルから読み込む。

    Args:
        prompt_path (str): プロンプトファイルパス

    Returns:
        str: プロンプト文字列
    """
    with open(prompt_path, "r") as f:
        return f.read().strip()


def build_persona_system_prompt(
    client_system_prompt: str,
    persona_content: str,
    persona_seed: HeadlessPersonaSeed,
) -> str:
    """
    クライアントプロンプトとペルソナ情報を結合してシステムプロンプトを生成する。

    Args:
        client_system_prompt (str): クライアント用システムプロンプト
        persona_content (str): ペルソナのMarkdown内容
        persona_seed (HeadlessPersonaSeed): ペルソナの構造化データ

    Returns:
        str: 結合済みシステムプロンプト
    """
    sidecar_yaml = yaml.safe_dump(
        persona_seed.model_dump(mode="json"),
        allow_unicode=True,
        sort_keys=False,
    ).strip()
    return (
        f"{client_system_prompt}\n\n"
        "# Persona Markdown\n\n"
        f"{persona_content}\n\n"
        "# Structured Sidecar\n\n"
        "```yaml\n"
        f"{sidecar_yaml}\n"
        "```"
    )


def create_client_configs(config):
    """
    モデルとペルソナを組み合わせて、クライアントの設定を作成します。

    Args:
        config (dict): 設定

    Returns:
        list: (
            model: モデル設定
            persona_content: 該当ペルソナ用のシステムプロンプト
            persona_seed: headless sidecar
            max_rounds: 最大会話数
            persona_name: ペルソナ名
            model_name: モデル名
        )
    """
    persona_included = config.get("persona_included")
    persona_excluded = config.get("persona_excluded")
    personas = load_personas(
        config["persona_location"], persona_included, persona_excluded
    )
    if not personas:
        print("ペルソナ読み込みが失敗しました。")
        return None
    client_system_prompt = load_client_system_prompt(
        config["client_system_prompt_path"]
    )

    models = [m for m in config["model_list"] if not m.get("disabled", False)]
    if not models:
        print("モデルを定義してください。")
        return None

    client_number = config["client_number"]
    if client_number == 0:
        client_number = len(personas)

    max_rounds = config.get("max_rounds")

    configs = []
    for i in range(client_number):
        persona_content, persona_seed, persona_max_rounds, persona_name = personas[
            i % len(personas)
        ]
        persona_content = build_persona_system_prompt(
            client_system_prompt,
            persona_content,
            persona_seed,
        )
        model = models[i % len(models)]
        effective_max_rounds = (
            persona_max_rounds if persona_max_rounds is not None else max_rounds
        )
        configs.append(
            (
                LLMRepository.get_or_create_model(
                    model["model_name"], model["model_settings"].copy()
                ),
                persona_content,
                persona_seed,
                effective_max_rounds,
                persona_name,
                model["model_name"],
            )
        )
    return configs


async def run_client(
    ws_url: str,
    api_url: str,
    model: Any,
    system_prompt: str,
    persona_seed: HeadlessPersonaSeed,
    max_rounds: int,
    client_id: str,
    model_name: str,
    finish_policy: FinishPolicy,
    auto_follow_position_search_link: bool,
    auto_run_profile_apply: bool,
    restore_history_on_restart: bool,
    random_disconnect_probability: float,
    resume_session_id: str | None,
    debug_mode: bool = False,
) -> None:
    """
    E2Eクライアントを実行する。

    Args:
        ws_url (str): キャリアアドバイザーサーバーのWebSocket URL
        api_url (str): キャリアアドバイザーサーバーのAPI URL
        model (Any): 求職者LLM model
        system_prompt (str): 求職者システムプロンプト
        max_rounds (int): 最大会話数
        client_id (str): キャリアアドバイザークライアントID
        model_name (str): ログ出力用モデル名
        finish_policy (FinishPolicy): 終了条件
        test_resume_session (bool): 同一session_idでの再接続と履歴復元を検証するか
        debug_mode (bool): デバッグモード

    Returns:
        None
    """
    print(f"{client_id} ({model_name}) 開始")

    client = E2EClient(
        ws_url,
        api_url,
        model,
        system_prompt,
        max_rounds,
        client_id,
        model_name,
        persona_seed,
        finish_policy,
        auto_follow_position_search_link=auto_follow_position_search_link,
        auto_run_profile_apply=auto_run_profile_apply,
        restore_history_on_restart=restore_history_on_restart,
        random_disconnect_probability=random_disconnect_probability,
        resume_session_id=resume_session_id,
        debug_mode=debug_mode,
    )
    result = await client.run()

    finish_reason = result.get("finish_reason", "unknown") if result else "no_result"
    session_id = result.get("session_id", "unknown") if result else "unknown"
    print(f"{client_id} ({model_name}) 終了: {finish_reason} [session_id={session_id}]")

    if result:
        stats["conversations"].append(result)


def generate_summary() -> None:
    """
    マークダウン形式のサマリを生成します。

    Returns:
        None
    """
    if not stats["conversations"]:
        return

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    summary_filename = f"summary_{timestamp}.md"
    print(f"サマリ生成開始：{summary_filename}")

    summary = ["# E2Eテスト概要\n"]
    all_first_msg_times = []
    all_total_times = []
    all_agent_invoke_times = []

    for conv in stats["conversations"]:
        for stat in conv["stats"]:
            all_first_msg_times.append(stat["first_message_time"])
            all_total_times.append(stat["total_response_time"])
            all_agent_invoke_times.append(stat["agent_invoke_time"])

    summary.append("## 全体統計")
    summary.append(f"- 総会話数: {len(stats['conversations'])}")
    summary.append(
        f"- 平均初回メッセージ応答時間: {sum(all_first_msg_times) / len(all_first_msg_times):.2f}s"
    )
    summary.append(
        f"- 平均総応答時間: {sum(all_total_times) / len(all_total_times):.2f}s"
    )
    summary.append(
        f"- 平均エージェント処理時間: {sum(all_agent_invoke_times) / len(all_agent_invoke_times):.2f}s\n"
    )

    summary.append("## クライアント別統計\n")
    for conv in stats["conversations"]:
        client_stats = conv["stats"]
        first_msg_times = [s["first_message_time"] for s in client_stats]
        total_times = [s["total_response_time"] for s in client_stats]
        agent_invoke_times = [s["agent_invoke_time"] for s in client_stats]

        summary.append(f"### {conv['persona']} ({conv['model']})")
        summary.append(f"- 会話ターン数: {conv['turns']}")
        summary.append(f"- 再接続回数: {conv.get('reconnects', 0)}")
        summary.append(f"- 終了理由: {conv.get('finish_reason', 'unknown')}")
        summary.append(
            f"- 最終セッションステータス: {conv.get('session_status', 'unknown')}"
        )
        summary.append(
            f"- 平均初回メッセージ応答時間: {sum(first_msg_times) / len(first_msg_times):.2f}s"
        )
        summary.append(f"- 平均総応答時間: {sum(total_times) / len(total_times):.2f}s")
        summary.append(
            f"- 平均エージェント処理時間: {sum(agent_invoke_times) / len(agent_invoke_times):.2f}s\n"
        )

    with open(summary_filename, "w") as f:
        f.write("\n".join(summary))

    print(f"サマリ生成完了：{summary_filename}")


async def main(args):
    """
    E2Eテストのエントリーポイント。設定を読み込み、クライアントを起動する。

    Args:
        args (argparse.Namespace): コマンドライン引数

    Returns:
        None
    """
    config = load_config()
    if args.run_mode:
        config["run_mode"] = args.run_mode

    client_configs = create_client_configs(config)
    if not client_configs:
        print("config読み込みが失敗しました。")
        return

    ws_url = config["agent_server"]["ws_url"]
    api_url = config["agent_server"]["api_url"]
    run_mode = config["run_mode"]
    finish_policy = FinishPolicy(
        _runtime_value(config, "finish_policy", FinishPolicy.EITHER)
    )
    auto_follow_position_search_link = _runtime_value(
        config, "auto_follow_position_search_link", True
    )
    auto_run_profile_apply = _runtime_value(config, "auto_run_profile_apply", True)
    restore_history_on_restart = _runtime_value(
        config, "restore_history_on_restart", True
    )
    random_disconnect_probability = float(
        _runtime_value(config, "random_disconnect_probability", 0.15)
    )
    resume_session_id = _runtime_value(config, "resume_session_id", None) or None
    if run_mode not in ["DEBUG", "TEST"]:
        print(f"run_modeを正しく設定してください。: {run_mode}")
        return

    try:
        if run_mode == "DEBUG":
            (
                model,
                system_prompt,
                persona_seed,
                max_rounds,
                client_id,
                model_name,
            ) = client_configs[0]
            await run_client(
                ws_url,
                api_url,
                model,
                system_prompt,
                persona_seed,
                max_rounds,
                client_id,
                model_name,
                finish_policy,
                auto_follow_position_search_link,
                auto_run_profile_apply,
                restore_history_on_restart,
                random_disconnect_probability,
                resume_session_id,
                debug_mode=True,
            )
        else:
            tasks = []
            for (
                model,
                system_prompt,
                persona_seed,
                max_rounds,
                client_id,
                model_name,
            ) in client_configs:
                task = run_client(
                    ws_url,
                    api_url,
                    model,
                    system_prompt,
                    persona_seed,
                    max_rounds,
                    client_id,
                    model_name,
                    finish_policy,
                    auto_follow_position_search_link,
                    auto_run_profile_apply,
                    restore_history_on_restart,
                    random_disconnect_probability,
                    resume_session_id,
                )
                tasks.append(task)
            await asyncio.gather(*tasks)
    finally:
        generate_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main(parse_args()))
    except KeyboardInterrupt:
        print("\nExiting...")
