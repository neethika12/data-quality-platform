from dash import html

def render():
    return html.Div([
        html.H1("⚙️ Configure", className='page-title'),
        html.P("Configure system thresholds and settings", className='page-subtitle'),
        html.Div([
            html.P("Coming soon: Threshold configuration and system settings.", style={'color': '#7f8c8d'})
        ], className='card')
    ])
