import dash
from dash import dcc, html, Input, Output, ctx
import dash_leaflet as dl
import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import random
import sqlite3
import helper_functions as h

class LegoGPT:
    """ Class to visualize LEGO results. """

    def __init__(self, input_type: str, filepath_lego: str):

        # check if input_type is valid
        if input_type not in ["excel", "sqlite"]:
            raise ValueError("Invalid input type. Please choose either 'excel' or 'sqlite'.")
        self.input_type = input_type
        self.filepath_lego = filepath_lego
        self.load_data()  # Load data on initialization
        self.create_app()  # Initialize Dash app
        self.setup_layout()  # Define layout
        self.setup_callbacks()  # Define callbacks
        
    def load_data(self, ):
        """ Load network data from LEGO results file. """

        filepath_coords = self.filepath_lego + "Power_BusInfo.xlsx"

        tables = ["rp", "k", "i", "g", "gi", "la", "vLineP", "vGenP","vStIntraRes", "vStInterRes", "pDemandP"]

        if input_type == "sqlite":
            # connect to the database
            conn = sqlite3.connect(self.filepath_lego + "result.sqlite")
            # print out all tables in the database
            # cursor = conn.cursor()
            # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            # print(cursor.fetchall())


            for table in tables:
                # load the data as variable with the table name
                setattr(self, table, h.extract_table_to_dataframe(conn, table))
            
            # region remove unnecessary index column in sets
            self.rp.drop(columns=["index"], inplace=True)
            self.rp.rename(columns={"0": "values"}, inplace=True)

            self.k.drop(columns=["index"], inplace=True)
            self.k.rename(columns={"0": "values"}, inplace=True)

            self.i.drop(columns=["index"], inplace=True)    
            self.i.rename(columns={"0": "values"}, inplace=True)

            self.g.drop(columns=["index"], inplace=True)
            self.g.rename(columns={"0": "values"}, inplace=True)

            self.gi.rename(columns={"0": "g"}, inplace=True)
            self.gi.rename(columns={"1": "i"}, inplace=True)
            self.gi.drop(columns=["index"], inplace=True)

            self.la.drop(columns=["index"], inplace=True)
            self.la.rename(columns={"0": "i"}, inplace=True)
            self.la.rename(columns={"1": "j"}, inplace=True)
            self.la.rename(columns={"2": "c"}, inplace=True)

            self.vLineP.rename(columns={"level_0": "rp"}, inplace=True)
            self.vLineP.rename(columns={"level_1": "k"}, inplace=True)
            self.vLineP.rename(columns={"level_2": "i"}, inplace=True)
            self.vLineP.rename(columns={"level_3": "j"}, inplace=True)
            self.vLineP.rename(columns={"level_4": "c"}, inplace=True)
            # Iterate over vLineP DataFrame
            for row_idx, row in enumerate(self.vLineP.itertuples(index=True)):  # Keep index for modification
                node_set = {row.i, row.j}  # Use set for order-independent comparison

                # Iterate over self.la DataFrame to find the matching line
                for idx, line in enumerate(self.la.itertuples(index=False)):
                    if {line.i, line.j} == node_set:
                        # Update the corresponding row in vLineP
                        self.vLineP.at[row_idx, "line"] = str(int(idx))  # Use row index from enumerate
                        break  # Stop searching once a match is found


                
            self.coords = h.load_lat_lon(filepath_coords)

        elif input_type == "excel":
            for table in tables:
                print(f"Loading table {table}...")
                if table == "vLineP":
                    df, df_lines = h.extract_excel_to_dataframe(filepath_lego, table)
                    self.vLineP = df
                    self.la = df_lines
                elif table == "gi":
                    df, df_g = h.extract_excel_to_dataframe(filepath_lego, table)
                    self.gi = df
                    self.g = df_g
                elif table == "la" or table == "g": # get from other dataframe
                    continue
                else:
                    # load the data as variable with the table name
                    setattr(self, table, h.extract_excel_to_dataframe(filepath_lego, table))
            self.coords = h.extract_excel_to_dataframe(filepath_lego, "coords")

            # only take values where duplicate is False
            self.vLineP = self.vLineP[self.vLineP["duplicate"] == False]
            # drop duplicate column
            self.vLineP.drop(columns=["duplicate"], inplace=True)


            # drop where everything except value is the same

            # save to csv
            self.vLineP.to_csv("vLineP.csv", index=False)
                           
        else:
            raise ValueError("Invalid input type. Please choose either 'excel' or 'sqlite'.")

        # Compute bounds for map display
        self.bounds = [
            [min(self.coords['lat']), min(self.coords['lon'])],
            [max(self.coords['lat']), max(self.coords['lon'])]
        ]

        self.vLineP_max = self.vLineP["values"].max()
        self.vLineP_min = self.vLineP["values"].min()   

    def filter_dataframe(self, attr_str: str, rp: str, scope: str, local_node: str=None, local_line: str=None, k_range: list = []) -> pd.DataFrame:
        """"
        Filter the dataframe based on the values for rp and k."
        """

        if attr_str == "vGenP":
            df = self.vGenP
            if df is None: # in case the attribute exits but is not loaded
                return None
            if "rp" in df.columns:
                df = df[df["rp"] == rp]
            if len(k_range) > 0:
                df = df[df["k"].isin(k_range)]
            if scope == "Local":
                g_local = self.gi[self.gi["i"] == local_node]
                df = df[df["g"].isin(g_local["g"])]
        elif attr_str == "pDemandP":
            df = self.pDemandP
            if df is None:
                return None
            if "rp" in df.columns:
                df = df[df["rp"] == rp]
            if len(k_range) > 0:
                df = df[df["k"].isin(k_range)]            
            if scope == "Local":
                df = df[df["i"] == local_node]
            elif scope == "Global":
                df = df.groupby(["k"]).sum().reset_index()
        elif attr_str == "vLineP":
            df = self.vLineP
            if df is None:
                return None
            if "rp" in df.columns:
                df = df[df["rp"] == rp]
            if len(k_range) > 0:
                df = df[df["k"].isin(k_range)]
            if scope == "Local":
                df = df[df["line"] == local_line]
                
        else: 
            df = None
            

        return df

    def create_app(self):
        """ Initialize Dash app. """
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True, prevent_initial_callbacks=False)

    def setup_layout(self):
        """ Define app layout. """

        self.long_format = True if (len(self.rp) == 1 and len(self.k) > 24) else False
        display_time_range = 'block' if self.long_format else 'none'
        display_rp = 'none' if self.long_format else 'block'



        self.app.layout = html.Div([

            # === GLOBAL TOP CONTROLS ROW (RP dropdown + Slider on left, Axis dropdowns + Button on right) ===
            html.Div([

                # Left side: Dropdown + Slider
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='rep-period-dropdown',
                            options=[{"label": f"Period: {p}", "value": p} for p in self.rp["values"].values],
                            value=self.rp["values"][0],
                            clearable=False,
                            style={'width': '130px', 'font-weight': 'bold', } ,
                        ),
                    ], style={'margin-right': '20px', 'display': display_rp}),

                    html.Div([
                        dcc.Slider(
                            id='time-slider',
                            min=1,
                            max=len(self.k),
                            step=1,
                            # marks={k: {'label': str(k) } for k in self.k}, # fonttstyle set in css file
                            marks=(
                                {
                                    1: {'label': 'k0001'},
                                    len(self.k) // 2: {'label': f"k{len(self.k) // 2:04d}"},
                                    len(self.k) : {'label': f"k{len(self.k) :04d}"},
                                } if self.long_format else {k: {'label': str(k)} for k in self.k}
                            ),
                            tooltip={"placement": "top", "always_visible": True},
                            value=1,
                        ),
                    ], style={'flex': '1'}),
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
                            options=[
                                {'label': 'Y: Power Flow', 'value': 'power_flow'},
                                {'label': 'Y: Dispatch', 'value': 'dispatch'},
                                {'label': 'Y: Demand', 'value': 'demand'},
                                {'label': 'Y: Storage Intra', 'value': 'storage_intra'},


                            ],
                            value='dispatch',
                            clearable=False,
                            style={'width': '120px', 'font-weight': 'bold'},
                        ),
                    ], style={'margin-right': '10px', 'margin-left': '4px'}),

                    html.Div([
                        # html.Label("X-Axis:", style={'font-weight': 'bold'}),
                        dcc.Dropdown(
                            id="x-axis-dropdown",
                            options=[
                                {'label': 'X: Time', 'value': 'time'},
                                {'label': 'X: Generator', 'value': 'generator'},
                                {'label': 'X: Storage', 'value': 'storage'},
                                {'label': 'X: Line', 'value': 'line'},

                            ],
                            value='time',
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
            dcc.Store(id="last-clicked-node", data=self.i["values"][0]),

            # === MAIN SECTION: Map + Graph ===
            html.Div([

                # Left Section: Map
                html.Div([
                    dl.Map(children=[
                        dl.TileLayer(url='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                                     attribution='&copy; <a href="https://carto.com/">CARTO</a>'),
                        dl.LayerGroup(id="network-layer"),
                    ], bounds=self.bounds, style={'height': '100%', 'width': '100%', 'background-color': '#6BA3A3'}, id="network-map"),
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
             Input("time-slider", "value")
            ]          
        )
        def update_network(selected_period, selected_time):
            # colors = self.generate_colors(selected_period, selected_time)

            def generate_colors(vLineP_filtered):
                color_values = vLineP_filtered["values"].to_numpy()
                # scale to min/max of the entire dataset
                color_values = (color_values - self.vLineP_min) / (self.vLineP_max - self.vLineP_min)
                color_map = plt.get_cmap('RdYlGn_r')
                return [
                    "#{:02x}{:02x}{:02x}".format(int(255 * c[0]), int(255 * c[1]), int(255 * c[2]))
                    for c in [color_map(s) for s in color_values]
                ]
            
            selected_time = f"k{selected_time:04d}"
            vLineP_filtered = self.vLineP[
                    (self.vLineP["rp"] == selected_period) & (self.vLineP["k"] == selected_time) # NOTE: check if vLineP exists in both directions -> DOES NOT!
                ]

            positions = []
            for i, j, flow in zip(vLineP_filtered["i"].values, vLineP_filtered["j"].values, vLineP_filtered["values"].values):
                if flow < 0: # reverse the direction for the arrows
                    positions.append([(self.coords.loc[j, 'lat'], self.coords.loc[j, 'lon']), (self.coords.loc[i, 'lat'], self.coords.loc[i, 'lon'])])
                else:
                    positions.append([(self.coords.loc[i, 'lat'], self.coords.loc[i, 'lon']), (self.coords.loc[j, 'lat'], self.coords.loc[j, 'lon'])])
                
            colors = generate_colors(vLineP_filtered)

            polylines = [
                dl.Polyline(
                    positions=position,
                    color=color, weight=5, id=str(int(line)),
                    children=dl.Popup(f"Power Flow: {abs(vLineP_filtered.iloc[idx]['values']):.2f} MW"), n_clicks=0
                ) for idx, (position, line, color) in enumerate(zip(positions, vLineP_filtered["line"].values, colors))
            ]

            # make arrows using the same color as the line and use PolylineDecorator

            patterns= [[dict(offset='15%', repeat='25%', arrowHead=dict(pixelSize=15, polygon=False, pathOptions=dict(stroke=True, color=color,)))] for color in colors]
            arrows = [dl.PolylineDecorator(children=polyline, patterns=pattern, n_clicks=0) for polyline, pattern in zip (polylines, patterns)]
            circles = [
                dl.CircleMarker(
                    center=(node.lat, node.lon),
                    radius=10, fillColor="#8C564B", weight=1, color="black",
                    fill=True, fillOpacity=1, id=node.Index,
                    children=dl.Popup(node.Index), n_clicks=0
                ) for node in self.coords.itertuples(index=True)
            ]

            return [dl.TileLayer(url='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',attribution='&copy; <a href="https://carto.com/">CARTO</a>'), dl.LayerGroup(children=arrows + circles, id="network-layer" + str(random.randint(0, 1000)))] # workaround, otherwise objects with same id are not updated!


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
            [Input(node.Index, "n_clicks") for node in self.coords.itertuples(index=True)]
        )
        def store_last_clicked_node(*args):
            if not ctx.triggered:
                return None
            clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
            return clicked_id

                
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
            Output("dynamic-plot-container", "children"),
            [Input("x-axis-dropdown", "value"), 
             Input("y-axis-dropdown", "value"), 
             Input("last-clicked-line", "data"),
             Input("last-clicked-node", "data"),
             Input("rep-period-dropdown", "value"),
             Input("local-button", "children"),
             Input("time-slider-range", "value")]
        )
        def update_dynamic_plot(x_axis, y_axis, line_idx, node_idx, selected_period, scope, time_range):
            """ Update the single plot based on selected x-axis, y-axis, last-clicked line or node. """

            print(f"Updating plot: x_axis={x_axis}, y_axis={y_axis}, selected_period={selected_period}, selected_time_range={time_range}")
            print(f"Scope: {scope}")

            fig = None # Initialize figure
            y_df = None
            k_range = [str(f"k{time:04d}") for time in range(time_range[0], time_range[1] + 1)] if self.long_format else []

            if y_axis == "demand":
                y_df = self.filter_dataframe("pDemandP", rp=selected_period, scope=scope, local_node=node_idx, k_range=k_range)
            elif y_axis == "dispatch":
                y_df = self.filter_dataframe("vGenP", rp=selected_period, scope=scope, local_node=node_idx, k_range=k_range)
            elif y_axis == "power_flow":
                y_df = self.filter_dataframe("vLineP", rp=selected_period, scope=scope, local_line=line_idx, k_range=k_range)

            if y_df is not None:
                if x_axis == "time":
                    x_label = "Time"
                    if y_axis == "dispatch":
                        fig = px.area(
                            y_df,
                            x="k",  # Use categorical 'k' for x-axis
                            y="values",
                            color="g",  # Different colors for each generator
                            title="Global dispatch over time" if scope == "Global" else f"Local dispatch for {node_idx} over time",
                            labels={"k": x_label, "values": "Dispatch", "g": "Generator"},
                        )
                    elif y_axis == "demand":
                        fig = px.line(
                            y_df,
                            x="k",  # Use categorical 'i' for x-axis
                            y="values",
                            title="Demand Over Time",
                            labels={"i": x_label, "values": "Demand"},
                        )
                    elif y_axis == "power_flow":
                        fig = px.line(
                            y_df,
                            x="k",  # Use categorical 'k' for x-axis
                            y="values",
                            color="line",  # Different colors for each line
                            title="Power Flow over time" if scope == "Global" else f"Local Power Flow for {line_idx} over time",
                            labels={"k": x_label, "values": "Power Flow", "line": "Line"},
                            hover_data={"values": True, "line": True, "i": True, "j": True}  # Show values and line on hover
                        )


                elif x_axis == "generator":
                    x_label = "Generator"
                    if y_axis == "dispatch":
                        fig = px.bar(
                            y_df,
                            x="g",  # Use categorical 'g' for x-axis
                            y="values",
                            color="g",  # Different colors for each generator
                            title="Global dispatch for each generator" if scope == "Global" else f"Local dispatch for {node_idx}",
                            labels={"g": x_label, "values": "Dispatch", "k": "Time"},
                            hover_data={"values": False, "k": False}  # Show values and time on hover
                        )

               
                elif x_axis == "line":
                    x_label = "Line"
                    if y_axis == "power_flow":
                        # make histogram of all lineflow values
                        fig = px.histogram(
                            y_df,
                            x="values",
                            color="line",
                            title="Power Flow Distribution over all Lines" if scope == "Global" else f"Local Power Flow Distribution for {line_idx}",
                            # labels={"values": "Power Flow", "line": "Line"},
                            nbins=10,
                            range_x=[self.vLineP_min, self.vLineP_max]
                        )

            # check if a figure fig was created
            if fig is None:
                fig = px.scatter(title="Select a valid combination for the plot")

            # set title center
            fig.update_layout(title_x=0.5)    
            # Fix the plot size (domain of axes) to a specific portion of the figure
            fig.update_layout(
                xaxis=dict(domain=[0, 0.85]),  # Plot takes 90% of the width
                yaxis=dict(domain=[0, 1]),    # Full height
                legend=dict(
                    x=0.85,
                    y=1,
                    xanchor="left",
                    yanchor="top",
                ),
                margin=dict(l=0, r=40, t=40, b=40)
            )
            # update the background color
            fig.update_layout(paper_bgcolor="#E1EDED", plot_bgcolor="#E1EDED")
            # set the font size
            fig.update_layout(font_size=14)
            # set axis labels bold
            fig.update_layout(
                xaxis_title_font=dict(size=18, color='black'),  
                yaxis_title_font=dict(size=18, color='black')
            )   

            return html.Div([dcc.Graph(figure=fig, id="dynamic-plot" + str(random.randint(0, 1000)), style={'height': '100%', 'width': '100%', })], style={'flex': '1', 'min-width': '0', 'height': '90vh', 'margin-top': '0px'})

    def run(self):
        """ Start the Dash server. """
        self.app.run(debug=False)

if __name__ == "__main__":

    input_type = "excel"
    # filepath_lego = "C:\\Users\\Kelvin Walenta\\LEGO-GPT\\examples\\"
    filepath_lego = "C:\\Users\\Kelvin Walenta\\LEGO-GPT\\Robert\\AT+Neighbours\\"
    LegoGPT(input_type=input_type, filepath_lego=filepath_lego).run()
