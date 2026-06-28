"""QueryAgent — the main LangGraph StateGraph orchestrating the Text2SQL pipeline."""

import logging
import time
from typing import Any, AsyncGenerator, Dict, Literal

from langchain_deepseek import ChatDeepSeek
from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.intent_recognition import IntentRecognitionNode
from app.agent.nodes.permission_check import PermissionCheckNode
from app.agent.nodes.rag_retrieval import RAGRetrievalNode
from app.agent.nodes.sql_generation import SQLGenerationNode
from app.agent.nodes.sql_validation import SQLValidationNode
from app.agent.nodes.sql_execution import SQLExecutionNode
from app.agent.nodes.result_wrapping import ResultWrappingNode
from app.agent.nodes.final_response import FinalResponseNode
from app.config import settings
from app.rag.embeddings import EmbeddingClient
from app.rag.vector_store import VectorStore
from app.rag.retriever import SchemaRetriever, FewShotRetriever
from app.security.sql_guard import SqlGuard

logger = logging.getLogger(__name__)

# Maximum number of SQL generation retries
_MAX_RETRIES: int = 2


def _format_rag_detail(schemas: list, examples: list) -> str:
    """Format a human-readable RAG retrieval summary with table names and example questions.

    Args:
        schemas: List of dicts with ``metadata.table_name`` and ``content``.
        examples: List of dicts with ``content`` (question→SQL pairs).

    Returns:
        A multi-line string or single summary line.
    """
    parts = []
    if schemas:
        table_names = []
        for s in schemas:
            name = (s.get("metadata", {}) or {}).get("table_name", "")
            if name:
                table_names.append(f"「{name}」")
            else:
                # Fallback: extract first line or first 40 chars from content
                content = str(s.get("content", "") or "").strip()
                first_line = content.split("\n")[0][:40]
                if first_line:
                    table_names.append(f"「{first_line}」")
        if table_names:
            parts.append(f"\u5339\u914d {len(schemas)} \u4e2a\u76f8\u5173\u8868\u7ed3\u6784\uff1a{', '.join(table_names)}")
        else:
            parts.append(f"\u5339\u914d {len(schemas)} \u4e2a\u76f8\u5173\u8868\u7ed3\u6784")
    if examples:
        example_questions = []
        for e in examples:
            content = str(e.get("content", "") or "").strip()
            # The content format is typically "question: ...\nSQL: ..."
            # Extract the question part
            q_part = content
            for line in content.split("\n"):
                line = line.strip()
                if line.lower().startswith("question:") or line.lower().startswith("问题"):
                    q_part = line.split(":", 1)[-1].strip()[:50]
                    break
                elif line.lower().startswith("sql:") or line.lower().startswith("sql语句"):
                    continue
                elif line and not q_part.startswith("question:"):
                    q_part = line[:50]
                    break
            if not q_part:
                q_part = content[:50]
            example_questions.append(f"\u300c{q_part}\u300d")
        parts.append(f"{len(examples)} \u6761\u76f8\u4f3c\u67e5\u8be2\u793a\u4f8b\uff1a{'; '.join(example_questions)}")
    if not parts:
        parts.append("\u65e0\u5339\u914d\u7684RAG\u7ed3\u679c\uff0c\u4f7f\u7528\u5143\u6570\u636e\u56de\u9000")
    return "\n".join(parts)


def _build_step_reasoning(node_name: str, node_output: dict) -> str:
    """Build a human-readable fallback description for a pipeline step.

    Used when the node doesn't produce explicit reasoning text (e.g.
    non-LLM nodes or LLM nodes with empty CoT/reasoning_content).
    """
    if node_name == "intent_rec":
        intent = node_output.get("intent", {}) or {}
        skill = intent.get("skill_name", "通用查询")
        return f"识别用户意图，匹配技能「{skill}」"

    if node_name == "perm_check":
        status = node_output.get("status", "")
        if status == "auth_failed":
            return "权限校验失败：当前用户无此数据源访问权限"
        return "数据源权限验证通过，允许继续查询"

    if node_name == "rag_retrieve":
        schemas = node_output.get("retrieved_schemas", [])
        examples = node_output.get("retrieved_examples", [])
        return _format_rag_detail(schemas, examples)

    if node_name == "sql_validate":
        err = node_output.get("error_info", "")
        if err:
            return f"SQL 安全审计拦截: {str(err)[:200]}"
        executed_sql = str(node_output.get("executed_sql", "") or "")
        if executed_sql:
            return f"SQL 安全审计通过（已注入 LIMIT 1000，{len(executed_sql)} 字符）"
        return "SQL 安全审计完成"

    if node_name == "sql_exec":
        rows = node_output.get("execution_result", [])
        error = node_output.get("error_info")
        if error:
            return f"SQL 执行出错：{str(error)[:200]}"
        return f"查询执行完成，返回 {len(rows)} 行数据"

    if node_name == "result_wrap":
        analysis = str(node_output.get("ai_analysis", "") or "")
        if analysis:
            return f"数据解读完成：{analysis[:200]}"
        return "正在解读查询结果并生成分析报告"

    if node_name == "sql_gen":
        sql = str(node_output.get("generated_sql", "") or "")
        if sql:
            return f"生成SQL语句（{len(sql)} 字符）"
        return "正在调用大模型生成 SQL 查询"

    return ""


