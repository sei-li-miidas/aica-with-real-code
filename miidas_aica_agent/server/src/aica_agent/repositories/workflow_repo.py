import logging
from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.entities.workflow_answer import WorkflowAnswer
from utils.const import LOGGER_PREFIX
from utils.log_utils import get_session_id


class WorkflowRepository:
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ) -> None:
        self._logger = logging.getLogger(
            f"{LOGGER_PREFIX}.{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._session_factory = session_factory

    def save_workflow_answer(
        self,
        workflow_id: str,
        answers: dict,
    ) -> None:
        """ワークフローの回答を登録または更新する"""
        session_id = get_session_id()
        with self._session_factory() as session:
            stmt = select(WorkflowAnswer).filter(
                WorkflowAnswer.session_id == session_id,
                WorkflowAnswer.workflow_id == workflow_id,
            )
            existing = session.scalars(stmt).first()

            if existing:
                existing.answers = answers
            else:
                new_answer = WorkflowAnswer(
                    session_id=session_id,
                    workflow_id=workflow_id,
                    answers=answers,
                )
                session.add(new_answer)

            session.commit()
