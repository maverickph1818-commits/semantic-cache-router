import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

r.set("test_question", "RAG stands for Retrieval Augmented Generation.")

answer = r.get("test_question")

print("Stored answer:", answer)