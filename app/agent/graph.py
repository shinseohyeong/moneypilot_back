from sqlalchemy.orm import Session

from app.agent.answer_builder import build_llm_answer, build_rule_based_answer
from app.agent.llm_router import decide_agent_action
from app.agent.state import AgentState
from app.agent.tool_registry import run_registered_tool


def run_agent_graph(
    db: Session,
    user_id: int,
    session_id: int,
    message: str,
    history: list[dict] | None = None,
) -> AgentState:
    """
    Agent 공통 실행 흐름.

    1. LLM Router가 action/month 결정
    2. action에 맞는 tool/RAG 실행
    3. 정확한 수치 답변은 rule 기반 생성
    4. RAG/일반 답변은 LLM으로 생성
    """

    decision = decide_agent_action(
        message=message,
        history=history,
    )

    action = decision.action
    month = decision.month

    state: AgentState = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message,
        "month": month,
        "history": history or [],
        "intent": action,
        "tool_result": None,
        "rag_result": None,
        "chat_rag_result": None,
        "answer": "",
        "error": None,
    }

    if action == "general":
        state["answer"] = build_llm_answer(
            message=message,
            action=action,
            history=history,
        )
        return state

    result = run_registered_tool(
        db=db,
        action=action,
        user_id=user_id,
        message=message,
        month=month,
    )

    if action == "spending_report":
        state["rag_result"] = result
    elif action == "agent_chat_rag":
        state["chat_rag_result"] = result
    else:
        state["tool_result"] = result

    if not result.get("success"):
        state["error"] = result.get("message")
        state["answer"] = result.get("message", "요청을 처리하지 못했습니다.")
        return state

    rule_answer = build_rule_based_answer(
        action=action,
        tool_result=result,
    )

    if rule_answer:
        state["answer"] = rule_answer
        return state

    state["answer"] = build_llm_answer(
        message=message,
        action=action,
        tool_result=state.get("tool_result"),
        rag_result=state.get("rag_result") or state.get("chat_rag_result"),
        history=history,
    )

    return state