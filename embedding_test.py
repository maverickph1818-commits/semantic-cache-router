from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [
    "A dog is running in the park.",
    "A puppy is playing outside."
]

embeddings = model.encode(texts, normalize_embeddings=True)

similarity = cosine_similarity(
    [embeddings[0]],
    [embeddings[1]]
)[0][0]

print("Text 1:", texts[0])
print("Text 2:", texts[1])
print("Similarity:", similarity)