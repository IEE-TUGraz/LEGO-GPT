import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import data_helper as dh
import plot_helper as ph
from dash import no_update


# ----- Path to the scenario folder -----
scenario_folder = "C:\\Users\\Kelvin Walenta\\LEGO-GPT\\LEGO-GPT\\examples\\001_Base_Example"

results_options = ["Total energy", "Storage Level"]
data_total_energy = dh.load_total_energy(scenario_folder)
data_storage_level = dh.load_storage_level(scenario_folder)

# ----- Content for the network visualization -----
data_network, options_network = dh.load_line_load(scenario_folder)


# Initialize the Dash app
app = Dash(__name__)

# Layout of the combined app
app.layout = html.Div([
    html.Div([
        html.H2("LEGO Results"),
        dcc.Dropdown(
            id='element-dropdown-results',
            options=[{'label': i, 'value': i} for i in results_options],
            value='Total energy'  # Default value
        ),
        dcc.Graph(id='element-graph-results', style={'height': '80vh', 'width': '80vh'})
    ], style={'display': 'inline-block', 'width': '48%', 'vertical-align': 'top'}),

    html.Div([
        html.H2("Network"),
        dcc.Dropdown(
            id='element-dropdown-network',
            options=options_network,
            value=1  # Default value
        ),
        dcc.Graph(id='element-graph-network', style={'height': '80vh', 'width': '80vh'})
    ], style={'display': 'inline-block', 'width': '48%', 'vertical-align': 'top'})
])


# Callback for the results app
@app.callback(
    Output('element-graph-results', 'figure'),
    Input('element-dropdown-results', 'value')
)
def update_graph_results(selected_element):
    if selected_element == "Total energy":
        fig = ph.plot_energy_sources(scenario_folder)
    elif selected_element == "Storage Level":
        fig = ph.plot_storage_level(scenario_folder)
    return fig

# Callback for the network app
@app.callback(
    Output('element-graph-network', 'figure'),
    Input('element-dropdown-network', 'value')
)
def update_graph_network(selected_element):
    fig = ph.plot_line_load(scenario_folder, selected_element)
    fig.update_traces(hoverinfo="none", hovertemplate=None)
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)