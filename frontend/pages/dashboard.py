import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("📈 Dashboard")
    st.write("Real-time data quality monitoring overview")

    col1, col2, col3 = st.columns(3)

    # Get datasets
    try:
        response = requests.get(f"{API_BASE_URL}/datasets", timeout=10)
        if response.status_code == 200:
            datasets_data = response.json()
            datasets = datasets_data.get("datasets", [])
        else:
            datasets = []
            st.warning("Could not fetch datasets")
    except Exception as e:
        datasets = []
        st.error(f"Error fetching datasets: {e}")

    if not datasets:
        st.info("No datasets uploaded yet. Go to Data Explorer to upload a dataset.")
        return

    # Select dataset
    dataset_names = {d["id"]: d["name"] for d in datasets}
    selected_dataset_id = st.selectbox(
        "Select Dataset",
        options=list(dataset_names.keys()),
        format_func=lambda x: dataset_names[x]
    )

    if selected_dataset_id:
        # Get dataset info
        try:
            response = requests.get(f"{API_BASE_URL}/datasets/{selected_dataset_id}", timeout=10)
            if response.status_code == 200:
                dataset_info = response.json()
            else:
                st.error("Could not fetch dataset info")
                return
        except Exception as e:
            st.error(f"Error: {e}")
            return

        # Get latest results
        try:
            response = requests.get(
                f"{API_BASE_URL}/datasets/{selected_dataset_id}/latest-result",
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                has_results = True
            else:
                has_results = False
                result = None
        except:
            has_results = False
            result = None

        # KPI Cards
        with col1:
            st.metric(
                "Rows",
                f"{dataset_info['row_count']:,}",
                help="Total records in dataset"
            )

        with col2:
            st.metric(
                "Columns",
                dataset_info['column_count'],
                help="Total features"
            )

        with col3:
            if has_results:
                quality_score = result.get("overall_quality_score", 0.0)
                st.metric(
                    "Quality Score",
                    f"{quality_score:.1%}",
                    help="Overall data quality"
                )
            else:
                st.metric("Quality Score", "N/A", help="Run analysis first")

        st.divider()

        if has_results and result:
            # Quality Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                completeness = result["completeness"]["completeness_score"]
                st.metric("Completeness", f"{completeness:.1%}")

            with col2:
                drift_score = result["drift_analysis"]["overall_drift_score"]
                st.metric("Drift Score", f"{drift_score:.2f}")

            with col3:
                anomaly_score = result["anomaly_detection"]["anomaly_score"]
                st.metric("Anomalies", f"{anomaly_score:.2f}")

            with col4:
                schema_changes = len(result["schema_validation"].get("changes", []))
                st.metric("Schema Changes", schema_changes)

            st.divider()

            # Alerts Summary
            try:
                response = requests.get(
                    f"{API_BASE_URL}/alerts/dataset/{selected_dataset_id}/summary",
                    timeout=10
                )
                if response.status_code == 200:
                    alert_summary = response.json()

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🔴 Critical", alert_summary.get("critical_count", 0))
                    with col2:
                        st.metric("🟡 Warnings", alert_summary.get("warning_count", 0))
                    with col3:
                        st.metric("🔵 Info", alert_summary.get("info_count", 0))

                    st.divider()

                    # Recent Alerts
                    if alert_summary.get("critical_count", 0) > 0:
                        st.subheader("🔴 Critical Alerts")
                        for alert in alert_summary.get("recent_critical", []):
                            st.error(f"**{alert['metric_type']}**: {alert['message']}")

            except Exception as e:
                st.warning(f"Could not fetch alerts: {e}")

            # Quality Metrics Gauge
            col1, col2 = st.columns(2)

            with col1:
                # Quality Score Gauge
                quality_score = result.get("overall_quality_score", 0.0)
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=quality_score * 100,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Quality Score"},
                    delta={"reference": 80},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 50], "color": "lightgray"},
                            {"range": [50, 80], "color": "gray"}
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 90
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Completeness Gauge
                completeness = result["completeness"]["completeness_score"]
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=completeness * 100,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Completeness"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "darkgreen"},
                        "steps": [
                            {"range": [0, 70], "color": "lightgray"},
                            {"range": [70, 90], "color": "gray"}
                        ]
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            # Analysis Details
            with st.expander("📋 Full Analysis Details"):
                st.json(result)

        else:
            st.info("No quality analysis results yet. Click the button below to run analysis.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Run Quality Analysis", use_container_width=True):
                with st.spinner("Running quality checks..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/datasets/{selected_dataset_id}/analyze",
                            timeout=30
                        )
                        if response.status_code == 200:
                            st.success("✅ Analysis complete!")
                            st.rerun()
                        else:
                            st.error(f"Analysis failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col2:
            if st.button("📊 Export Results", use_container_width=True):
                st.info("Export feature coming soon!")
