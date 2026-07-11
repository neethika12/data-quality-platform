from dash import html

def render():
    return html.Div([
        html.H1("🔔 Alerts", className='page-title'),
        html.P("View and manage quality alerts", className='page-subtitle'),
        html.Div([
            html.P("Coming soon: Alert log with filtering, acknowledgment, and severity levels.", style={'color': '#7f8c8d'})
        ], className='card')
    ])
