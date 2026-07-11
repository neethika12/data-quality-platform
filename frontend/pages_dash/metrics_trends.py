from dash import html

def render():
    return html.Div([
        html.H1("📉 Metrics Trends", className='page-title'),
        html.P("Track quality metrics over time", className='page-subtitle'),
        html.Div([
            html.P("Coming soon: Time-series visualization with trend analysis.", style={'color': '#7f8c8d'})
        ], className='card')
    ])