class QueryAgent:
    """LangGraph-based agent that converts natural-language questions to SQL.

    The pipeline has 8 nodes connected in a StateGraph:

    1. **intent_rec** — identifies which Skill to use.
    2. **perm_check** — validates the data source is active.
    3. **rag_retrieve** — retrieves relevant schemas and few-shot examples.
    4. **sql_gen** — generates SQL with CoT reasoning (LLM call).
    5. **sql_validate** — runs security checks and injects LIMIT.
    6. **sql_exec** — executes the SQL on the user's data source.
    7. **result_wrap** — wraps results with LLM analysis + chart suggestion.
    8. **final** — assembles the final response dict.

    Conditional routing:
        - ``perm_check`` → ``result_wrap`` on ``auth_failed``.
        - ``sql_exec`` → ``sql_gen`` on failure (up to 2 retries).
        - ``sql_exec`` → ``result_wrap`` on success or after exhausting retries.

    Usage::

        agent = QueryAgent()
        result = await agent.run(
            question="今年销售额最高的10个产品是哪些？",
            datasource_id=1,
            user_id=1,
        )
    """

    def __init__(self, llm=None) -> None:
        # ---- LLM (accept external instance; fall back to settings) ----
        if llm is not None:
            self._llm = llm
        else:
            logger.warning("No LLM provided — falling back to settings (may be unconfigured)")
            self._llm = ChatDeepSeek(
                model=settings.llm_model,
                api_key=settings.llm_api_key or "sk-placeholder",
                temperature=0.1,
            )

        # ---- Embeddings & Vector Store ----
        self._embed_client: EmbeddingClient = EmbeddingClient()
        self._vector_store: VectorStore = VectorStore()

        # ---- Retrievers ----
        self._schema_retriever: SchemaRetriever = SchemaRetriever(
            self._embed_client, self._vector_store
        )
        self._fewshot_retriever: FewShotRetriever = FewShotRetriever(
            self._embed_client, self._vector_store
        )

        # ---- Security ----
        self._sql_guard: SqlGuard = SqlGuard()

        # ---- 8 Nodes ----
        self._intent_rec_node = IntentRecognitionNode()
        self._perm_check_node = PermissionCheckNode()
        self._rag_retrieve_node = RAGRetrievalNode(
            self._schema_retriever, self._fewshot_retriever
        )
        self._sql_gen_node = SQLGenerationNode(self._llm)
        self._sql_validate_node = SQLValidationNode(self._sql_guard)
        self._sql_exec_node = SQLExecutionNode()
        self._result_wrap_node = ResultWrappingNode(self._llm)
        self._final_node = FinalResponseNode()

        # ---- Build & Compile Graph ----
        self._graph = self._build_graph()

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self):
        """Construct and compile the StateGraph."""

        builder = StateGraph(AgentState)

        # Add all nodes
        builder.add_node("intent_rec", self._intent_rec_node)
        builder.add_node("perm_check", self._perm_check_node)
        builder.add_node("rag_retrieve", self._rag_retrieve_node)
        builder.add_node("sql_gen", self._sql_gen_node)
        builder.add_node("sql_validate", self._sql_validate_node)
        builder.add_node("sql_exec", self._sql_exec_node)
        builder.add_node("result_wrap", self._result_wrap_node)
        builder.add_node("final", self._final_node)

        # Entry point
        builder.set_entry_point("intent_rec")

        # Serial edges
        builder.add_edge("intent_rec", "perm_check")
        builder.add_edge("rag_retrieve", "sql_gen")
        builder.add_edge("sql_gen", "sql_validate")
        builder.add_edge("result_wrap", "final")
        builder.add_edge("final", END)

        # Conditional: perm_check → rag_retrieve or result_wrap
        builder.add_conditional_edges(
            "perm_check",
            self._route_after_perm_check,
            {
                "rag_retrieve": "rag_retrieve",
                "result_wrap": "result_wrap",
            },
        )

        # Conditional: sql_validate → sql_exec or result_wrap (skip retry for dangerous SQL)
        builder.add_conditional_edges(
            "sql_validate",
            self._route_after_sql_validate,
            {
                "sql_exec": "sql_exec",
                "result_wrap": "result_wrap",
            },
        )

        # Conditional: sql_exec → sql_gen (retry) or result_wrap
        builder.add_conditional_edges(
            "sql_exec",
            self._route_after_sql_exec,
            {
                "sql_gen": "sql_gen",
                "result_wrap": "result_wrap",
            },
        )

        compiled = builder.compile()
        logger.info("QueryAgent StateGraph compiled successfully")
        return compiled

    # ------------------------------------------------------------------
    # Routing functions
    # ------------------------------------------------------------------

    @staticmethod
    def _route_after_perm_check(state: AgentState) -> Literal["rag_retrieve", "result_wrap"]:
        """Route after permission check.

        Returns:
            ``"rag_retrieve"`` if the data source is active,
            ``"result_wrap"`` if auth failed.
        """
        status: str = state.get("status", "")
        if status == "auth_failed":
            logger.warning("Permission check failed — routing to result_wrap")
            return "result_wrap"
        return "rag_retrieve"

    @staticmethod
    def _route_after_sql_validate(state: AgentState) -> Literal["sql_exec", "result_wrap"]:
        """Route after SQL validation.

        Dangerous operations (DROP, DELETE, etc.) skip retry and go
        straight to result_wrap.  Recoverable errors proceed to execution
        where the existing retry logic handles them.
        """
        error: str | None = state.get("error_info")
        if error and ("禁止" in error or "注入" in error):
            logger.warning("SQL validation blocked dangerous operation — routing to result_wrap")
            return "result_wrap"
        return "sql_exec"

    @staticmethod
    def _route_after_sql_exec(state: AgentState) -> Literal["sql_gen", "result_wrap"]:
        """Route after SQL execution.

        Returns:
            ``"sql_gen"`` if execution failed AND retry count < 2,
            ``"result_wrap"`` if success or retries exhausted.
        """
        status: str = state.get("status", "")
        retry_count: int = state.get("retry_count", 0)

        if status == "success":
            logger.info("SQL execution succeeded — routing to result_wrap")
            return "result_wrap"

        if retry_count < _MAX_RETRIES:
            logger.info(
                "SQL execution failed (retry %d/%d) — routing to sql_gen",
                retry_count + 1, _MAX_RETRIES,
            )
            return "sql_gen"

        logger.warning(
            "SQL execution failed after %d retries — routing to result_wrap",
            retry_count,
        )
        return "result_wrap"

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    async def run(
        self, question: str, datasource_id: int, user_id: int,
        history: list[dict] | None = None, max_context_turns: int = 6,
    ) -> Dict[str, Any]:
        history_context = (history or [])[-max_context_turns:] if max_context_turns > 0 else []
        logger.info(
            "QueryAgent.run: ds=%d user=%d question=%s history=%d turns",
            datasource_id, user_id, question[:100], len(history_context),
        )

        initial_state: AgentState = {
            "question": question, "datasource_id": datasource_id, "user_id": user_id,
            "intent": None, "retrieved_schemas": [], "retrieved_examples": [],
            "cot_reasoning": "", "generated_sql": "", "executed_sql": "",
            "execution_result": [], "ai_analysis": "", "chart_suggestion": None,
            "error_info": None, "retry_count": 0, "status": "init", "final_result": None,
            "history": history_context,
            "suggested_questions": [],
        }

        pipeline_steps = []
        node_times = {}  # node_name -> (start, end)

        # Collect node-level timestamps via stream
        t_start = time.time()
        last_node = None
        async for event in self._graph.astream(initial_state, stream_mode="updates"):
            for node_name, _update in event.items():
                now = time.time()
                if last_node and last_node not in node_times:
                    node_times[last_node] = t_start
                if node_name not in node_times:
                    node_times[node_name] = now
                last_node = node_name

        # Reconstruct final state
        final_state_result = await self._graph.ainvoke(initial_state)
        fs = final_state_result

        # Helper: map node name to approximate elapsed time from node_times
        node_step_map = {
            "intent_rec": "意图识别", "perm_check": "权限校验", "rag_retrieve": "RAG检索",
            "sql_gen": "SQL生成", "sql_validate": "安全审计", "sql_exec": "SQL执行",
            "result_wrap": "结果分析", "final": "响应组装",
        }
        prev_time = t_start
        def node_elapsed(node: str) -> int:
            nonlocal prev_time
            if node in node_times:
                t = node_times[node]
                dur = int((t - prev_time) * 1000)
                prev_time = t
                return max(dur, 0)
            return 0

        def add_step(node: str, label: str, detail: str = "", status: str = "ok"):
            pipeline_steps.append({
                "step": label, "status": status,
                "detail": detail[:300], "elapsed_ms": node_elapsed(node)
            })

        intent = fs.get("intent", {})
        add_step("intent_rec", "意图识别", f"识别结果: {intent.get('skill_name', '通用查询') if isinstance(intent, dict) else '通用查询'}")

        if fs.get("status") == "auth_failed":
            add_step("perm_check", "权限校验", "数据源验证失败", "error")
        else:
            add_step("perm_check", "权限校验", "数据源验证通过")

        schemas = fs.get("retrieved_schemas", [])
        examples = fs.get("retrieved_examples", [])
        add_step("rag_retrieve", "RAG检索", _format_rag_detail(schemas, examples))

        cot = fs.get("cot_reasoning", "")
        sql = fs.get("generated_sql", "")
        retry = fs.get("retry_count", 0)
        add_step("sql_gen", "SQL生成", f"{'CoT推理完成' if cot else '生成SQL'}\n{sql[:200]}" + (f"\n(重试{retry}次)" if retry else ""))

        val_err = fs.get("error_info", "")
        val_ok = not val_err or ("禁止" not in val_err and "注入" not in val_err)
        add_step("sql_validate", "安全审计",
            "SQL 安全校验通过" if val_ok else val_err[:100],
            "ok" if val_ok else "error")

        rows = fs.get("execution_result", [])
        err = fs.get("error_info", "")
        if err:
            add_step("sql_exec", "SQL执行", err[:200], "error")
        else:
            add_step("sql_exec", "SQL执行", f"返回 {len(rows)} 行")

        add_step("result_wrap", "结果分析", fs.get("ai_analysis", "")[:200])
        add_step("final", "响应组装", f"总耗时 {round((time.time()-t_start)*1000)}ms")

        result: Dict[str, Any] = fs.get("final_result", {}) or dict(fs)
        result["pipeline_steps"] = pipeline_steps
        logger.info("Pipeline steps collected: %d steps", len(pipeline_steps))

        return result

    # ------------------------------------------------------------------
    # Streaming run — yields SSE progress events
    # ------------------------------------------------------------------

    _STEP_MAP = {
        "intent_rec": "意图识别", "perm_check": "权限校验", "rag_retrieve": "RAG检索",
        "sql_gen": "SQL生成", "sql_validate": "安全审计", "sql_exec": "SQL执行",
        "result_wrap": "结果分析",
    }

    async def run_stream(
        self, question: str, datasource_id: int, user_id: int,
        history: list[dict] | None = None,         max_context_turns: int = 6,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the pipeline and yield SSE progress events for each node.

        Yielded event format::

            {"event": "step", "step": "意图识别", "status": "completed", "elapsed_ms": 5}
            {"event": "step", "step": "权限校验", "status": "completed", "elapsed_ms": 3}
            ...
            {"event": "done", "data": {...}}
        """
        history_context = (history or [])[-max_context_turns:] if max_context_turns > 0 else []
        logger.info("QueryAgent.run_stream: ds=%d user=%d question=%s", datasource_id, user_id, question[:100])

        initial_state: AgentState = {
            "question": question, "datasource_id": datasource_id, "user_id": user_id,
            "intent": None, "retrieved_schemas": [], "retrieved_examples": [],
            "cot_reasoning": "", "generated_sql": "", "executed_sql": "",
            "execution_result": [], "ai_analysis": "", "chart_suggestion": None,
            "error_info": None, "retry_count": 0, "status": "init", "final_result": None,
            "history": history_context,
            "suggested_questions": [],
            "native_reasoning": "",
        }

        t_start = time.time()
        prev_time = t_start
        completed_steps = set()
        step_elapsed: dict[str, int] = {}  # step_name -> elapsed_ms

        # Stream each node completion and capture reasoning text
        accumulated_reasoning: list[str] = []
        reasoning_nodes = {"sql_gen", "result_wrap"}

        async for event in self._graph.astream(initial_state, stream_mode="updates"):
            for node_name in event:
                step_name = self._STEP_MAP.get(node_name)
                if not step_name or node_name in completed_steps:
                    continue
                completed_steps.add(node_name)
                now = time.time()
                elapsed = max(int((now - prev_time) * 1000), 0)
                prev_time = now
                step_elapsed[step_name] = elapsed

                node_output = event[node_name]

                # Extract reasoning from LLM-calling nodes
                # Priority: native reasoning_content > prompt-based CoT > generated SQL
                reasoning = ""
                if node_name in reasoning_nodes:
                    native = str(node_output.get("native_reasoning", "") or "")
                    if native:
                        reasoning = native
                    elif node_name == "sql_gen":
                        cot = str(node_output.get("cot_reasoning", "") or "").strip()
                        if cot:
                            reasoning = cot
                        else:
                            sql = str(node_output.get("generated_sql", "") or "")
                            if sql:
                                reasoning = f"生成SQL:\n{sql}"

                # ---- Fallback descriptions for ALL pipeline steps ----
                if not reasoning:
                    reasoning = _build_step_reasoning(node_name, node_output)

                if reasoning:
                    accumulated_reasoning.append(reasoning)

                logger.info("[Pipeline|%s] streaming progress, reasoning=%dchars",
                           step_name, len(reasoning))
                yield {
                    "event": "step",
                    "step": step_name,
                    "status": "completed",
                    "elapsed_ms": elapsed,
                    "reasoning": reasoning,
                }

        # Final invoke to get completed state
        fs = await self._graph.ainvoke(initial_state)
        final = fs.get("final_result", {}) or dict(fs)

        # Build pipeline_steps with real elapsed times from step events
        pipeline_steps = []
        # Compute per-step elapsed times using a running clock
        step_clock = t_start
        step_details = {
            "意图识别": {
                "detail": f"识别结果: {(fs.get('intent', {}) or {}).get('skill_name', '通用查询')}",
            },
            "权限校验": {
                "detail": "数据源验证通过" if fs.get("status") != "auth_failed" else "验证失败",
            },
            "RAG检索": {
                "detail": _format_rag_detail(fs.get("retrieved_schemas", []), fs.get("retrieved_examples", [])),
            },
            "SQL生成": {
                "detail": f"生成SQL ({len(fs.get('generated_sql', ''))} chars)"
                    + (f" (重试{fs.get('retry_count', 0)}次)" if fs.get('retry_count') else "")
                    + f"\n推理: {str(fs.get('native_reasoning', '') or fs.get('cot_reasoning', ''))[:300]}",
            },
            "安全审计": {
                "detail": "SQL 安全校验通过" if not fs.get("error_info") or ("禁止" not in str(fs.get("error_info","")) and "注入" not in str(fs.get("error_info",""))) else str(fs.get("error_info", ""))[:100],
                "status": "ok" if not fs.get("error_info") or ("禁止" not in str(fs.get("error_info","")) and "注入" not in str(fs.get("error_info",""))) else "error",
            },
            "SQL执行": {
                "detail": f"返回 {len(fs.get('execution_result', []))} 行" if not fs.get("error_info")
                    else str(fs.get("error_info", ""))[:100],
                "status": "ok" if not fs.get("error_info") else "error",
            },
            "结果分析": {
                "detail": fs.get("ai_analysis", "")[:200],
            },
        }
        for node_name, step_name in self._STEP_MAP.items():
            if node_name in completed_steps:
                detail_info = step_details.get(step_name, {})
                # Use tracked elapsed or compute based on running clock
                dur = step_elapsed.get(step_name, 0)
                if dur <= 0:
                    now = time.time()
                    dur = max(int((now - step_clock) * 1000), 0)
                    step_clock = now
                pipeline_steps.append({
                    "step": step_name,
                    "status": detail_info.get("status", "ok"),
                    "detail": detail_info.get("detail", ""),
                    "elapsed_ms": dur,
                })

        # Inject pipeline_steps and latency into final result
        total_latency = round((time.time() - t_start) * 1000)
        final["pipeline_steps"] = pipeline_steps
        final["latency_ms"] = total_latency

        yield {
            "event": "done",
            "data": final,
        }

