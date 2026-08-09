import asyncio
import asyncio
from enum import StrEnum
from typing import Any

import boto3
from openai import AsyncOpenAI

import boto3
from openai import AsyncOpenAI


class LLMModel(StrEnum):
    """
    LLMモデル名。

    `config.yml` の `model_list.model_name` と対応する識別子です。
    """

    BEDROCK_CLAUDE_V1 = "bedrock-claude-v1"
    OPENAI_GPT_4_1 = "openai-gpt-4.1"


class NotSupportedProvider(Exception):
    """
    LLMModelにないモデル
    """

    def __init__(self, message):
        """
        サポート対象外のモデル指定時に送出する例外。

        Args:
            message (str): エラーメッセージ

        Returns:
            None
        """
        super().__init__(message)


class LLMRepository:
    models: dict[str, Any] = {}

    @staticmethod
    def _normalize_model_config(
        model_name: str, model_config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        モデル設定を正規化し、空値の認証キーを除去する。

        Args:
            model_name (str): モデル名
            model_config (dict[str, Any]): 元のモデル設定辞書

        Returns:
            dict[str, Any]: 正規化されたモデル設定辞書
        """
        normalized_config = model_config.copy()

        if model_name == LLMModel.BEDROCK_CLAUDE_V1:
            for key in (
                "aws_access_key_id",
                "aws_secret_access_key",
                "aws_session_token",
                "region_name",
            ):
                value = normalized_config.get(key)
                if value in (None, ""):
                    normalized_config.pop(key, None)

        return normalized_config

    @staticmethod
    def get_or_create_model(model_name: str, model_config: dict[str, str]):
        """
        モデルを初期化し、同一モデルは再利用する。

        Args:
            model_name (str): モデル名
            model_config (dict[str, Any]): モデルパラメータ

        Returns:
            Any: モデル
        """
        if model_name not in [e.value for e in LLMModel]:
            raise NotSupportedProvider(f"サポートしないモデル: {model_name}")

        model_config = LLMRepository._normalize_model_config(model_name, model_config)

        model_config = LLMRepository._normalize_model_config(model_name, model_config)

        if model_name not in LLMRepository.models:
            if model_name == LLMModel.OPENAI_GPT_4_1:
                LLMRepository.models[model_name] = OpenAIJobSeekerModel(model_config)
            elif model_name == LLMModel.BEDROCK_CLAUDE_V1:
                LLMRepository.models[model_name] = BedrockJobSeekerModel(model_config)
            if model_name == LLMModel.OPENAI_GPT_4_1:
                LLMRepository.models[model_name] = OpenAIJobSeekerModel(model_config)
            elif model_name == LLMModel.BEDROCK_CLAUDE_V1:
                LLMRepository.models[model_name] = BedrockJobSeekerModel(model_config)

        return LLMRepository.models[model_name]


class OpenAIJobSeekerModel:
    def __init__(self, model_config: dict[str, Any]):
        """
        OpenAI クライアントを初期化する。

        Args:
            model_config (dict[str, Any]): モデル設定辞書

        Returns:
            None
        """
        self.model_name = str(model_config["model"]).removeprefix("openai:")
        self.temperature = float(model_config.get("temperature", 0.0))
        self.top_p = float(model_config.get("top_p", 1.0))
        self.client = AsyncOpenAI()

    async def ask(self, system_prompt: str, user_message: str) -> str:
        """
        OpenAI モデルに問い合わせてテキスト応答を返す。

        Args:
            system_prompt (str): システムプロンプト
            user_message (str): ユーザーメッセージ

        Returns:
            str: モデルの応答テキスト
        """
        response = await self.client.chat.completions.create(
            model=self.model_name,
            temperature=self.temperature,
            top_p=self.top_p,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        content = response.choices[0].message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.text
                for item in content
                if getattr(item, "type", None) == "text" and getattr(item, "text", None)
            )
        return str(content)


class BedrockJobSeekerModel:
    def __init__(self, model_config: dict[str, Any]):
        """
        Bedrock クライアントを初期化する。

        Args:
            model_config (dict[str, Any]): モデル設定辞書

        Returns:
            None
        """
        self.model_name = str(model_config["model"]).removeprefix("bedrock_converse:")
        self.temperature = float(model_config.get("temperature", 0.0))
        self.top_p = float(model_config.get("top_p", 1.0))
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=model_config.get("aws_access_key_id") or None,
            aws_secret_access_key=model_config.get("aws_secret_access_key") or None,
            aws_session_token=model_config.get("aws_session_token") or None,
            region_name=model_config.get("region_name") or None,
        )

    async def ask(self, system_prompt: str, user_message: str) -> str:
        """
        Bedrock モデルに問い合わせてテキスト応答を返す。

        Args:
            system_prompt (str): システムプロンプト
            user_message (str): ユーザーメッセージ

        Returns:
            str: モデルの応答テキスト
        """
        response = await asyncio.to_thread(
            self.client.converse,
            modelId=self.model_name,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            inferenceConfig={
                "temperature": self.temperature,
                "topP": self.top_p,
            },
        )
        content = response.get("output", {}).get("message", {}).get("content", [])
        return "".join(
            item.get("text", "") for item in content if isinstance(item, dict)
        )
