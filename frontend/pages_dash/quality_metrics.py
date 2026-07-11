from dash import html

def render():
    return html.Div([
        html.H1("✅ Quality Metrics", className='page-title'),
        html.P("Detailed data quality and completeness analysis", className='page-subtitle'),
        html.Div([
            html.P("Coming soon: Detailed null rate analysis, anomaly detection, and completeness metrics.", style={'color': '#7f8c8d'})
        ], className='card')
    ])
