# ⚡ Semantic Cache + Cost-Aware Model Router

An AI application that combines semantic caching, intelligent model selection, and API cost tracking to make repeated AI requests more efficient.

## 🚀 Overview

This project routes user questions to different AI models based on question complexity. It uses semantic similarity to identify previously answered questions and reuse cached responses instead of calling the AI provider again.

A Streamlit dashboard displays answers, cache performance, estimated API costs, and recent request history.

## ✨ Features

* **Semantic caching:** Reuses answers to sufficiently similar questions.
* **Cost-aware model routing:** Selects between configured AI models based on question complexity.
* **API cost estimation:** Estimates request costs from token usage and configured pricing rates.
* **Request history:** Stores the 50 most recent requests in Redis.
* **Usage analytics:** Tracks cache hits, misses, request totals, and cache hit rate.
* **Interactive dashboard:** Provides a simple interface built with Streamlit.
* **REST API:** Exposes endpoints through FastAPI.

## 🛠️ Tech Stack

* Python
* FastAPI
* Streamlit
* Redis
* Sentence Transformers
* scikit-learn
* OpenAI Python SDK
* Groq API

## 🏗️ Architecture

1. A user submits a question through the Streamlit dashboard.
2. FastAPI receives the request.
3. The semantic cache compares the question with stored question embeddings.
4. If a sufficiently similar question exists, the cached answer is returned.
5. Otherwise, the router selects a configured AI model and calls the provider.
6. The answer is cached, estimated cost is recorded, and request history is updated.
7. The dashboard displays the answer and usage statistics.

## 📋 Prerequisites

* Python installed
* Redis installed and running
* A Groq API key
* Git

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/maverickph1818-commits/semantic-cache-router.git
cd semantic-cache-router
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the dependencies

```bash
pip install fastapi uvicorn redis python-dotenv openai sentence-transformers scikit-learn streamlit pandas requests
```

### 4. Configure your API key

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace the placeholder with your own API key. Never commit or publish your `.env` file.

### 5. Start Redis

If Redis was installed using Homebrew on macOS:

```bash
brew services start redis
```

Check that it is running:

```bash
redis-cli ping
```

Expected response:

```text
PONG
```

### 6. Start the FastAPI backend

In one terminal:

```bash
source .venv/bin/activate
uvicorn app:app --reload
```

API documentation:

http://127.0.0.1:8000/docs

### 7. Start the Streamlit dashboard

In a second terminal, from the project directory:

```bash
source .venv/bin/activate
streamlit run dashboard.py
```

Open:

http://localhost:8501

## 🔌 API Endpoints

| Method | Endpoint   | Description                      |
| ------ | ---------- | -------------------------------- |
| GET    | `/`        | Check whether the API is running |
| POST   | `/ask`     | Submit a question                |
| GET    | `/stats`   | Retrieve usage statistics        |
| GET    | `/history` | Retrieve recent request history  |

Example request:

```json
{
  "question": "What is RAM?"
}
```

Send this JSON body to `POST /ask`.

## 📊 Metrics

The dashboard tracks:

* Cache hits and cache misses
* Cache hit rate
* Total requests
* Estimated API cost
* Cost of the latest request
* Recent questions and answers

Cost figures are estimates based on configured token rates. Actual provider charges may differ.

## 🔒 Security

* API credentials belong in `.env`.
* `.env` and the virtual environment are excluded using `.gitignore`.
* Never publish API keys, passwords, or other secrets.

## 🗺️ Future Improvements

* Add configurable model-routing rules.
* Improve cache expiration and cache management.
* Add more detailed latency and cost-savings analytics.
* Add automated tests.
* Deploy a public demo.
* Improve dashboard design and usability.

## 👨‍💻 Author

**Piravin Maverick**

GitHub: [@maverickph1818-commits](https://github.com/maverickph1818-commits)

---

Built as a project exploring AI infrastructure, semantic similarity, caching, and cost-aware model routing.
