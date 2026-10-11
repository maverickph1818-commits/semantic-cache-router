
import requests
import streamlit as st
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Semantic Cache Router",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Semantic Cache Router")
st.caption(
    "AI model routing, semantic caching and cost tracking"
)

st.subheader("Ask the AI")

question = st.text_area(
    "Enter your question",
    placeholder="Ask something here...",
    height=120
)

if st.button("Ask AI", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Getting your answer..."):
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question},
                    timeout=180
                )
                response.raise_for_status()
                result = response.json()

            st.session_state["last_result"] = result

        except requests.RequestException as error:
            st.error(f"Could not connect to the API: {error}")

if "last_result" in st.session_state:
    result = st.session_state["last_result"]

    st.subheader("Latest Response")

    col1, col2, col3 = st.columns(3)

    col1.metric("Cache Status", result["cache"])
    col2.metric("Selected Model", result["model"])
    col3.metric(
        "Request Cost (USD)",
        f'${result["estimated_cost_usd"]:.8f}'
    )

    st.markdown("### Answer")
    st.markdown(result["answer"])

st.divider()
st.subheader("Usage Statistics")

if st.button("Refresh Statistics"):
    st.rerun()

try:
    stats_response = requests.get(
        f"{API_URL}/stats",
        timeout=10
    )
    stats_response.raise_for_status()
    stats = stats_response.json()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Estimated Cost",
        f'${stats["total_estimated_cost_usd"]:.6f}'
    )

    col2.metric(
        "Total Requests",
        stats["total_requests"]
    )

    col3.metric(
        "Cache Hit Rate",
        f'{stats["cache_hit_rate_percent"]:.2f}%'
    )

    col4, col5 = st.columns(2)

    col4.metric("Cache Hits", stats["cache_hits"])
    col5.metric("Cache Misses", stats["cache_misses"])

    st.markdown("### Cache Performance")

    chart_data = pd.DataFrame({
        "Request Type": ["Cache Hits", "Cache Misses"],
        "Requests": [
            stats["cache_hits"],
            stats["cache_misses"]
        ]
    })

    st.bar_chart(
        chart_data,
        x="Request Type",
        y="Requests"
    )

except requests.RequestException:
    st.error(
        "Cannot load statistics. Make sure your FastAPI server is running."
    )

st.divider()
st.subheader("Request History")

st.caption(
    "Your 50 most recent requests are stored in Redis, newest first."
)

if st.button("Refresh Request History"):
    st.rerun()

try:
    history_response = requests.get(
        f"{API_URL}/history",
        timeout=10
    )
    history_response.raise_for_status()

    history_data = history_response.json()
    entries = history_data.get("history", [])

    if not entries:
        st.info(
            "No request history yet. Ask the AI a question to create an entry."
        )
    else:
        rows = []

        for entry in entries:
            rows.append({
                "Time": entry.get("timestamp", ""),
                "Question": entry.get("question", ""),
                "Cache": entry.get("cache", ""),
                "Model": entry.get("model", ""),
                "Estimated Cost (USD)": entry.get(
                    "estimated_cost_usd", 0.0
                )
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("View a previous answer"):
            selected_index = st.selectbox(
                "Choose a past request",
                range(len(entries)),
                format_func=lambda i: (
                    f'{entries[i].get("timestamp", "")} — '
                    f'{entries[i].get("question", "")[:80]}'
                )
            )

            selected_entry = entries[selected_index]

            st.markdown("**Question**")
            st.write(selected_entry.get("question", ""))

            st.markdown("**Answer**")
            st.markdown(selected_entry.get("answer", ""))

except requests.RequestException:
    st.error(
        "Cannot load request history. Make sure your FastAPI server is running."
    )