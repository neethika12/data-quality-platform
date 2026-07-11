from dash import html

def render():
    return html.Div([
        html.H1("📋 Reports", className='page-title'),
        html.P("Generate and export quality analysis reports", className='page-subtitle'),
        html.Div([
            html.P("Coming soon: Report generation and export functionality.", style={'color': '#7f8c8d'})
        ], className='card')
    ])
