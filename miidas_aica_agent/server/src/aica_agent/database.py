"""
DB接続
"""

from contextlib import contextmanager
from typing import Generator
import logging

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session, declarative_base

from utils.const import LOGGER_PREFIX

Base = declarative_base()


class Database:
    def __init__(self, db_url: str) -> None:
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._engine = create_engine(db_url)
        self._session_factory = orm.scoped_session(
            orm.sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            ),
        )

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session: Session = self._session_factory()
        try:
            yield session
        except Exception:
            self._logger.exception("DBセッションロールバック")
            session.rollback()
            raise
        finally:
            session.close()
