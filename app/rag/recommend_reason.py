from ollama import Client

from app.core.config import settings

client = Client(
    host=settings.ollama_base_url.rstrip("/"),
)


def generate_reason(
    question: str,
    documents: list[str]
):

    context = "\n\n".join(documents)

    prompt = f"""
        너는 금융상품 추천 전문가이다.

        사용자 정보
        {question}

        추천 대상 상품 정보
        {context}

        아래 규칙을 반드시 지켜라.

        [필수 규칙]
        - 추천 대상 상품은 위의 '추천 대상 상품 정보'에 있는 상품 하나뿐이다.
        - 추천 대상 상품명을 그대로 사용한다.
        - 다른 금융상품명은 절대로 언급하지 않는다.
        - 다른 상품과 비교하지 않는다.
        - context에 없는 특징, 혜택, 가입조건, 우대금리 등을 절대로 만들어내지 않는다.
        - 사용자의 가입기간과 예치금액을 반영하여 왜 적합한지만 설명한다.
        - "경쟁력 있는 금리", "높은 수익", "우수한 혜택"처럼 근거 없는 표현은 사용하지 않는다.
        - 2~3문장의 자연스러운 한국어로 작성한다.
        - 추천 이유만 출력한다.
        """


    response = client.chat(
        model=settings.ollama_llm_model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "num_ctx": 2048,
            "temperature": 0.3,
        }
    )


    return response["message"]["content"]