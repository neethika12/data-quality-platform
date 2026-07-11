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

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-critical {
        background-color: #ff6b6b;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-warning {
        background-color: #ffa94d;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-info {
        background-color: #4dabf7;
        color: white;
        padding: 10px;
        border-radius: 5px;
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

# Main app
st.title("📊 Data Quality & Drift Detection Platform")

# Sidebar
with st.sidebar:
    st.header("Navigation")

    if not check_api_health():
        st.error("❌ Backend API not running. Please start the backend server.")
        st.stop()
    else:
        st.success("✅ Backend connected")

    menu_selection = st.radio(
        "Select Page",
        options=["Dashboard", "Data Explorer", "Drift Analysis", "Quality Metrics", "Alerts", "Metrics Trends", "Comparison", "Reports", "Configure"],
        label_visibility="collapsed"
    )

# Route to pages based on selection
if menu_selection == "Dashboard":
    from pages import dashboard
    dashboard.render()

elif menu_selection == "Data Explorer":
    from pages import data_explorer
    data_explorer.render()

elif menu_selection == "Drift Analysis":
    from pages import drift_analysis
    drift_analysis.render()

elif menu_selection == "Quality Metrics":
    from pages import quality_metrics
    quality_metrics.render()

elif menu_selection == "Alerts":
    from pages import alerts
    alerts.render()

elif menu_selection == "Metrics Trends":
    from pages import metrics_trends
    metrics_trends.render()

elif menu_selection == "Comparison":
    from pages import comparison
    comparison.render()

elif menu_selection == "Reports":
    from pages import reports
    reports.render()

elif menu_selection == "Configure":
    from pages import configure
    configure.render()
