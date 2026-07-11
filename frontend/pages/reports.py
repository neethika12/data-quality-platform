import streamlit as st
import requests
import json

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("📋 Reports")
    st.write("Generate and export quality analysis reports")

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

    col1, col2 = st.columns(2)

    with col1:
        report_type = st.radio(
            "Report Format",
            options=["View Online", "Download JSON", "Download Text"],
            label_visibility="collapsed"
        )

    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            with st.spinner("Generating report..."):
                try:
                    # Get report
                    format_param = "json" if report_type == "View Online" else report_type.split()[-1].lower()

                    response = requests.get(
                        f"{API_BASE_URL}/datasets/{selected_id}/report",
                        params={"format": format_param},
                        timeout=10
                    )

                    if response.status_code == 200:
                        report_data = response.json()

                        if report_type == "View Online":
                            st.success("✅ Report Generated")

                            # Display report sections
                            st.subheader("Quality Score")
                            score = report_data.get("overall_quality_score", 0)
                            st.metric("Overall", f"{score:.1%}")

                            st.divider()

                            st.subheader("Completeness")
                            comp = report_data.get("completeness", {})
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Score", f"{comp.get('completeness_score', 0):.1%}")
                            with col2:
                                st.metric("Records", f"{comp.get('record_count', {}).get('current_count', 0):,}")

                            st.divider()

                            st.subheader("Schema Validation")
                            schema = report_data.get("schema_validation", {})
                            changes = schema.get("changes", [])
                            st.metric("Changes", len(changes))
                            if changes:
                                for change in changes[:5]:
                                    st.write(f"- {change['type']}: {change['column']}")

                            st.divider()

                            st.subheader("Drift Analysis")
                            drift = report_data.get("drift_analysis", {})
                            st.metric("Drift Score", f"{drift.get('overall_drift_score', 0):.2f}")
                            drifted = drift.get("drifted_features", [])
                            if drifted:
                                for feature in drifted[:3]:
                                    st.write(f"- {feature['feature']}: {feature['drift_score']:.3f}")

                            st.divider()

                            st.subheader("Recommendations")
                            for rec in report_data.get("recommendations", []):
                                st.write(f"• {rec}")

                            # Export buttons
                            st.divider()

                            col1, col2 = st.columns(2)

                            with col1:
                                if st.button("⬇️ Export as JSON", use_container_width=True):
                                    json_str = json.dumps(report_data, indent=2)
                                    st.download_button(
                                        label="📥 Download JSON",
                                        data=json_str,
                                        file_name=f"report_{selected_id}.json",
                                        mime="application/json"
                                    )

                            with col2:
                                if st.button("⬇️ Export as Text", use_container_width=True):
                                    # Get text report
                                    text_response = requests.get(
                                        f"{API_BASE_URL}/datasets/{selected_id}/report",
                                        params={"format": "text"},
                                        timeout=10
                                    )
                                    if text_response.status_code == 200:
                                        text_data = text_response.json()
                                        st.download_button(
                                            label="📥 Download Text",
                                            data=text_data.get("content", ""),
                                            file_name=f"report_{selected_id}.txt",
                                            mime="text/plain"
                                        )

                        else:
                            # Download directly
                            if report_type == "Download JSON":
                                json_str = json.dumps(report_data, indent=2)
                                st.download_button(
                                    label="📥 Download JSON",
                                    data=json_str,
                                    file_name=f"report_{selected_id}.json",
                                    mime="application/json"
                                )
                            else:
                                # Text report
                                text_content = report_data.get("content", "")
                                st.download_button(
                                    label="📥 Download Text",
                                    data=text_content,
                                    file_name=f"report_{selected_id}.txt",
                                    mime="text/plain"
                                )

                    else:
                        st.error(f"Error: {response.text}")

                except Exception as e:
                    st.error(f"Error generating report: {e}")

    st.divider()

    st.subheader("Report Templates")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**📄 Executive Summary**")
        st.write("High-level overview for stakeholders")

    with col2:
        st.write("**🔧 Technical Report**")
        st.write("Detailed analysis for data engineers")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**📊 Metrics Report**")
        st.write("Time-series trends and KPIs")

    with col2:
        st.write("**⚠️ Issues Report**")
        st.write("Critical findings and recommendations")
