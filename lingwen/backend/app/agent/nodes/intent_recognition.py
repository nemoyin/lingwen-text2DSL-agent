"""Intent recognition node — identifies which Skill to use for the query."""

import logging
import time
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.models.database import async_session
from app.services import skill_service

logger = logging.getLogger(__name__)


class IntentRecognitionNode:
    """Determines the active skill template for the incoming question.

    Queries the database for the first active :class:`SkillTemplate` and
    attaches its identity to the agent state.
    """

    async def __call__(self, state: AgentState) -> Dict:
        """Execute intent recognition.

        Args:
            state: The current agent state with at least ``question``,
                ``datasource_id``, and ``user_id``.

        Returns:
            A partial state update with ``intent`` and ``status``.
        """
        question = state.get("question", "")
        t0 = time.time()
        logger.info("[Pipeline|意图识别] 开始识别, question=%s", question[:60])

        async with async_session() as db:
            skill = await skill_service.get_active(db)
            if skill is None:
                elapsed = round((time.time() - t0) * 1000)
                logger.warning("[Pipeline|意图识别] 无活跃Skill, 使用fallback, elapsed=%dms", elapsed)
                return {
                    "intent": {"skill_name": "智能问数", "skill_id": 0},
                    "status": "init",
                }

            elapsed = round((time.time() - t0) * 1000)
            logger.info("[Pipeline|意图识别] 完成, skill_name=%s skill_id=%d elapsed=%dms",
                        skill.name, skill.id, elapsed)
            return {
                "intent": {
                    "skill_name": skill.name,
                    "skill_id": skill.id,
                },
                "status": "init",
            }
