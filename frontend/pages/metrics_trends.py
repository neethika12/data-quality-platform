import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("📈 Metrics Trends")
    st.write("Track quality metrics over time")

    # Get datasets
    try:
        response = requests.get(f"{API_BASE_URL}/datasets", timeout=10)
        if response.status_code == 200:
            datasets = response.json().get("datasets", [])
        else:
            datasets = []
    except:
        datasets = []

    if not datasets:
        st.info("No datasets available.")
        return

    dataset_names = {d["id"]: d["name"] for d in datasets}
    selected_id = st.selectbox(
        "Select Dataset",
        options=list(dataset_names.keys()),
        format_func=lambda x: dataset_names[x]
    )

    if not selected_id:
        return

    col1, col2 = st.columns(2)

    with col1:
        metric_type = st.selectbox(
            "Metric to Track",
            options=["quality_score", "drift_score", "completeness", "anomaly_score"],
            format_func=lambda x: x.replace("_", " ").title()
        )

    with col2:
        limit = st.slider("Last N analyses", 5, 50, 20)

    st.divider()

    # Fetch metric history
    try:
        response = requests.get(
            f"{API_BASE_URL}/datasets/{selected_id}/metric-history",
            params={"metric_type": metric_type, "limit": limit},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            metrics = data.get("metrics", [])

            if not metrics:
                st.info(f"No historical data for {metric_type}")
                return

            # Also get latest result for current values
            result_response = requests.get(
                f"{API_BASE_URL}/datasets/{selected_id}/latest-result",
                timeout=10
            )

            if result_response.status_code == 200:
                latest_result = result_response.json()

                # Create dataframe from metrics
                df_history = pd.DataFrame([
                    {
                        "Date": pd.to_datetime(m.get("created_at", "")),
                        metric_type: m.get("value", 0)
                    }
                    for m in metrics
                ])

                if not df_history.empty:
                    df_history = df_history.sort_values("Date")

                    # Trend chart
                    fig = go.Figure()

                    fig.add_trace(go.Scatter(
                        x=df_history["Date"],
                        y=df_history[metric_type],
                        mode='lines+markers',
                        name=metric_type.replace("_", " ").title(),
                        line=dict(color='#2980b9', width=2),
                        marker=dict(size=8)
                    ))

                    # Add trend line
                    if len(df_history) > 1:
                        z = np.polyfit(range(len(df_history)), df_history[metric_type], 1)
                        p = np.poly1d(z)
                        trend_line = p(range(len(df_history)))

                        fig.add_trace(go.Scatter(
                            x=df_history["Date"],
                            y=trend_line,
                            mode='lines',
                            name='Trend',
                            line=dict(color='#e74c3c', width=2, dash='dash')
                        ))

                    fig.update_layout(
                        title=f"{metric_type.replace('_', ' ').title()} Over Time",
                        xaxis_title="Date",
                        yaxis_title=metric_type.replace("_", " ").title(),
                        hovermode="x unified",
                        height=400
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Statistics
                    st.subheader("Statistics")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            "Current",
                            f"{df_history[metric_type].iloc[-1]:.3f}"
                        )

                    with col2:
                        st.metric(
                            "Average",
                            f"{df_history[metric_type].mean():.3f}"
                        )

                    with col3:
                        min_val = df_history[metric_type].min()
                        st.metric(
                            "Minimum",
                            f"{min_val:.3f}"
                        )

                    with col4:
                        max_val = df_history[metric_type].max()
                        st.metric(
                            "Maximum",
                            f"{max_val:.3f}"
                        )

                    # Trend direction
                    st.divider()

                    if len(df_history) > 1:
                        current = df_history[metric_type].iloc[-1]
                        previous = df_history[metric_type].iloc[-2]
                        change = current - previous
                        percent_change = (change / previous * 100) if previous != 0 else 0

                        if change > 0:
                            st.warning(f"📈 Increasing by {abs(percent_change):.1f}%")
                        elif change < 0:
                            st.success(f"📉 Decreasing by {abs(percent_change):.1f}%")
                        else:
                            st.info("➡️ No change")

                    # Data table
                    with st.expander("View Historical Data"):
                        display_df = df_history.copy()
                        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d %H:%M")
                        st.dataframe(display_df, use_container_width=True)

        else:
            st.error("Could not fetch metric history")

    except Exception as e:
        st.error(f"Error: {e}")


import numpy as np
