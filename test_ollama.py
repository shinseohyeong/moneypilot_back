from ollama import Client


client = Client(
    host="http://192.168.0.213:11434",
    timeout=300
)


result = client.embed(
    model="bge-m3",
    input=[
        "금융상품 종류: 예금",
        "우리은행 WON플러스예금 상품입니다."
    ]
)


print(len(result.embeddings))
print(len(result.embeddings[0]))