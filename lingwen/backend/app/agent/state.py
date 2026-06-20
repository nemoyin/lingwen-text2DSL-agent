"""Agent state definition for the LangGraph QueryAgent.

The :class:`AgentState` carries all data through the 8-node pipeline,
from intent recognition to final response assembly.
"""

from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    """Shared state dictionary flowing through the Agent's StateGraph.

    Each node reads from and writes back to this state.  Fields marked
    ``Optional`` may be absent during early pipeline stages.
    """

    # Inputs
    question: str
    datasource_id: int
    user_id: int

    # Intent recognition output
    intent: Optional[dict]

    # RAG retrieval outputs
    retrieved_schemas: list[dict]
    retrieved_examples: list[dict]

    # SQL generation outputs
    cot_reasoning: str
    generated_sql: str
    native_reasoning: str

    # SQL validation / execution outputs
    executed_sql: str
    execution_result: list[dict]

    # Result wrapping outputs
    ai_analysis: str
    chart_suggestion: Optional[dict]

    # Error & retry tracking
    error_info: Optional[str]
    retry_count: int

    # Pipeline status: init | auth_failed | failed | success
    status: str

    # Final assembled output (populated by final_response node)
    final_result: Optional[dict]

    # Multi-turn conversation context
    history: list[dict]
    suggested_questions: list[str]

    # Pipeline steps for transparency
    pipeline_steps: list[dict]
