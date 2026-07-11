import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("📊 Drift Analysis")
    st.write("Detect and analyze distribution drift in your data")

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
        st.info("No datasets available. Upload one first.")
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
                drift_analysis = result.get("drift_analysis", {})

                # Overall Drift
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Overall Drift Score",
                        f"{drift_analysis.get('overall_drift_score', 0):.2f}"
                    )

                with col2:
                    st.metric(
                        "Severity Level",
                        drift_analysis.get("severity_level", "INFO")
                    )

                with col3:
                    drifted = drift_analysis.get("drifted_count", 0)
                    total = drift_analysis.get("feature_count", 0)
                    st.metric(
                        "Features Drifted",
                        f"{drifted}/{total}"
                    )

                st.divider()

                # Feature Drift Details
                drifted_features = drift_analysis.get("drifted_features", [])

                if drifted_features:
                    st.subheader("Feature Drift Details")

                    # Create dataframe
                    df_drift = pd.DataFrame([
                        {
                            "Feature": f["feature"],
                            "Drift Score": f['drift_score'],
                            "P-Value": f"{f['p_value']:.4f}",
                            "Test": f["test_method"],
                            "Interpretation": f["interpretation"]
                        }
                        for f in drifted_features
                    ])

                    st.dataframe(df_drift, use_container_width=True)

                    # Drift Score Chart
                    fig = px.bar(
                        df_drift,
                        x="Feature",
                        y="Drift Score",
                        color="Drift Score",
                        color_continuous_scale="Reds",
                        title="Feature Drift Scores"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.success("✅ No significant drift detected!")

                # Statistical Test Results
                with st.expander("📈 Statistical Test Details"):
                    for feature in drifted_features:
                        st.write(f"**{feature['feature']}**")
                        st.write(f"- Test: {feature['test_method']}")
                        st.write(f"- P-Value: {feature['p_value']:.6f}")
                        st.write(f"- Drift Score: {feature['drift_score']:.3f}")
                        st.write(f"- Interpretation: {feature['interpretation']}")
                        st.divider()

            else:
                st.info("Run quality analysis first to see drift analysis")

        except Exception as e:
            st.error(f"Error: {e}")
