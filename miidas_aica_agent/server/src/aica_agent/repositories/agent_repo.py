from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from domain.entities.agent import Agent
from domain.entities.workflow import Workflow


class AgentRepository:
    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
    ) -> None:
        self._session_factory = session_factory

    def get_agents(self) -> list[Agent]:
        """
        ・エージェント
        ・エージェントに紐づいたツール
        ・ハンドオフ先のエージェント
        を取得する。

        Returns:
            エージェント一覧
        """
        with self._session_factory() as session:
            stmt = (
                select(Agent)
                .options(
                    joinedload(Agent.tools),
                    joinedload(
                        Agent.next_agents.and_(Workflow.dest_agent.has())
                    ).joinedload(Workflow.dest_agent),
                )
                .where(Agent.deleted_at.is_(None))
            )
            return session.scalars(stmt).unique().all()
