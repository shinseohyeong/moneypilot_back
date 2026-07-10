import json
from datetime import datetime

from openai import OpenAI

from app.core.config import settings
from app.agent.prompts import AGENT_DECISION_SYSTEM_PROMPT
from app.agent.schemas import AgentDecision


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def decide_agent_action(
    message: str,
    history: list[dict] | None = None,
) -> AgentDecision:
    """
    사용자 질문을 보고 사용할 action과 month를 결정한다.
    """

    current_date = datetime.now().strftime("%Y-%m-%d")

    history_text = ""

    if history:
        history_text = "\n".join(
            [
                f"{item.get('role')}: {item.get('content')}"
                for item in history[-6:]
            ]
        )

    user_prompt = f"""
현재 날짜: {current_date}

최근 대화:
{history_text}

사용자 질문:
{message}

위 질문에 대해 사용할 action과 month를 JSON으로 반환해줘.
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": AGENT_DECISION_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
        return AgentDecision(**data)

    except Exception:
        return AgentDecision(
            action="general",
            month=None,
            reason="LLM Router JSON 파싱 실패",
        )