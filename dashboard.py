
import requests
import streamlit as st
import pandas as pd

API_URL = "https://semantic-cache-router-api.onrender.com"

st.set_page_config(
    page_title="Semantic Cache Router",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Semantic Cache Router")
st.caption(
    "AI model routing, semantic caching, response-time tracking and cost estimation"
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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Cache Status", result.get("cache", "Unknown"))
    col2.metric("Selected Model", result.get("model", "Unknown"))
    col3.metric(
        "Request Cost (USD)",
        f'${result.get("estimated_cost_usd", 0):.8f}'
    )
    col4.metric(
        "Response Time",
        f'{result.get("response_time_ms", 0):,.2f} ms'
    )

    st.markdown("### Answer")
    st.markdown(result.get("answer", "No answer returned."))

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
        f'${stats.get("total_estimated_cost_usd", 0):.6f}'
    )
    col2.metric("Total Requests", stats.get("total_requests", 0))
    col3.metric(
        "Cache Hit Rate",
        f'{stats.get("cache_hit_rate_percent", 0):.2f}%'
    )

    col4, col5 = st.columns(2)

    col4.metric("Cache Hits", stats.get("cache_hits", 0))
    col5.metric("Cache Misses", stats.get("cache_misses", 0))

    st.markdown("### Cache Performance")

    chart_data = pd.DataFrame({
        "Request Type": ["Cache Hits", "Cache Misses"],
        "Requests": [
            stats.get("cache_hits", 0),
            stats.get("cache_misses", 0)
        ]
    })

    st.bar_chart(
        chart_data,
        x="Request Type",
        y="Requests"
    )

    cache_hits = stats.get("cache_hits", 0)
    cache_misses = stats.get("cache_misses", 0)
    total_cost = stats.get("total_estimated_cost_usd", 0)

    if cache_misses > 0:
        average_miss_cost = total_cost / cache_misses
        estimated_savings = average_miss_cost * cache_hits

        st.metric(
            "Approximate Cost Savings from Cache",
            f"${estimated_savings:.6f}"
        )
        st.caption(
            "Rough estimate: average recorded cost per cache miss multiplied "
            "by cache hits. Actual savings may differ because cached questions "
            "and uncached questions may have different costs."
        )
    else:
        st.info(
            "Run at least one cache-miss request to estimate potential savings."
        )

except requests.RequestException:
    st.error(
        "Cannot load statistics. Make sure your FastAPI server is running."
    )

st.divider()

st.subheader("Response-Time Comparison")

st.caption(
    "Compare average response times for cache hits and cache misses "
    "using recent requests with recorded timing data."
)

try:
    timing_response = requests.get(
        f"{API_URL}/history",
        timeout=10
    )
    timing_response.raise_for_status()

    timing_entries = timing_response.json().get("history", [])

    timed_rows = [
        {
            "Cache": entry.get("cache", ""),
            "Response Time (ms)": entry.get("response_time_ms")
        }
        for entry in timing_entries
        if entry.get("response_time_ms") is not None
    ]

    if timed_rows:
        timing_df = pd.DataFrame(timed_rows)
        timing_df["Response Time (ms)"] = pd.to_numeric(
            timing_df["Response Time (ms)"],
            errors="coerce"
        )
        timing_df = timing_df.dropna(
            subset=["Response Time (ms)"]
        )

        averages = (
            timing_df.groupby("Cache")["Response Time (ms)"]
            .mean()
            .reset_index()
        )

        st.markdown("### Average Response Time")

        st.dataframe(
            averages.round(2),
            use_container_width=True,
            hide_index=True
        )

        st.bar_chart(
            averages,
            x="Cache",
            y="Response Time (ms)"
        )

        average_times = averages.set_index("Cache")[
            "Response Time (ms)"
        ].to_dict()

        miss_time = average_times.get("MISS")
        hit_time = average_times.get("HIT")

        if miss_time is not None and hit_time is not None:
            if miss_time > 0:
                improvement = (
                    (miss_time - hit_time) / miss_time
                ) * 100

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Average Cache Miss",
                    f"{miss_time:,.2f} ms"
                )

                col2.metric(
                    "Average Cache Hit",
                    f"{hit_time:,.2f} ms"
                )

                col3.metric(
                    "Speed Improvement",
                    f"{improvement:.2f}%",
                    help=(
                        "Calculated from average miss and hit response "
                        "times in the recent recorded history. A negative "
                        "value means cache hits were slower in this sample."
                    )
                )
            else:
                st.info(
                    "Cannot calculate the percentage because the average "
                    "cache-miss response time is zero."
                )
        else:
            st.info(
                "Run at least one cache-hit request and one cache-miss "
                "request with response-time data to calculate the "
                "speed improvement."
            )
    else:
        st.info(
            "No response-time data found yet. Ask a few questions first."
        )

except requests.RequestException:
    st.error(
        "Cannot load response-time data. Make sure your FastAPI server is running."
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

    entries = history_response.json().get("history", [])

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
                "Response Time (ms)": entry.get("response_time_ms"),
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
