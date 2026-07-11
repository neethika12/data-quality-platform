from dash import html, dcc, callback, Input, Output
import requests
import plotly.express as px
import pandas as pd

API_BASE_URL = "http://localhost:8000/api"

def render():
    return html.Div([
        html.H1("📈 Drift Analysis", className='page-title'),
        html.P("Detect and analyze distribution drift in your data", className='page-subtitle'),
        html.Div(id='drift-content'),
    ])

@callback(
    Output('drift-content', 'children'),
    Input('drift-content', 'id'),
    prevent_initial_call=False
)
def load_drift(_):
    try:
        response = requests.get(f"{API_BASE_URL}/datasets", timeout=10)
        datasets = response.json().get("datasets", []) if response.status_code == 200 else []

        if not datasets:
            return html.Div("No datasets available", className='card')

        dataset_id = datasets[0]["id"]
        result_response = requests.get(f"{API_BASE_URL}/datasets/{dataset_id}/latest-result", timeout=10)

        if result_response.status_code != 200:
            return html.Div("Run analysis first to see drift results", className='card')

        result = result_response.json()
        drift = result.get("drift_analysis", {})
        drifted_features = drift.get("drifted_features", [])

        content = []

        # Metrics
        content.append(html.Div([
            html.Div([
                html.Div(f"{drift.get('overall_drift_score', 0):.2f}", style={'fontSize': '32px', 'fontWeight': '700'}),
                html.Div("Drift Score", style={'fontSize': '12px', 'color': '#7f8c8d'}),
            ], className='metric-card', style={'background': '#ffa94d'} if drift.get('severity_level') == 'WARNING' else {'background': '#52c41a'}),

            html.Div([
                html.Div(f"{drift.get('drifted_count', 0)}/{drift.get('feature_count', 0)}", style={'fontSize': '32px', 'fontWeight': '700'}),
                html.Div("Features Drifted", style={'fontSize': '12px', 'color': '#7f8c8d'}),
            ], className='metric-card', style={'background': '#667eea'}),
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(150px, 1fr))', 'gap': '16px', 'marginBottom': '20px'}))

        # Drifted features table
        if drifted_features:
            rows = [html.Tr([
                html.Th("Feature", style={'padding': '8px', 'textAlign': 'left', 'fontWeight': '600', 'borderBottom': '2px solid #e0e0e0'}),
                html.Th("Drift Score", style={'padding': '8px', 'textAlign': 'left', 'fontWeight': '600', 'borderBottom': '2px solid #e0e0e0'}),
                html.Th("P-Value", style={'padding': '8px', 'textAlign': 'left', 'fontWeight': '600', 'borderBottom': '2px solid #e0e0e0'}),
                html.Th("Test", style={'padding': '8px', 'textAlign': 'left', 'fontWeight': '600', 'borderBottom': '2px solid #e0e0e0'}),
            ])]

            for feature in drifted_features[:10]:
                rows.append(html.Tr([
                    html.Td(feature['feature'], style={'padding': '8px', 'borderBottom': '1px solid #e0e0e0'}),
                    html.Td(f"{feature['drift_score']:.3f}", style={'padding': '8px', 'borderBottom': '1px solid #e0e0e0'}),
                    html.Td(f"{feature['p_value']:.6f}", style={'padding': '8px', 'borderBottom': '1px solid #e0e0e0'}),
                    html.Td(feature['test_method'], style={'padding': '8px', 'borderBottom': '1px solid #e0e0e0'}),
                ]))

            content.append(html.Table(rows, style={'width': '100%', 'borderCollapse': 'collapse'}))
        else:
            content.append(html.Div("✅ No significant drift detected", style={'color': '#52c41a', 'fontWeight': '600'}))

        return html.Div(content, className='card')

    except Exception as e:
        return html.Div(f"Error: {str(e)}", className='card', style={'color': '#ff6b6b'})
