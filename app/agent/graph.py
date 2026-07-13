from typing import Literal

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agent.answer_builder import (
    build_llm_answer,
    build_rule_based_answer,
)
from app.agent.decision_router import decide_agent_action
from app.agent.state import AgentState
from app.agent.tool_registry import run_registered_tool


TOOL_ACTIONS = {
    "spending_summary",
    "spending_category",
    "spending_report",
    "stock_price",
    "agent_chat_rag",
}


def decide_action_node(
    state: AgentState,
) -> AgentState:
    """
    사용자 질문을 분석해 action과 month를 결정한다.
    """

    decision = decide_agent_action(
        message=state["message"],
        history=state.get("history"),
    )

    return {
        "intent": decision.action,
        "month": decision.month,
        "error": None,
    }


def route_after_decision(
    state: AgentState,
) -> Literal["tool", "answer"]:
    """
    Tool이 필요한 action인지 판단한다.
    """

    if state["intent"] in TOOL_ACTIONS:
        return "tool"

    return "answer"


def execute_tool_node(
    state: AgentState,
    db: Session,
) -> AgentState:
    """
    action에 맞는 DB Tool 또는 RAG 검색 Tool을 실행한다.
    결과 종류에 따라 서로 다른 State 필드에 저장한다.
    """

    action = state["intent"]

    result = run_registered_tool(
        db=db,
        action=action,
        user_id=state["user_id"],
        message=state["message"],
        month=state.get("month"),
    )

    if action == "spending_report":
        return {
            "tool_result": None,
            "rag_result": result,
            "chat_rag_result": None,
        }

    if action == "agent_chat_rag":
        return {
            "tool_result": None,
            "rag_result": None,
            "chat_rag_result": result,
        }

    return {
        "tool_result": result,
        "rag_result": None,
        "chat_rag_result": None,
    }


def get_failed_result_message(
    state: AgentState,
) -> str | None:
    """
    실행한 Tool 또는 RAG 검색이 실패했으면 사용자용 메시지를 반환한다.
    """

    for key in (
        "tool_result",
        "rag_result",
        "chat_rag_result",
    ):
        result = state.get(key)

        if result and not result.get("success"):
            return result.get(
                "message",
                "관련 데이터를 찾지 못했습니다.",
            )

    return None


def generate_answer_node(
    state: AgentState,
) -> AgentState:
    """
    정확한 수치 질문은 규칙 기반으로,
    일반 질문과 RAG 질문은 Ollama로 답변한다.
    """

    failed_message = get_failed_result_message(state)

    if failed_message:
        return {
            "answer": failed_message,
        }

    rule_based_answer = build_rule_based_answer(
        action=state["intent"],
        tool_result=state.get("tool_result"),
    )

    if rule_based_answer:
        return {
            "answer": rule_based_answer,
        }

    answer = build_llm_answer(
        message=state["message"],
        action=state["intent"],
        tool_result=state.get("tool_result"),
        rag_result=state.get("rag_result"),
        chat_rag_result=state.get("chat_rag_result"),
        history=state.get("history"),
    )

    return {
        "answer": answer,
    }


def build_agent_graph(
    db: Session,
):
    """
    DB Session을 사용하는 LangGraph를 생성한다.
    """

    workflow = StateGraph(AgentState)

    workflow.add_node(
        "decide_action",
        decide_action_node,
    )

    workflow.add_node(
        "execute_tool",
        lambda state: execute_tool_node(
            state=state,
            db=db,
        ),
    )

    workflow.add_node(
        "generate_answer",
        generate_answer_node,
    )

    workflow.set_entry_point("decide_action")

    workflow.add_conditional_edges(
        "decide_action",
        route_after_decision,
        {
            "tool": "execute_tool",
            "answer": "generate_answer",
        },
    )

    workflow.add_edge(
        "execute_tool",
        "generate_answer",
    )

    workflow.add_edge(
        "generate_answer",
        END,
    )

    return workflow.compile()


def run_agent_graph(
    db: Session,
    user_id: int,
    session_id: int,
    message: str,
    history: list[dict] | None = None,
) -> dict:
    """
    Agent Graph 실행 진입점.
    """

    graph = build_agent_graph(db)

    initial_state: AgentState = {
        "user_id": user_id,
        "session_id": session_id,
        "message": message,
        "month": None,
        "history": history or [],
        "intent": "general",
        "tool_result": None,
        "rag_result": None,
        "chat_rag_result": None,
        "answer": "",
        "error": None,
    }

    result = graph.invoke(initial_state)

    return dict(result)