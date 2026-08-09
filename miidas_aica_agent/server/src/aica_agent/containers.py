"""
依存性注入（Dependency Injection: DI）
"""

import logging.config
from pathlib import Path

from dependency_injector import containers, providers

from database import Database
from repositories import (
    action_log_repo,
    agent_repo,
    chat_repo,
    position_repo,
    rate_limit_repo,
    user_repo,
    api_repo,
    prompt_repo,
    summary_repo,
    workflow_repo,
    workflow_definition_repo,
)
from services import (
    chat_service,
    chat_service_refactored,
    conversation_summary_service,
    position_change_analyze_summary_service,
    position_service,
    rate_limit_service,
    user_service,
    llm_service,
    agent_service,
    summary_service,
    workflow_service,
)
from services.chat.llm_runner import (
    CompletionsAgentRunner,
    LLMRunner,
    ResponsesAgentRunner,
)
from services.chat.agent_runtime_config import (
    COMPLETIONS_API_STYLE,
    DEFAULT_SERVICE_VARIANT,
    REFACTORED_SERVICE_VARIANT,
    SUPPORTED_API_STYLES,
    SUPPORTED_SERVICE_VARIANTS,
    get_api_style,
    get_service_variant,
)
from services.chat.config_validator import InvalidAgentRuntimeConfigError
from security.llm_output_guard import LLMOutputGuard
from utils.cache_utils import RedisCacheUtil
from utils.log_utils import record_factory


_CONFIG_BASE_DIR = Path(__file__).resolve().parent


def _resolve_config_dir(path: str) -> str:
    resolved = Path(path)
    if resolved.is_absolute():
        return str(resolved)
    return str((_CONFIG_BASE_DIR / resolved).resolve())


def _build_chat_service(service_variant: str, **kwargs):
    if service_variant == REFACTORED_SERVICE_VARIANT:
        return chat_service_refactored.ChatService(**kwargs)
    if service_variant == DEFAULT_SERVICE_VARIANT:
        kwargs.pop("llm_runner", None)
        return chat_service.ChatService(**kwargs)
    allowed = ", ".join(sorted(SUPPORTED_SERVICE_VARIANTS))
    raise InvalidAgentRuntimeConfigError(
        f"service_variant: {service_variant} is not supported. Only {allowed} are valid."
    )


