from ollama import Client
from app.core.config import settings


client = Client(
    host=settings.ollama_base_url
)


print("HOST:", settings.ollama_base_url)
print("MODEL:", settings.ollama_llm_model)


response = client.chat(
    model=settings.ollama_llm_model,
    messages=[
        {
            "role": "user",
            "content": "예금 추천 이유 한 줄만 알려줘"
        }
    ],
    options={
        "temperature":0.3
    }
)


print(response["message"]["content"])