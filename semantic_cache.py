from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

cache = []

SIMILARITY_THRESHOLD = 0.7


def find_cached_answer(question):
    if not cache:
        return None

    question_embedding = model.encode(
        [question],
        normalize_embeddings=True
    )

    for item in cache:
        similarity = cosine_similarity(
            question_embedding,
            [item["embedding"]]
        )[0][0]

        print("Similarity:", similarity)

        if similarity >= SIMILARITY_THRESHOLD:
            print("CACHE HIT")
            return item["answer"]

    print("CACHE MISS")
    return None


def add_to_cache(question, answer):
    embedding = model.encode(
        question,
        normalize_embeddings=True
    )

    cache.append({
        "question": question,
        "embedding": embedding,
        "answer": answer
    })


question1 = "What is RAG?"
answer1 = "RAG stands for Retrieval Augmented Generation."

add_to_cache(question1, answer1)

question2 = "What does RAG mean?"

answer = find_cached_answer(question2)

if answer:
    print("Answer:", answer)
else:
    print("We need to call the AI.")