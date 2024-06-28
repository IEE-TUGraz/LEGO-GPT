import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import data_helper as dh
import plot_helper as ph


scenario_folder = "examples\\001_Base_Example\\"
line_load = dh.load_line_load(scenario_folder)

# get number of representative periods
num_rp = line_load.shape[1] - 5

options = [{'label': 'rp' + str(i), 'value': i} for i in range(1, num_rp+1)]
default_value = 1

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("Select an Element to Plot"),
    dcc.Dropdown(
        id='element-dropdown',
        options=options,
        value=default_value  # Default value
    ),
    dcc.Graph(id='element-graph', style={'height': '80vh', 'width': '80vh'})
])

# Callback to update the graph
@app.callback(
    Output('element-graph', 'figure'),
    Input('element-dropdown', 'value')
)
def update_graph(selected_element: int = 1):
    fig = ph.plot_line_load(scenario_folder, selected_element)
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
