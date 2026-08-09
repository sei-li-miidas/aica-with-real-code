import logging.config
from pathlib import Path

from dependency_injector import containers, providers

from commands.aggregate_and_delete_rate_limits import AggregateAndDeleteRateLimits
from commands.chat_command import ChatCommand
from database import Database
from repositories import rate_limit_archive_repo
from utils.cache_utils import RedisCacheUtil


class Container(containers.DeclarativeContainer):
    """
    Dependency Injecttion
    """

    config = providers.Configuration(
        yaml_files=[str(Path(__file__).parent / "config.yml")]
    )

    _ = providers.Resource(
        logging.config.dictConfig,
        config=config.logging,
    )

    db = providers.Singleton(Database, db_url=config.db.url)

    cache_util = providers.Singleton(
        RedisCacheUtil,
        host=config.cache.redis.host,
        port=config.cache.redis.port,
    )

    chat_command_factory = providers.Factory(
        ChatCommand,
        session_factory=db.provided.session,
    )

    rate_limit_archive_repository = providers.Factory(
        rate_limit_archive_repo.RedisRateLimitArchiveRepository,
        session_factory=db.provided.session,
        cache_util=cache_util,
    )

    aggregate_and_delete_rate_limits_factory = providers.Factory(
        AggregateAndDeleteRateLimits,
        rate_limit_archive_repository=rate_limit_archive_repository,
        rate_limit=config.rate_limits,
    )
