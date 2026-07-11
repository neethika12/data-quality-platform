import streamlit as st
from backend.config import settings

def render():
    st.header("⚙️ Configuration")
    st.write("Configure system thresholds and settings")

    tab1, tab2 = st.tabs(["Thresholds", "System Info"])

    with tab1:
        st.subheader("Quality Thresholds")
        st.write("Adjust alert thresholds for your use case")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribution Drift")
            drift_warning = st.slider(
                "Drift Warning Threshold",
                min_value=0.0,
                max_value=1.0,
                value=settings.DRIFT_WARNING_THRESHOLD,
                step=0.05,
                help="Drift score above this triggers WARNING"
            )

            drift_critical = st.slider(
                "Drift Critical Threshold",
                min_value=0.0,
                max_value=1.0,
                value=settings.DRIFT_CRITICAL_THRESHOLD,
                step=0.05,
                help="Drift score above this triggers CRITICAL"
            )

        with col2:
            st.subheader("Null Rates")
            null_warning = st.slider(
                "Null Rate Warning (%)",
                min_value=0,
                max_value=100,
                value=int(settings.NULL_RATE_WARNING * 100),
                step=1,
                help="Null rate above this triggers WARNING"
            )

            null_critical = st.slider(
                "Null Rate Critical (%)",
                min_value=0,
                max_value=100,
                value=int(settings.NULL_RATE_CRITICAL * 100),
                step=1,
                help="Null rate above this triggers CRITICAL"
            )

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Data Freshness")
            freshness_warning = st.number_input(
                "Freshness Warning (hours)",
                value=settings.FRESHNESS_WARNING_HOURS,
                min_value=1,
                max_value=720,
                help="Alert if data not updated for this long"
            )

            freshness_critical = st.number_input(
                "Freshness Critical (hours)",
                value=settings.FRESHNESS_CRITICAL_HOURS,
                min_value=1,
                max_value=720,
                help="Critical alert if data not updated for this long"
            )

        with col2:
            st.subheader("Record Count")
            record_drop = st.slider(
                "Record Drop Warning (%)",
                min_value=0,
                max_value=100,
                value=int(settings.RECORD_DROP_WARNING_PERCENT * 100),
                step=1,
                help="Alert if record count drops by this %"
            )

        st.divider()

        if st.button("💾 Save Configuration", use_container_width=True):
            st.info("Configuration would be saved to database (not implemented yet)")

    with tab2:
        st.subheader("System Information")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("API URL", "http://localhost:8000/api")
            st.metric("Database", settings.DB_PATH)
            st.metric("Upload Directory", settings.UPLOAD_DIR)

        with col2:
            st.metric("Debug Mode", settings.DEBUG)
            st.metric("Sample Size", f"{settings.SAMPLE_SIZE_FOR_STATS:,}")
            st.metric("API Version", settings.API_VERSION)

        st.divider()

        st.subheader("Current Thresholds")
        st.json({
            "drift": {
                "warning": settings.DRIFT_WARNING_THRESHOLD,
                "critical": settings.DRIFT_CRITICAL_THRESHOLD
            },
            "null_rate": {
                "warning": settings.NULL_RATE_WARNING,
                "critical": settings.NULL_RATE_CRITICAL
            },
            "freshness_hours": {
                "warning": settings.FRESHNESS_WARNING_HOURS,
                "critical": settings.FRESHNESS_CRITICAL_HOURS
            },
            "record_drop": {
                "warning_percent": settings.RECORD_DROP_WARNING_PERCENT
            }
        })

        st.divider()

        if st.button("🔄 Reload Configuration", use_container_width=True):
            st.success("Configuration reloaded")