def _build_refactored_llm_runner(api_style: str, **kwargs) -> LLMRunner:
    if api_style == COMPLETIONS_API_STYLE:
        return CompletionsAgentRunner(**kwargs)
    if api_style in SUPPORTED_API_STYLES:
        return ResponsesAgentRunner(**kwargs)
    allowed = ", ".join(sorted(SUPPORTED_API_STYLES))
    raise InvalidAgentRuntimeConfigError(
        f"agent_runtime.api_style: {api_style} is not supported. Only {allowed} are valid."
    )


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["endpoints", "utils.fastapi.dependency"]
    )

    config = providers.Configuration(yaml_files=["config.yml"])

    logging.setLogRecordFactory(record_factory)
    _ = providers.Resource(
        logging.config.dictConfig,
        config=config.logging,
    )

    db = providers.Singleton(Database, db_url=config.db.url)

    cache_util = providers.Singleton(
        RedisCacheUtil,
        host=config.cache.redis.host,
        port=config.cache.redis.port,
        default_ttl=config.cache.redis.ttl,
    )

    agent_repository = providers.Factory(
        agent_repo.AgentRepository,
        session_factory=db.provided.session,
    )

    chat_repository = providers.Factory(
        chat_repo.ChatRepository,
        session_factory=db.provided.session,
    )

    user_repository = providers.Factory(
        user_repo.UserRepository,
        session_factory=db.provided.session,
    )

    prompt_repository = providers.Singleton(
        prompt_repo.PromptRepository,
        prompts_dir=providers.Callable(_resolve_config_dir, config.prompts.dir),
    )

    workflow_repository = providers.Factory(
        workflow_repo.WorkflowRepository,
        session_factory=db.provided.session,
    )

    workflow_definition_repository = providers.Singleton(
        workflow_definition_repo.WorkflowDefinitionRepository,
        workflow_dir=providers.Callable(_resolve_config_dir, config.workflows.dir),
    )

    agent_svc = providers.Singleton(
        agent_service.AgentService,
        agent_repository=agent_repository,
        prompt_repository=prompt_repository,
    )

    llm_svc = providers.Resource(
        llm_service.LLMService,
        mcp_url=config.mcp.url,
        timeout=config.mcp.timeout,
        model_list=config.model_list,
        agent_svc=agent_svc,
    )

    action_log_repository = providers.Factory(
        action_log_repo.ActionLogRepository,
        session_factory=db.provided.session,
    )

    rate_limit_repository = providers.Factory(
        rate_limit_repo.RedisRateLimitRepository,
        redis_cache_util=cache_util,
    )

    # 異なるユーザーが会員登録＆面談応募するので、本体側へのHTTPリクエストは全部１つのセッションで行っていけない。
    # AICA APIサーバへのリクエストはステートレスなので、１つのセッションで大丈夫です。
    aica_api_repository = providers.Resource(
        api_repo.AICAAPIRepository,
        timeout=config.api.timeout,
        aica_api_url=config.api.aica,
    )

    position_repository = providers.Factory(
        position_repo.PositionRepository,
        cache_util=cache_util,
    )

    rate_limit_svc = providers.Factory(
        rate_limit_service.RateLimitService,
        rate_limit_repository=rate_limit_repository,
        rate_limit=config.rate_limits,
    )

    position_svc = providers.Factory(
        position_service.PositionService,
        position_repository=position_repository,
        aica_api_repository=aica_api_repository,
        chat_repository=chat_repository,
        user_repository=user_repository,
        action_log_repository=action_log_repository,
    )

    summary_repository = providers.Factory(
        summary_repo.SummaryRepository,
        session_factory=db.provided.session,
    )

    position_change_analyze_summary_svc = providers.Singleton(
        position_change_analyze_summary_service.PositionChangeAnalyzeSummaryService,
        model_list=config.model_list,
    )

    workflow_svc = providers.Factory(
        workflow_service.WorkflowService,
        aica_api_repository=aica_api_repository,
        workflow_repository=workflow_repository,
        workflow_definition_repository=workflow_definition_repository,
        position_change_analyze_summary_svc=position_change_analyze_summary_svc,
    )

    conversation_summary_svc = providers.Singleton(
        conversation_summary_service.ConversationSummaryService,
        model_list=config.model_list,
    )

    summary_svc = providers.Factory(
        summary_service.SummaryService,
        conversation_summary_service=conversation_summary_svc,
        summary_repository=summary_repository,
        chat_repository=chat_repository,
    )

    llm_output_guard = providers.Singleton(
        LLMOutputGuard,
    )

    refactored_llm_runner = providers.Factory(
        _build_refactored_llm_runner,
        api_style=providers.Callable(get_api_style, config),
        action_log_repository=action_log_repository,
        logger=providers.Callable(logging.getLogger, "aica_agent.llm_runner"),
    )

    chat_svc = providers.Factory(
        _build_chat_service,
        service_variant=providers.Callable(get_service_variant, config),
        position_svc=position_svc,
        llm_svc=llm_svc,
        chat_repository=chat_repository,
        position_repository=position_repository,
        user_repository=user_repository,
        action_log_repository=action_log_repository,
        rate_limit_service=rate_limit_svc,
        workflow_service=workflow_svc,
        conversation_summary_svc=conversation_summary_svc,
        summary_service=summary_svc,
        llm_runner=refactored_llm_runner,
        llm_output_guard=llm_output_guard,
    )

    user_svc = providers.Factory(
        user_service.UserService,
        position_svc=position_svc,
        chat_repository=chat_repository,
        user_repository=user_repository,
        aica_api_repository=aica_api_repository,
        action_log_repository=action_log_repository,
        miidas_api_url=config.api.miidas,
        timeout=config.api.timeout,
    )
