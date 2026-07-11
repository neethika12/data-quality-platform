from dash import html, dcc
import plotly.graph_objects as go
import requests
import json

API_BASE_URL = "http://localhost:8000/api"

COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#52c41a",
    "danger": "#ff6b6b",
    "warning": "#ffa94d",
    "info": "#4dabf7",
}

def render():
    try:
        # Fetch datasets
        response = requests.get(f"{API_BASE_URL}/datasets", timeout=10)
        datasets = response.json().get("datasets", []) if response.status_code == 200 else []

        if not datasets:
            return html.Div([
                html.H1("📊 Dashboard", className='page-title'),
                html.P("Real-time data quality monitoring overview", className='page-subtitle'),
                html.Div("📤 No datasets uploaded yet. Go to Data Explorer to upload a dataset.", className='card', style={'padding': '20px', 'textAlign': 'center', 'color': '#7f8c8d'})
            ])

        # Get first dataset
        dataset = datasets[0]
        dataset_id = dataset["id"]

        # Try to get latest results
        result_response = requests.get(f"{API_BASE_URL}/datasets/{dataset_id}/latest-result", timeout=10)
        has_results = result_response.status_code == 200
        result = result_response.json() if has_results else {}

        # KPI Cards
        kpi_cards = []

        kpi_cards.append(html.Div([
            html.Div(f"{dataset.get('row_count', 0):,}", className='metric-value'),
            html.Div("Total Rows", className='metric-label'),
        ], className='metric-card', style={'background': f'linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%)'}))

        kpi_cards.append(html.Div([
            html.Div(str(dataset.get("column_count", 0)), className='metric-value'),
            html.Div("Columns", className='metric-label'),
        ], className='metric-card', style={'background': f'linear-gradient(135deg, {COLORS["warning"]} 0%, #ff922b 100%)'}))

        kpi_cards.append(html.Div([
            html.Div(f"{result.get('overall_quality_score', 0):.1%}" if has_results else "N/A", className='metric-value'),
            html.Div("Quality Score", className='metric-label'),
        ], className='metric-card', style={'background': f'linear-gradient(135deg, {COLORS["success"]} 0%, #51cf66 100%)'}))

        quality_score = result.get('overall_quality_score', 0) if has_results else 0

        # Gauge chart
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=quality_score * 100,
            title={'text': "Quality Score"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': COLORS['primary']},
                'steps': [
                    {'range': [0, 50], 'color': '#f0f0f0'},
                    {'range': [50, 80], 'color': '#e0e0e0'}
                ],
                'threshold': {
                    'line': {'color': COLORS['danger'], 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        gauge_fig.update_layout(height=300, margin=dict(l=0, r=0, t=50, b=0), template='plotly_white')

        # Alerts summary
        alerts_response = requests.get(f"{API_BASE_URL}/alerts/dataset/{dataset_id}/summary", timeout=10)
        alert_summary = alerts_response.json() if alerts_response.status_code == 200 else {}

        alerts_content = []
        if alert_summary.get('critical_count', 0) > 0:
            alerts_content.append(html.Div([
                html.Span(f"🔴 {alert_summary.get('critical_count', 0)} Critical Alerts", style={'fontWeight': '600', 'color': COLORS['danger']}),
            ], className='alert-critical'))

        if alert_summary.get('warning_count', 0) > 0:
            for alert in alert_summary.get('recent_warning', [])[:3]:
                alerts_content.append(html.Div([
                    html.Span(f"🟡 {alert.get('metric_type', 'Unknown')}", style={'fontWeight': '600', 'color': COLORS['warning']}),
                    html.Div(alert.get('message', ''), style={'fontSize': '12px', 'color': COLORS['warning']})
                ], className='alert-warning'))

        return html.Div([
            html.H1("📊 Dashboard", className='page-title'),
            html.P("Real-time data quality monitoring overview", className='page-subtitle'),

            # KPI Grid
            html.Div(kpi_cards, style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '16px', 'marginBottom': '30px'}),

            # Quality gauge
            html.Div([
                dcc.Graph(figure=gauge_fig)
            ], className='card', style={'marginBottom': '30px'}),

            # Alerts section
            html.Div([
                html.H3("Recent Alerts", style={'fontSize': '18px', 'fontWeight': '600', 'marginBottom': '12px'}),
                html.Div(alerts_content if alerts_content else html.Div("✅ No alerts", style={'color': COLORS['success'], 'fontWeight': '600'})),
            ], className='card'),

            # Analysis button
            html.Div([
                html.Button(
                    "🔍 Run Quality Analysis",
                    style={'padding': '12px 24px', 'fontSize': '16px', 'marginTop': '20px'}
                ),
            ], className='card', style={'marginTop': '20px'}),
        ])

    except Exception as e:
        return html.Div([
            html.H1("📊 Dashboard", className='page-title'),
            html.Div(f"❌ Error loading dashboard: {str(e)}", className='card', style={'color': COLORS['danger'], 'padding': '20px'})
        ])
