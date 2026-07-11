from dash import html

def render():
    return html.Div([
        html.H1("🔄 Comparison", className='page-title'),
        html.P("Compare quality metrics across two analyses", className='page-subtitle'),
        html.Div([
            html.P("Coming soon: Before/after analysis with recommendations.", style={'color': '#7f8c8d'})
        ], className='card')
    ])
