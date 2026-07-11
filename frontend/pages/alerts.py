import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE_URL = "http://localhost:8000/api"

def render():
    st.header("🔔 Alert Management")
    st.write("View and manage quality alerts")

    # Get datasets
    try:
        response = requests.get(f"{API_BASE_URL}/datasets", timeout=10)
        if response.status_code == 200:
            datasets = response.json().get("datasets", [])
        else:
            datasets = []
    except:
        datasets = []

    col1, col2, col3 = st.columns(3)

    with col1:
        filter_dataset = st.selectbox(
            "Filter by Dataset",
            options=["All"] + [d["name"] for d in datasets],
            key="dataset_filter"
        )

    with col2:
        filter_severity = st.selectbox(
            "Filter by Severity",
            options=["All", "CRITICAL", "WARNING", "INFO"],
            key="severity_filter"
        )

    with col3:
        limit = st.number_input("Limit", value=50, min_value=10, max_value=200)

    st.divider()

    try:
        # Get all alerts
        params = {"limit": limit}
        if filter_severity != "All":
            params["severity"] = filter_severity

        response = requests.get(f"{API_BASE_URL}/alerts", params=params, timeout=10)

        if response.status_code == 200:
            alerts_data = response.json()
            alerts = alerts_data.get("alerts", [])

            # Filter by dataset if needed
            if filter_dataset != "All":
                selected_dataset = next(
                    (d for d in datasets if d["name"] == filter_dataset),
                    None
                )
                if selected_dataset:
                    alerts = [a for a in alerts if a["dataset_id"] == selected_dataset["id"]]

            if not alerts:
                st.info("No alerts found")
            else:
                # Summary
                critical = len([a for a in alerts if a["severity"] == "CRITICAL"])
                warning = len([a for a in alerts if a["severity"] == "WARNING"])
                info = len([a for a in alerts if a["severity"] == "INFO"])

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", len(alerts))
                with col2:
                    st.metric("🔴 Critical", critical)
                with col3:
                    st.metric("🟡 Warning", warning)
                with col4:
                    st.metric("🔵 Info", info)

                st.divider()

                # Alert Table
                st.subheader("Alert Log")

                # Create display dataframe
                alert_display = []
                for alert in alerts:
                    severity_icon = {
                        "CRITICAL": "🔴",
                        "WARNING": "🟡",
                        "INFO": "🔵"
                    }.get(alert.get("severity", "INFO"), "❓")

                    alert_display.append({
                        "Severity": f"{severity_icon} {alert['severity']}",
                        "Metric": alert["metric_type"],
                        "Message": alert["message"],
                        "Value": f"{alert['value']:.2f}",
                        "Status": alert["status"],
                        "Created": alert["created_at"][:10]
                    })

                df_alerts = pd.DataFrame(alert_display)
                st.dataframe(df_alerts, use_container_width=True)

                # Alert Details
                st.divider()
                st.subheader("Alert Details")

                for i, alert in enumerate(alerts[:10]):
                    with st.expander(f"{alert['metric_type']} - {alert['message'][:50]}..."):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Metric Type**: {alert['metric_type']}")
                            st.write(f"**Severity**: {alert['severity']}")
                            st.write(f"**Status**: {alert['status']}")

                        with col2:
                            st.write(f"**Value**: {alert['value']}")
                            st.write(f"**Threshold**: {alert['threshold']}")
                            st.write(f"**Created**: {alert['created_at']}")

                        if alert["status"] == "ACTIVE":
                            if st.button(
                                "Acknowledge Alert",
                                key=f"ack_btn_{alert['id']}"
                            ):
                                response = requests.post(
                                    f"{API_BASE_URL}/alerts/{alert['id']}/acknowledge",
                                    timeout=10
                                )
                                if response.status_code == 200:
                                    st.success("✅ Alert acknowledged")
                                    st.rerun()

        else:
            st.error("Could not fetch alerts")

    except Exception as e:
        st.error(f"Error: {e}")
