import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("🔄 Before & After Comparison")
    st.write("Compare quality metrics across two analyses")

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

    st.divider()

    # Get latest result
    try:
        response = requests.get(
            f"{API_BASE_URL}/datasets/{selected_id}/latest-result",
            timeout=10
        )

        if response.status_code == 200:
            current = response.json()

            # Try to get previous result from metric history
            history_response = requests.get(
                f"{API_BASE_URL}/datasets/{selected_id}/metric-history",
                params={"metric_type": "quality_score", "limit": 2},
                timeout=10
            )

            history_data = history_response.json() if history_response.status_code == 200 else {"metrics": []}
            metrics = history_data.get("metrics", [])

            if len(metrics) < 2:
                st.info("Need at least 2 analyses to compare. Run analysis again after making changes to your data.")
                return

            # Create comparison
            st.subheader("Quality Score Comparison")

            col1, col2, col3 = st.columns(3)

            with col1:
                current_score = current.get("overall_quality_score", 0)
                st.metric("Current Score", f"{current_score:.1%}")

            with col2:
                previous_score = metrics[0].get("value", 0)
                st.metric("Previous Score", f"{previous_score:.1%}")

            with col3:
                change = current_score - previous_score
                change_pct = (change / previous_score * 100) if previous_score != 0 else 0
                st.metric(
                    "Change",
                    f"{change:.1%}",
                    delta=f"{change_pct:+.1f}%"
                )

            st.divider()

            # Component comparison
            st.subheader("Component Metrics")

            comparison_data = {
                "Metric": ["Completeness", "Drift Score", "Anomaly Score"],
                "Current": [
                    current.get("completeness", {}).get("completeness_score", 0),
                    current.get("drift_analysis", {}).get("overall_drift_score", 0),
                    current.get("anomaly_detection", {}).get("anomaly_score", 0),
                ],
                "Previous": [0, 0, 0]  # Would need to fetch actual previous values
            }

            df_comparison = pd.DataFrame(comparison_data)

            # Create comparison chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                name='Current',
                x=df_comparison["Metric"],
                y=df_comparison["Current"],
                marker=dict(color='#2980b9')
            ))

            fig.add_trace(go.Bar(
                name='Previous',
                x=df_comparison["Metric"],
                y=df_comparison["Previous"],
                marker=dict(color='#95a5a6')
            ))

            fig.update_layout(
                title="Metric Comparison",
                barmode='group',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Schema changes
            st.subheader("Schema Changes")
            schema = current.get("schema_validation", {})
            changes = schema.get("changes", [])

            if changes:
                for change in changes:
                    status_icon = "🔴" if change["severity"] == "CRITICAL" else "🟡" if change["severity"] == "WARNING" else "🔵"
                    st.write(f"{status_icon} **{change['type']}**: {change['column']}")
                    if change.get("old") and change.get("new"):
                        st.write(f"   {change['old']} → {change['new']}")
            else:
                st.success("✅ No schema changes")

            # Drift changes
            st.subheader("Drift Analysis")
            drift = current.get("drift_analysis", {})
            drifted_features = drift.get("drifted_features", [])

            if drifted_features:
                df_drift = pd.DataFrame([
                    {
                        "Feature": f["feature"],
                        "Drift Score": f"{f['drift_score']:.3f}",
                        "P-Value": f"{f['p_value']:.6f}",
                        "Status": "📊 Drifted"
                    }
                    for f in drifted_features
                ])
                st.dataframe(df_drift, use_container_width=True)
            else:
                st.success("✅ No significant drift detected")

            # Anomaly changes
            st.subheader("Anomaly Changes")
            anomalies = current.get("anomaly_detection", {})
            total_anomalies = anomalies.get("total_anomalies", 0)

            st.write(f"**Total Anomalies**: {total_anomalies}")

            null_analysis = anomalies.get("null_analysis", {})
            high_null_cols = [c for c, info in null_analysis.items() if info.get("status") in ["WARNING", "CRITICAL"]]

            if high_null_cols:
                st.write(f"**Columns with High Null Rates**: {', '.join(high_null_cols[:5])}")
            else:
                st.write("✅ No high null rate issues")

            # Recommendations
            st.subheader("Recommendations")
            recommendations = [
                "Check data pipeline for failures" if schema.get("is_breaking") else None,
                "Investigate distribution changes" if drift.get("severity_level") == "CRITICAL" else None,
                "Review data quality thresholds" if total_anomalies > 100 else None,
                "Monitor completeness improvements" if current.get("completeness", {}).get("completeness_score", 0) > 0.95 else None,
            ]

            for rec in [r for r in recommendations if r]:
                st.write(f"• {rec}")

            if not any(recommendations):
                st.success("✅ No critical recommendations")

        else:
            st.error("Could not fetch analysis results")

    except Exception as e:
        st.error(f"Error: {e}")
