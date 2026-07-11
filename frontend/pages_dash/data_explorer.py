from dash import html, dcc, callback, Input, Output
import requests

API_BASE_URL = "http://localhost:8000/api"

def render():
    return html.Div([
        html.H1("📁 Data Explorer", className='page-title'),
        html.P("Upload and explore your datasets", className='page-subtitle'),

        html.Div([
            html.H3("Upload New Dataset", style={'fontSize': '18px', 'fontWeight': '600', 'marginBottom': '16px'}),

            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    '📤 Drag and drop CSV or Parquet file here, or click to select'
                ]),
                style={
                    'width': '100%',
                    'height': '100px',
                    'lineHeight': '100px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '8px',
                    'textAlign': 'center',
                    'cursor': 'pointer',
                    'backgroundColor': '#f8f9fa',
                },
                multiple=False
            ),

            html.Div(id='upload-status', style={'marginTop': '16px'}),
        ], className='card'),

        html.Div([
            html.H3("Your Datasets", style={'fontSize': '18px', 'fontWeight': '600', 'marginBottom': '16px'}),
            html.Div(id='datasets-list'),
        ], className='card', style={'marginTop': '20px'}),
    ])

@callback(
    Output('datasets-list', 'children'),
    Input('datasets-list', 'id'),
    prevent_initial_call=False
)
def load_datasets(_):
    try:
        response = requests.get(f"{API_BASE_URL}/datasets", timeout=10)
        datasets = response.json().get("datasets", []) if response.status_code == 200 else []

        if not datasets:
            return html.Div("No datasets yet. Upload one to get started!", style={'color': '#7f8c8d'})

        rows = []
        for ds in datasets:
            rows.append(html.Div([
                html.Div(f"📄 {ds['name']}", style={'fontWeight': '600', 'fontSize': '16px'}),
                html.Div(f"Rows: {ds.get('row_count', 0):,} | Columns: {ds.get('column_count', 0)}", style={'fontSize': '13px', 'color': '#7f8c8d', 'marginTop': '4px'}),
            ], style={'padding': '12px', 'borderBottom': '1px solid #e0e0e0'})
            )

        return html.Div(rows)

    except Exception as e:
        return html.Div(f"Error: {str(e)}", style={'color': '#ff6b6b'})
