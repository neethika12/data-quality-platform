import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("✅ Quality Metrics Dashboard")
    st.write("Detailed data quality and completeness analysis")

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

    if selected_id:
        try:
            response = requests.get(
                f"{API_BASE_URL}/datasets/{selected_id}/latest-result",
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()

                # Tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "Completeness", "Null Analysis", "Anomalies", "Schema"
                ])

                with tab1:
                    st.subheader("Data Completeness")
                    completeness = result.get("completeness", {})

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        score = completeness.get("completeness_score", 0)
                        st.metric("Overall Completeness", f"{score:.1%}")

                    with col2:
                        records = completeness.get("record_count", {})
                        st.metric("Record Count", f"{records.get('current_count', 0):,}")

                    with col3:
                        freshness = completeness.get("freshness", {})
                        hours = freshness.get("hours_since_update", 0)
                        st.metric("Hours Since Update", f"{hours:.1f}h")

                    st.divider()

                    # Freshness Status
                    freshness = completeness.get("freshness", {})
                    if freshness.get("status") == "CRITICAL":
                        st.error(f"⚠️ Data is stale: {freshness['hours_since_update']:.1f} hours")
                    elif freshness.get("status") == "WARNING":
                        st.warning(f"⚠️ Data is aging: {freshness['hours_since_update']:.1f} hours")
                    else:
                        st.success("✅ Data is fresh")

                with tab2:
                    st.subheader("Null Value Analysis")
                    null_analysis = result.get("anomaly_detection", {}).get("null_analysis", {})

                    if null_analysis:
                        # Create dataframe
                        null_data = [
                            {
                                "Column": col,
                                "Null Count": info["null_count"],
                                "Null Rate": f"{info['null_rate']:.2%}",
                                "Status": info["status"]
                            }
                            for col, info in null_analysis.items()
                        ]
                        df_null = pd.DataFrame(null_data)
                        st.dataframe(df_null, use_container_width=True)

                        # Null Rate Visualization
                        null_rates = [
                            {"Column": col, "Null Rate": info["null_rate"] * 100}
                            for col, info in null_analysis.items()
                        ]
                        df_viz = pd.DataFrame(null_rates)

                        if not df_viz.empty:
                            fig = go.Figure(
                                data=[go.Bar(x=df_viz["Column"], y=df_viz["Null Rate"])]
                            )
                            fig.update_layout(
                                title="Null Rate by Column",
                                xaxis_title="Column",
                                yaxis_title="Null Rate (%)"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                with tab3:
                    st.subheader("Anomalies")
                    anomalies = result.get("anomaly_detection", {})

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Total Anomalies",
                            anomalies.get("total_anomalies", 0)
                        )

                    with col2:
                        st.metric(
                            "Anomaly Score",
                            f"{anomalies.get('anomaly_score', 0):.3f}"
                        )

                    with col3:
                        outlier_count = len(anomalies.get("outliers", {}))
                        st.metric("Columns with Outliers", outlier_count)

                    st.divider()

                    # Outlier Details
                    if anomalies.get("outliers"):
                        st.subheader("Outlier Detection")
                        outliers = anomalies.get("outliers", {})

                        for col, info in outliers.items():
                            st.write(f"**{col}** ({info['method']})")
                            st.write(f"- Count: {info['outlier_count']}")
                            st.write(f"- Percentage: {info['percentage']:.2f}%")

                with tab4:
                    st.subheader("Schema Validation")
                    schema = result.get("schema_validation", {})

                    if schema.get("is_breaking"):
                        st.error("🔴 Breaking schema changes detected!")
                    else:
                        st.success("✅ No breaking changes")

                    if schema.get("changes"):
                        st.subheader("Schema Changes")
                        changes = schema.get("changes", [])
                        for change in changes:
                            st.write(f"**{change['type']}**: {change['column']}")
                            st.write(f"- Severity: {change['severity']}")
                            if change.get("old"):
                                st.write(f"- Old: {change['old']} → New: {change['new']}")
                    else:
                        st.info("No schema changes detected")

            else:
                st.info("Run analysis first")

        except Exception as e:
            st.error(f"Error: {e}")
