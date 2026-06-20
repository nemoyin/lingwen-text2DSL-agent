"""Query request and response Pydantic schemas."""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Natural-language query sent by the user."""

    question: str = Field(..., min_length=1, description="用户自然语言问题")
    datasource_id: int = Field(..., ge=1, description="目标数据源 ID")
    skill_id: Optional[int] = Field(default=None, ge=1, description="指定 Skill 模板 ID")
    history: Optional[list[dict]] = Field(default=None, description="多轮对话历史，每个元素含 question 和 answer 字段")
    max_context_turns: int = Field(default=6, ge=0, le=20, description="最大上下文轮数")


class QueryResponse(BaseModel):
    """Complete response after the 8-step Agent pipeline."""

    question: str = Field(..., description="原始问题")
    data: List[dict[str, Any]] = Field(default_factory=list, description="查询结果数据（行列表）")
    columns: List[str] = Field(default_factory=list, description="列名列表")
    analysis: str = Field(default="", description="AI 自然语言分析")
    sql: str = Field(default="", description="生成的 SQL 语句")
    chart_suggestion: Optional[dict] = Field(default=None, description="图表建议")
    row_count: int = Field(default=0, description="返回行数")
    is_truncated: bool = Field(default=False, description="是否被截断（超过1000行）")
    latency_ms: float = Field(default=0.0, description="总耗时（毫秒）")
    total_tokens: int = Field(default=0, description="LLM 调用消耗的总 Token 数")
    pipeline_steps: list[dict] = Field(default_factory=list, description="管线各步骤详情")
    suggested_questions: list[str] = Field(default_factory=list, description="LLM 推荐的后续问题（最多3个）")
    history_id: Optional[int] = Field(default=None, description="保存到查询历史后返回的 ID")

    model_config = {"from_attributes": True}
