import dash
from dash import dcc, html, Input, Output, ctx
import dash_leaflet as dl
import numpy as np
import os
import helper_functions as h
from data_loader import load_data
from ui_handler import generate_network_map, generate_dynamic_plot
import sys

class LegoGPT:
    """ Class to visualize LEGO results. """

    def __init__(self, config_path: str = None):
        """ Initialize the class. """

        # Load configuration from this directory or from the provided path
        config = h.load_config("config.yml") if config_path is None else h.load_config(config_path)
        self.input_dir = config["input_dir"]
        self.input_type = config["input_type"]
        self.tables = config["tables"]
        self.dropdown_options_y = config["dropdown_options_y"]
        self.dropdown_options_x = config["dropdown_options_x"]
        self.map_options = config["map_options"]

        if self.input_type not in ["excel", "sqlite", "V2G"]:
            raise ValueError("Invalid input type. Please choose either 'excel', 'sqlite' or V2G.")

        required_tables = ["i", "la", "vLineP", "pPmax", "k"]
        missing = [t for t in required_tables if t not in self.tables]
        if missing:
            raise ValueError(f"Missing required table(s): {', '.join(missing)}")


        self.load_data()  # Load data on initialization
        self.create_app()  # Initialize Dash app
        self.setup_layout()  # Define layout
        self.setup_callbacks()  # Define callbacks
     
    def load_data(self, ):
        """ Load network data from LEGO results file. """
        load_data(self)
        
    def create_app(self):
        """ Initialize Dash app. """
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True, prevent_initial_callbacks=False)

    def setup_layout(self):
        """ Define app layout. """

        self.long_format = True if "rp" not in self.tables or (len(self.rp) == 1 and len(self.k) > 24) else False
        display_time_range = 'block' if self.long_format else 'none'
        display_rp = 'none' if self.long_format else 'block'
        if not self.long_format:
            options = [{"label": f"Period: {p}", "value": p} for p in self.rp["values"].values]
            value = self.rp["values"][0]
        else:
            options = ["Period: All"]
            value = "All"
        self.app.layout = html.Div([

            # === GLOBAL TOP CONTROLS ROW (RP dropdown + Slider on left, Axis dropdowns + Button on right) ===
            html.Div([

                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='rep-period-dropdown',
                            options=options,
                            value=value,
                            clearable=False,
                            style={'width': '130px', 'font-weight': 'bold'},
                        ),
                    ], style={'margin-right': '20px', 'display': display_rp}),

                    # === Time Slider + Optional Number Input ===
                    html.Div([
                        # Slider
                        html.Div([
                            dcc.Slider(
                                id='time-slider',
                                min=1,
                                max=len(self.k),
                                step=1,
                                marks=(
                                    {
                                        1: {'label': 'k0001'},
                                        len(self.k) // 2: {'label': f"k{len(self.k) // 2:04d}"},
                                        len(self.k): {'label': f"k{len(self.k):04d}"},
                                    } if self.long_format else {k: {'label': str(k)} for k in self.k}
                                ),
                                tooltip={"placement": "top", "always_visible": True},
                                value=1,
                            )
                        ], style={'flex': '1'}),  # Slider fills most of the space

                        # Number input (only if long format)
                        html.Div([
                            dcc.Input(
                                id='time-slider-input',
                                type='number',
                                min=1,
                                max=len(self.k),
                                step=1,
                                value=1,
                                style={'width': '70px', 'margin-left': '10px'}
                            )
                        ], style={'display': display_time_range, 'flex': 'none'})  # input stays compact
                    ], style={'flex': '1', 'display': 'flex', 'align-items': 'center', 'gap': '10px'}),

                ], style={
                    'display': 'flex',
                    'align-items': 'center',
                    'flex': '1',
                    'margin-right': '20px',
                    'min-width': '0',
                    'max-width': '50%'
                }),


                # Right side: Axis Dropdowns + Button (left-aligned within their container) + RangeSlider
                html.Div([
                    html.Div([
                        # html.Label("Y-Axis:", style={'font-weight': 'bold'}),
                        dcc.Dropdown(
                            id="y-axis-dropdown",
                            options=self.dropdown_options_y,
                            value=self.dropdown_options_y[0]['value'],
                            clearable=False,
                            style={'width': '120px', 'font-weight': 'bold'},
                        ),
                    ], style={'margin-right': '10px', 'margin-left': '4px'}),

                    html.Div([
                        # html.Label("X-Axis:", style={'font-weight': 'bold'}),
                        dcc.Dropdown(
                            id="x-axis-dropdown",
                            options=self.dropdown_options_x,
                            value=self.dropdown_options_x[0]['value'],
                            clearable=False,
                            style={'width': '120px', 'font-weight': 'bold'},
                        ),
                    ], style={'margin-right': '10px'}),

                    html.Div([
                        # html.Label("Scope:", style={'font-weight': 'bold'}),
                        html.Button("Local", id="local-button", n_clicks=0, style={
                            'minWidth': '80px',
                            'padding': '6px 12px',
                            'display': 'flex',
                            'alignItems': 'center',
                            'font-weight': 'bold',
                        }),
                    ]),
                    # add additional slider for the range of k values if long format
                    html.Div([
                        dcc.RangeSlider(
                            id='time-slider-range',
                            min=1,
                            max=len(self.k),
                            step=1,
                            marks=(
                                {
                                    1: {'label': 'k0001'},
                                    len(self.k) // 2: {'label': f"k{len(self.k) // 2:04d}"},
                                    len(self.k) : {'label': f"k{len(self.k) :04d}"},
                                } 
                            ),
                            tooltip={"placement": "top", "always_visible": True},
                            #allowCross=False,
                            value=[1, 24],
                            pushable=24,
                            
                        ),

                    ], style={'margin-right': '10px', "flex": "1","display": display_time_range}),





                ], style={
                    'display': 'flex',
                    'align-items': 'center',
                    'justify-content': 'flex-start',
                    'width': '50%',
                }),

            ], style={
                'display': 'flex',
                'align-items': 'center',
                'margin-bottom': '10px',
                'justify-content': 'space-between',
                'flex-wrap': 'wrap'
            }),

            dcc.Store(id="last-clicked-line", data=self.la.index[0]),
            dcc.Store(id="last-clicked-node", data=self.i.index[0]),
            dcc.Store(id="map-zoom", data=self.map_options["default_zoom"]),  # Default zoom

            # === MAIN SECTION: Map + Graph ===
            html.Div([

                # Left Section: Map
                html.Div([
                    dl.Map(children=[
                        dl.TileLayer(url='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                                     attribution='&copy; <a href="https://carto.com/">CARTO</a>'),
                        dl.LayerGroup(id="network-layer"),
                    ], bounds=self.bounds, style={'height': '100%', 'width': '100%', 'background-color': '#6BA3A3'}, id="network-map",
                    zoom=self.map_options["default_zoom"], center=[np.mean(self.i['lat']), np.mean(self.i['lon'])]),
                ], style={'flex': '1', 'min-width': '0', 'height': '90vh'}),

                # Right Section: Graph
                html.Div([                   
                    dcc.Graph(id="dynamic-plot", style={'width': '100%', 'height': '100%', 'background-color': '#6BA3A3'}), # NOTE: this whole html.Div is replaced in the callback !!                  
                ], id="dynamic-plot-container", style={'flex': '1', 'min-width': '0', 'height': '90vh', 'margin-top': '0px'})
            ], style={'display': 'flex', 'gap': '10px', 'height': '90vh', 'flex-wrap': 'wrap'}),
        ], style={"background-color": "#6BA3A3", "padding": "10px"})

    def setup_callbacks(self):
        """ Define callbacks for interactivity. """

        @self.app.callback(
            Output("network-map", "children"),  
            [Input("rep-period-dropdown", "value"),
             Input("time-slider", "value"),
             Input("map-zoom", "data")
            ],          
             # prevent_initial_call=True
        )
        def update_network(selected_period, selected_time, zoom_level):
            return generate_network_map(
                vLineP=self.vLineP,
                buses=self.i,
                selected_period=selected_period,
                selected_time=selected_time,
                long_format=self.long_format,
                zoom_level=zoom_level,
                map_options=self.map_options,
            )
        
        @self.app.callback(
            Output("last-clicked-line", "data"),
            [Input(str(line.Index), "n_clicks") for line in self.la.itertuples(index=True)]
        )
        def store_last_clicked_line(*args):
            if not ctx.triggered:
                return None
            
            clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
            return clicked_id

        @self.app.callback(
            Output("last-clicked-node", "data"),
            [Input(node.Index, "n_clicks") for node in self.i.itertuples(index=True)]
        )
        def store_last_clicked_node(*args):
            if not ctx.triggered:
                return None
            clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
            return clicked_id
        
        @self.app.callback(
            Output("time-slider", "value"),
            Output("time-slider-input", "value"),
            Input("time-slider", "value"),
            Input("time-slider-input", "value"),
        )
        def sync_slider_and_input(slider_val, input_val):
            ctx = dash.callback_context
            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate

            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if triggered_id == "time-slider":
                return slider_val, slider_val
            else:
                return input_val, input_val
               
        @self.app.callback(
            Output("local-button", "children"),
            Input("local-button", "n_clicks")
        )
        def toggle_button_label(n_clicks):
            if n_clicks % 2 == 0:
                return "Local"
            else:
                return "Global"

        @self.app.callback(
            Output("map-zoom", "data"),
            Input("network-map", "zoom")
        )
        def store_map_zoom(zoom_level):
            return zoom_level

        @self.app.callback(
            Output("dynamic-plot-container", "children"),
            [Input("x-axis-dropdown", "value"), 
             Input("y-axis-dropdown", "value"), 
             Input("last-clicked-line", "data"),
             Input("last-clicked-node", "data"),
             Input("rep-period-dropdown", "value"),
             Input("local-button", "children"),
             Input("time-slider-range", "value")],
             # prevent_initial_call=True

        )
        def update_dynamic_plot(x_axis, y_axis, line_idx, node_idx, selected_period, scope, time_range):
            return generate_dynamic_plot(
                self=self,
                x_axis=x_axis,
                y_axis=y_axis,
                line_idx=line_idx,
                node_idx=node_idx,
                selected_period=selected_period,
                scope=scope,
                time_range=time_range
            )
    
    def run(self):
        """ Start the Dash server. """
        self.app.run(debug=False)

if __name__ == "__main__":
    # check for passed config file (if calling from command line)
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.yml"

    # fallback if config doesn't exist
    if not os.path.exists(config_path):
        h.copy_default_config()  # assumes it writes to config.yml
    else:
        # Run with specified config
        LegoGPT(config_path=config_path).run()