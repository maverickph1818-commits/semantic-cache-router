
import os
import json
import time
from datetime import datetime, timezone

import redis
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

app = FastAPI(title="Semantic Cache Router")

model = SentenceTransformer("all-MiniLM-L6-v2")

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

SIMILARITY_THRESHOLD = 0.7
CACHE_KEY = "semantic_cache"
COST_KEY = "total_estimated_cost_usd"
CACHE_HITS_KEY = "cache_hits"
CACHE_MISSES_KEY = "cache_misses"
HISTORY_KEY = "request_history"
HISTORY_LIMIT = 50


class Question(BaseModel):
    question: str


def choose_model(question):
    complex_words = [
        "analyze",
        "compare",
        "evaluate",
        "design",
        "architecture",
        "step by step",
        "pros and cons",
        "in detail"
    ]

    question_lower = question.lower()

    for word in complex_words:
        if word in question_lower:
            return "openai/gpt-oss-120b"

    return "openai/gpt-oss-20b"


def ask_ai(question):
    selected_model = choose_model(question)

    print("Selected model:", selected_model)

    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "user", "content": question}
        ]
    )

    answer = response.choices[0].message.content
    usage = response.usage
    estimated_cost = 0.0

    if usage:
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        # Estimated rates in USD per million tokens.
        # Verify provider pricing before relying on these estimates.
        if selected_model == "openai/gpt-oss-120b":
            input_rate = 0.15
            output_rate = 0.60
        else:
            input_rate = 0.075
            output_rate = 0.30

        estimated_cost = (
            input_tokens * input_rate / 1_000_000
            + output_tokens * output_rate / 1_000_000
        )

        print("Input tokens:", input_tokens)
        print("Output tokens:", output_tokens)
        print("Total tokens:", usage.total_tokens)
        print(f"Estimated API cost: ${estimated_cost:.8f}")

    return answer, estimated_cost


def get_cache():
    data = r.get(CACHE_KEY)

    if data:
        return json.loads(data)

    return []


def save_cache(cache):
    r.set(CACHE_KEY, json.dumps(cache), ex=3600)


def add_to_total_cost(cost):
    r.incrbyfloat(COST_KEY, cost)


def get_total_cost():
    total = r.get(COST_KEY)
    return float(total) if total else 0.0


def increment_cache_hits():
    r.incr(CACHE_HITS_KEY)


def increment_cache_misses():
    r.incr(CACHE_MISSES_KEY)


def find_cached_answer(question):
    cache = get_cache()

    if not cache:
        return None

    question_embedding = model.encode(
        [question],
        normalize_embeddings=True
    )

    for item in cache:
        cached_embedding = item["embedding"]

        similarity = cosine_similarity(
            question_embedding,
            [cached_embedding]
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
    ).tolist()

    cache = get_cache()

    cache.append({
        "question": question,
        "embedding": embedding,
        "answer": answer
    })

    save_cache(cache)


def record_request(
    question,
    answer,
    cache_status,
    selected_model,
    cost,
    response_time_ms
):
    entry = {
        "question": question,
        "answer": answer,
        "cache": cache_status,
        "model": selected_model,
        "estimated_cost_usd": float(cost),
        "response_time_ms": round(response_time_ms, 2),
        "timestamp": datetime.now(
            timezone.utc
        ).astimezone().isoformat(timespec="seconds")
    }

    r.lpush(HISTORY_KEY, json.dumps(entry))
    r.ltrim(HISTORY_KEY, 0, HISTORY_LIMIT - 1)


@app.get("/")
def home():
    return {
        "message": "Semantic Cache Router is running!"
    }


@app.get("/stats")
def stats():
    cache_hits = int(r.get(CACHE_HITS_KEY) or 0)
    cache_misses = int(r.get(CACHE_MISSES_KEY) or 0)

    total_requests = cache_hits + cache_misses

    cache_hit_rate = (
        cache_hits / total_requests * 100
        if total_requests > 0
        else 0.0
    )

    return {
        "total_estimated_cost_usd": get_total_cost(),
        "currency": "USD",
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "total_requests": total_requests,
        "cache_hit_rate_percent": round(cache_hit_rate, 2)
    }


@app.get("/history")
def history():
    entries = r.lrange(
        HISTORY_KEY,
        0,
        HISTORY_LIMIT - 1
    )

    return {
        "count": len(entries),
        "limit": HISTORY_LIMIT,
        "history": [
            json.loads(entry)
            for entry in entries
        ]
    }


@app.post("/ask")
def ask(question: Question):
    request_start = time.perf_counter()
    question_text = question.question.strip()

    if not question_text:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    cached_answer = find_cached_answer(question_text)

    if cached_answer is not None:
        increment_cache_hits()

        answer = cached_answer
        cache_status = "HIT"
        selected_model = "cached"
        estimated_cost = 0.0

    else:
        increment_cache_misses()

        selected_model = choose_model(question_text)

        try:
            answer, estimated_cost = ask_ai(question_text)
        except Exception as error:
            raise HTTPException(
                status_code=502,
                detail="The AI provider request failed. Check the backend terminal."
            ) from error

        add_to_total_cost(estimated_cost)
        add_to_cache(question_text, answer)

        cache_status = "MISS"

    response_time_ms = (
        time.perf_counter() - request_start
    ) * 1000

    record_request(
        question_text,
        answer,
        cache_status,
        selected_model,
        estimated_cost,
        response_time_ms
    )

    return {
        "question": question_text,
        "answer": answer,
        "cache": cache_status,
        "model": selected_model,
        "estimated_cost_usd": estimated_cost,
        "total_estimated_cost_usd": get_total_cost(),
        "response_time_ms": round(response_time_ms, 2)
    }