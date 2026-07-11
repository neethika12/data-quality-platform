import dash
from dash import dcc, html, callback, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import requests
import pandas as pd
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# API configuration
API_BASE_URL = "http://localhost:8000/api"

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Data Quality Platform"

# Define color scheme
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#52c41a",
    "danger": "#ff6b6b",
    "warning": "#ffa94d",
    "info": "#4dabf7",
    "bg_light": "#f8f9fa",
    "bg_dark": "#2c3e50",
    "text_dark": "#2c3e50",
    "text_light": "#7f8c8d",
}

# Professional stylesheet
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        "rel": "stylesheet",
    }
]

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {
                font-family: 'Inter', sans-serif;
            }

            body {
                background-color: ''' + COLORS["bg_light"] + ''';
                margin: 0;
                padding: 0;
            }

            .navbar {
                background: linear-gradient(135deg, ''' + COLORS["primary"] + ''' 0%, ''' + COLORS["secondary"] + ''' 100%);
                color: white;
                padding: 20px 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .navbar-title {
                font-size: 24px;
                font-weight: 700;
            }

            .navbar-status {
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
            }

            .sidebar {
                width: 250px;
                background: white;
                border-right: 1px solid #e0e0e0;
                padding: 20px;
                height: 100vh;
                position: fixed;
                overflow-y: auto;
                box-shadow: 2px 0 8px rgba(0,0,0,0.05);
            }

            .nav-item {
                padding: 12px 16px;
                margin: 8px 0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 14px;
                font-weight: 500;
                color: ''' + COLORS["text_dark"] + ''';
            }

            .nav-item:hover {
                background-color: ''' + COLORS["bg_light"] + ''';
                transform: translateX(4px);
            }

            .nav-item.active {
                background: linear-gradient(135deg, ''' + COLORS["primary"] + ''' 0%, ''' + COLORS["secondary"] + ''' 100%);
                color: white;
            }

            .main-content {
                margin-left: 250px;
                padding: 30px;
            }

            .page-title {
                font-size: 28px;
                font-weight: 700;
                color: ''' + COLORS["text_dark"] + ''';
                margin-bottom: 8px;
            }

            .page-subtitle {
                font-size: 14px;
                color: ''' + COLORS["text_light"] + ''';
                margin-bottom: 24px;
            }

            .card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }

            .metric-card {
                background: linear-gradient(135deg, ''' + COLORS["primary"] + ''' 0%, ''' + COLORS["secondary"] + ''' 100%);
                color: white;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
            }

            .metric-value {
                font-size: 32px;
                font-weight: 700;
                margin: 10px 0;
            }

            .metric-label {
                font-size: 12px;
                opacity: 0.9;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .alert-critical {
                background-color: #fff5f5;
                border-left: 4px solid ''' + COLORS["danger"] + ''';
                padding: 12px;
                border-radius: 4px;
                margin: 8px 0;
            }

            .alert-warning {
                background-color: #fffbf0;
                border-left: 4px solid ''' + COLORS["warning"] + ''';
                padding: 12px;
                border-radius: 4px;
                margin: 8px 0;
            }

            .alert-info {
                background-color: #f0f7ff;
                border-left: 4px solid ''' + COLORS["info"] + ''';
                padding: 12px;
                border-radius: 4px;
                margin: 8px 0;
            }

            button {
                background: linear-gradient(135deg, ''' + COLORS["primary"] + ''' 0%, ''' + COLORS["secondary"] + ''' 100%);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }

            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# App layout
app.layout = html.Div([
    # Store for page state
    dcc.Store(id='page-store', data='dashboard'),

    # Navbar
    html.Div([
        html.Div([
            html.Span("📊 Data Quality Platform", className="navbar-title"),
        ]),
        html.Div(id='navbar-status', className='navbar-status'),
    ], className='navbar'),

    # Container
    html.Div([
        # Sidebar
        html.Div([
            html.Div([
                html.Div("NAVIGATION", style={'fontSize': '12px', 'fontWeight': '600', 'color': COLORS['text_light'], 'marginBottom': '12px', 'textTransform': 'uppercase'}),

                html.Div(id='nav-buttons'),

                html.Hr(style={'margin': '20px 0', 'border': 'none', 'borderTop': '1px solid #e0e0e0'}),

                html.Div([
                    html.Div("ABOUT", style={'fontSize': '12px', 'fontWeight': '600', 'color': COLORS['text_light'], 'marginBottom': '12px', 'textTransform': 'uppercase'}),
                    html.P([
                        "Data Quality Platform v1.0",
                        html.Br(),
                        html.Br(),
                        "Detect schema changes, distribution drift, anomalies & completeness issues.",
                        html.Br(),
                        html.Br(),
                        html.A("View on GitHub", href="https://github.com/neethika12/data-quality-platform", target="_blank", style={'color': COLORS['primary'], 'textDecoration': 'none', 'fontWeight': '600'})
                    ], style={'fontSize': '13px', 'color': COLORS['text_light'], 'lineHeight': '1.6'}),
                ]),
            ], style={'padding': '20px'}),
        ], className='sidebar'),

        # Main content
        html.Div(id='page-content', className='main-content'),

    ], style={'display': 'flex'}),
], style={'height': '100vh', 'display': 'flex', 'flexDirection': 'column'})

# Navigation click callback
@callback(
    Output('page-store', 'data'),
    Input({'type': 'nav-btn', 'index': dash.ALL}, 'n_clicks'),
    State({'type': 'nav-btn', 'index': dash.ALL}, 'id'),
    prevent_initial_call=True
)
def nav_click(clicks, ids):
    if not ids:
        return 'dashboard'
    ctx = dash.callback_context
    if not ctx.triggered:
        return 'dashboard'
    return ctx.triggered[0]['prop_id'].split('"index":"')[1].split('"}')[0]

# Navigation buttons callback
@callback(
    Output('nav-buttons', 'children'),
    Input('page-store', 'data'),
)
def update_nav(current_page):
    pages = [
        ('📊 Dashboard', 'dashboard'),
        ('📁 Data Explorer', 'data_explorer'),
        ('📈 Drift Analysis', 'drift_analysis'),
        ('✅ Quality Metrics', 'quality_metrics'),
        ('🔔 Alerts', 'alerts'),
        ('📉 Metrics Trends', 'metrics_trends'),
        ('🔄 Comparison', 'comparison'),
        ('📋 Reports', 'reports'),
        ('⚙️ Configure', 'configure'),
    ]

    nav_items = []
    for label, page in pages:
        is_active = page == current_page
        nav_items.append(
            html.Button(
                label,
                id={'type': 'nav-btn', 'index': page},
                n_clicks=0,
                className='nav-item active' if is_active else 'nav-item',
                style={
                    'width': '100%',
                    'textAlign': 'left',
                    'background': (f'linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%)'
                                  if is_active else 'transparent'),
                    'color': 'white' if is_active else COLORS['text_dark'],
                }
            )
        )

    return nav_items

# API status callback
@callback(
    Output('navbar-status', 'children'),
    Input('page-store', 'data'),
)
def update_api_status(_):
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health", timeout=2)
        if response.status_code == 200:
            return "✅ Backend Connected"
    except:
        return "❌ Backend Offline"
    return "❌ Backend Offline"

# Page routing
@callback(
    Output('page-content', 'children'),
    Input('page-store', 'data'),
)
def display_page(page):
    if page == 'dashboard':
        from pages_dash import dashboard
        return dashboard.render()
    elif page == 'data_explorer':
        from pages_dash import data_explorer
        return data_explorer.render()
    elif page == 'drift_analysis':
        from pages_dash import drift_analysis
        return drift_analysis.render()
    elif page == 'quality_metrics':
        from pages_dash import quality_metrics
        return quality_metrics.render()
    elif page == 'alerts':
        from pages_dash import alerts
        return alerts.render()
    elif page == 'metrics_trends':
        from pages_dash import metrics_trends
        return metrics_trends.render()
    elif page == 'comparison':
        from pages_dash import comparison
        return comparison.render()
    elif page == 'reports':
        from pages_dash import reports
        return reports.render()
    elif page == 'configure':
        from pages_dash import configure
        return configure.render()
    else:
        return html.Div("Page not found")

if __name__ == '__main__':
    app.run_server(debug=True, port=8050, host='0.0.0.0')
