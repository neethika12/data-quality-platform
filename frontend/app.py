import streamlit as st
import requests
from datetime import datetime
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Page config
st.set_page_config(
    page_title="Data Quality Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling
st.markdown("""
<style>
    /* Sidebar styling */
    .sidebar .sidebar-content {
        padding: 20px;
    }

    /* Main content area */
    .main {
        padding: 2rem 3rem;
        background-color: #f8f9fa;
    }

    /* Cards and metrics */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }

    /* Alert styles */
    .alert-critical {
        background-color: #ff6b6b;
        color: white;
        padding: 12px;
        border-radius: 5px;
        border-left: 4px solid #d93f3f;
    }

    .alert-warning {
        background-color: #ffa94d;
        color: white;
        padding: 12px;
        border-radius: 5px;
        border-left: 4px solid #d9730d;
    }

    .alert-info {
        background-color: #4dabf7;
        color: white;
        padding: 12px;
        border-radius: 5px;
        border-left: 4px solid #1971c2;
    }

    /* Navigation buttons */
    .nav-button {
        width: 100%;
        padding: 12px;
        margin: 5px 0;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        transition: all 0.3s;
    }

    .nav-button:hover {
        transform: translateX(5px);
    }

    /* Header styling */
    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #667eea;
        padding-bottom: 10px;
    }

    h2 {
        color: #34495e;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# API configuration
API_BASE_URL = "http://localhost:8000/api"

def check_api_health():
    """Check if backend API is running."""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Main app title
st.title("📊 Data Quality & Drift Detection Platform")
st.markdown("*Real-time data quality monitoring, drift detection, and anomaly alerts*")
st.divider()

# Sidebar navigation
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=DQ+Platform", width=150)

    st.markdown("## 🗺️ Navigation")

    # API status
    if check_api_health():
        st.success("✅ Backend Connected", icon="✅")
    else:
        st.error("❌ Backend API not running. Please start the backend server.")
        st.stop()

    st.markdown("---")

    # Navigation menu
    pages = {
        "📊 Dashboard": "Dashboard",
        "📁 Data Explorer": "Data Explorer",
        "📈 Drift Analysis": "Drift Analysis",
        "✅ Quality Metrics": "Quality Metrics",
        "🔔 Alerts": "Alerts",
        "📉 Metrics Trends": "Metrics Trends",
        "🔄 Comparison": "Comparison",
        "📋 Reports": "Reports",
        "⚙️ Configure": "Configure",
    }

    for label, page_name in pages.items():
        if st.button(label, use_container_width=True,
                    key=f"btn_{page_name}",
                    type="primary" if st.session_state.current_page == page_name else "secondary"):
            st.session_state.current_page = page_name
            st.rerun()

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **Data Quality Platform v1.0**

    Detect:
    - Schema changes
    - Distribution drift
    - Data anomalies
    - Completeness issues

    [GitHub](https://github.com/neethika12/data-quality-platform)
    """)

# Route to pages based on selection
try:
    if st.session_state.current_page == "Dashboard":
        from pages import dashboard
        dashboard.render()

    elif st.session_state.current_page == "Data Explorer":
        from pages import data_explorer
        data_explorer.render()

    elif st.session_state.current_page == "Drift Analysis":
        from pages import drift_analysis
        drift_analysis.render()

    elif st.session_state.current_page == "Quality Metrics":
        from pages import quality_metrics
        quality_metrics.render()

    elif st.session_state.current_page == "Alerts":
        from pages import alerts
        alerts.render()

    elif st.session_state.current_page == "Metrics Trends":
        from pages import metrics_trends
        metrics_trends.render()

    elif st.session_state.current_page == "Comparison":
        from pages import comparison
        comparison.render()

    elif st.session_state.current_page == "Reports":
        from pages import reports
        reports.render()

    elif st.session_state.current_page == "Configure":
        from pages import configure
        configure.render()

except Exception as e:
    st.error(f"❌ Error loading page: {str(e)}")
    st.info("💡 Tip: Make sure the backend is running on http://localhost:8000")
