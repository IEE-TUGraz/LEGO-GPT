# map_helper.py
import dash_leaflet as dl
import matplotlib.pyplot as plt
import pandas as pd
import random
import plotly.express as px
import random
from dash import html, dcc

def generate_network_map(vLineP: pd.DataFrame, buses:pd.DataFrame, selected_period: str, selected_time: int, long_format: bool, zoom_level: int, map_options: dict) -> list:
    """
    Generates a network map visualization using power flow data and bus locations.
    
    Args:
        vLineP (pd.DataFrame): DataFrame containing power flow data with columns:
            - "i": Starting bus ID of the line.
            - "j": Ending bus ID of the line.
            - "values": Power flow values.
            - "rel_values": Relative power flow values (used for color mapping).
            - "line": Line IDs.
            - "k": Time step identifier.
            - "rp": Period identifier.
            - "pPmax": Line rating (maximum power capacity).

        buses (pd.DataFrame): DataFrame containing bus location data with columns:
            - "lat": Latitude of the bus.
            - "lon": Longitude of the bus.

        selected_period (str): The selected period identifier for filtering the data.
        selected_time (int): The selected time step identifier for filtering the data.
        long_format (bool): Whether the data is in long format (only filter by time) or not.
        zoom_level (int): The current zoom level of the map.

        map_options (dict): Dictionary containing map configuration options:
            - "line_weight": Line thickness for the polylines.
            - "arrow_zoom_scale": Scaling factor for arrow sizes based on zoom level.
            - "arrow_min_size": Minimum size for arrows.
            - "node_zoom_scale": Scaling factor for node sizes based on zoom level.
            - "node_min_size": Minimum size for nodes.
            - "default_zoom": Default zoom level if none is provided.

    Returns:
        list: A list of Dash Leaflet components representing the network map, including:
            - A tile layer for the map background.
            - A layer group containing arrows (power flow directions) and circles (bus nodes).

    """
    selected_time = f"k{selected_time:04d}"
    # Use config values
    line_weight = map_options["line_weight"]
    arrow_scale = map_options["arrow_zoom_scale"]
    arrow_min = map_options["arrow_min_size"]
    node_scale = map_options["node_zoom_scale"]
    node_min = map_options["node_min_size"]
    default_zoom = map_options["default_zoom"]

    if long_format:
        vLineP_filtered = vLineP[vLineP["k"] == selected_time]
    else:
        vLineP_filtered = vLineP[(vLineP["rp"] == selected_period) & (vLineP["k"] == selected_time)]

    # Generate positions and colors
    positions = []
    for i, j, flow in zip(vLineP_filtered["i"].values, vLineP_filtered["j"].values, vLineP_filtered["values"].values):
        if flow < 0:
            positions.append([(buses.loc[j, 'lat'], buses.loc[j, 'lon']), (buses.loc[i, 'lat'], buses.loc[i, 'lon'])])
        else:
            positions.append([(buses.loc[i, 'lat'], buses.loc[i, 'lon']), (buses.loc[j, 'lat'], buses.loc[j, 'lon'])])

    color_values = vLineP_filtered["rel_values"].to_numpy()
    color_map = plt.get_cmap('RdYlGn_r')
    colors = [
        "#{:02x}{:02x}{:02x}".format(int(255 * c[0]), int(255 * c[1]), int(255 * c[2]))
        for c in [color_map(s) for s in color_values]
    ]

    polylines = [
        dl.Polyline(
            positions=position,
            color=color, weight=line_weight, id=str(int(line)),
            children=[
                dl.Popup(f"Power Flow: {abs(vLineP_filtered.iloc[idx]['values']):.2f} MW, Line rating: {vLineP_filtered.iloc[idx]['pPmax']:.2f} MW"),
            ],
            n_clicks=0
        ) for idx, (position, line, color) in enumerate(zip(positions, vLineP_filtered["line"].values, colors))
    ]

    def get_arrow_size(zoom):
        if zoom is None:
            zoom = default_zoom
        return max(arrow_min, int(zoom * arrow_scale))

    def get_node_size(zoom):
        if zoom is None:
            zoom = default_zoom
        return max(node_min, int(zoom * node_scale))

    arrow_size = get_arrow_size(zoom_level)
    node_size = get_node_size(zoom_level)

    patterns = [[dict(offset='50%', repeat='25%', arrowHead=dict(
        pixelSize=arrow_size,
        polygon=False,
        pathOptions=dict(stroke=True, color=color)
    ))] for color in colors]

    arrows = [dl.PolylineDecorator(children=polyline, patterns=pattern, n_clicks=0)
              for polyline, pattern in zip(polylines, patterns)]

    circles = [
        dl.CircleMarker(
            center=(node.lat, node.lon),
            radius=node_size, fillColor="#8C564B", weight=1, color="black",
            fill=True, fillOpacity=1, id=node.Index,
            children=dl.Popup(node.Index), n_clicks=0
        ) for node in buses.itertuples(index=True)
    ]

    tile_layer = dl.TileLayer(url='https://tile.jawg.io/jawg-light/{z}/{x}/{y}{r}.png?access-token=K29acH6XcPPrHIAdDENjCaooa47B7CDZieD4CPBI2EiVrg8iKRjqiS80D8ACx9Np')

    return [tile_layer, dl.LayerGroup(children=arrows + circles, id="network-layer" + str(random.randint(0, 1000)))]

def filter_dataframe(self, attr_str: str, rp: str, scope: str, local_node: str=None, local_line: str=None, k_range: list=[]) -> pd.DataFrame:
    """
    Filters a DataFrame based on the provided attributes, scope, and conditions.

    Args:
        attr_str (str): The attribute string specifying which DataFrame to filter.
                        Options include "vGenP", "pDemandP", and "vLineP".
        rp (str): The reporting period to filter by, applicable when `long_format` is False.
        scope (str): The scope of filtering. Options include "Local" and "Global".
                    - "Local": Filters data specific to a local node or line.
                    - "Global": Aggregates data globally (only applicable for "pDemandP").
        local_node (str, optional): The local node identifier for filtering when `scope` is "Local".
                                    Defaults to None.
        local_line (str, optional): The local line identifier for filtering when `scope` is "Local".
                                    Defaults to None.
        k_range (list, optional): A list of `k` values to filter the DataFrame by. Defaults to an empty list.

    Returns:
        pd.DataFrame: The filtered DataFrame based on the specified conditions.
                    Returns None if the specified DataFrame is not available.

    Note:
        - The method operates on different DataFrames (`vGenP`, `pDemandP`, `vLineP`) based on `attr_str`.
        - If `long_format` is False, the DataFrame is filtered by the reporting period (`rp`).
        - For "pDemandP" with "Global" scope, the data is aggregated by summing over `k` values.
        - For "vGenP" with "Local" scope, filtering is based on the local node's group (`g`).
        - For "vLineP" with "Local" scope, filtering is based on the local line identifier.

    """
   
    df = None

    if attr_str == "vGenP":
        df = self.vGenP
        if df is None:
            return None
        if not self.long_format:
            df = df[df["rp"] == rp]
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            g_local = self.gi[self.gi["i"] == local_node]
            df = df[df["g"].isin(g_local["g"])]

    elif attr_str == "pDemandP":
        df = self.pDemandP
        if df is None:
            return None
        if not self.long_format:
            df = df[df["rp"] == rp]
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            df = df[df["i"] == local_node]
        elif scope == "Global":
            df = df.groupby(["k"]).sum().reset_index()

    elif attr_str == "vLineP":
        df = self.vLineP
        if df is None:
            return None
        if not self.long_format:
            df = df[df["rp"] == rp]
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            df = df[df["line"] == local_line]

    return df

def generate_dynamic_plot(self, x_axis: str, y_axis: str, line_idx: str, node_idx: str, selected_period: str, scope: str, time_range: list) -> html.Div:
    """
    Generates a dynamic plot based on the provided parameters.
    Parameters:
        x_axis (str): The variable to be used for the x-axis. Options include "time", "generator", or "line".
        y_axis (str): The variable to be used for the y-axis. Options include "demand", "dispatch", or "power_flow".
        line_idx (str): The str(index) of the line to be used for local power flow plots.
        node_idx (str): The index (str) of the node to be used for local dispatch or demand plots.
        selected_period (str): The selected period for filtering the data.
        scope (str): The scope of the plot, either "Global" or "Local".
        time_range (list): A 2-element list specifying the range of time steps [start, end] for the plot.
    Returns:
        html.Div: A Dash HTML Div containing the generated plot as a dcc.Graph component.

    Note:
        - The function dynamically filters the data based on the provided parameters and generates a plot using Plotly.
        - The plot type and configuration depend on the combination of x_axis and y_axis values.
        - If the combination of x_axis and y_axis is invalid, a placeholder scatter plot is generated.
        - The layout of the plot is customized with specific margins, background colors, and font sizes.

    """


    print(f"Updating plot: x_axis={x_axis}, y_axis={y_axis}, selected_period={selected_period}, selected_time_range={time_range}, local_node={node_idx}, local_line={line_idx}, scope={scope}")
    
    fig = None
    y_df = None
    k_range = [str(f"k{time:04d}") for time in range(time_range[0], time_range[1] + 1)] if self.long_format else self.k["values"].values.tolist()

    if y_axis == "demand":
        y_df = filter_dataframe(self, "pDemandP", rp=selected_period, scope=scope, local_node=node_idx, k_range=k_range)
    elif y_axis == "dispatch":
        y_df = filter_dataframe(self, "vGenP", rp=selected_period, scope=scope, local_node=node_idx, k_range=k_range)
    elif y_axis == "power_flow":
        y_df = filter_dataframe(self, "vLineP", rp=selected_period, scope=scope, local_line=line_idx, k_range=k_range)

    if y_df is not None and not y_df.empty:
        if x_axis == "time":
            x_label = "Time"
            if y_axis == "dispatch":
                title = "Global dispatch over time" if scope == "Global" else f"Local dispatch for {node_idx} over time"
                fig = px.area(y_df, x="k", y="values", color="g", title=title, labels={"k": x_label, "values": "Dispatch", "g": "Generator"})
            elif y_axis == "demand":
                fig = px.line(y_df, x="k", y="values", title="Demand Over Time", labels={"i": x_label, "values": "Demand"})
            elif y_axis == "power_flow":
                title = "Power Flow over time" if scope == "Global" else f"Local Power Flow for {line_idx} over time"
                fig = px.line(y_df, x="k", y="values", color="line", title=title, labels={"k": x_label, "values": "Power Flow", "line": "Line"},
                              hover_data={"values": True, "line": True, "i": True, "j": True})

        elif x_axis == "generator" and y_axis == "dispatch":
            x_label = "Generator"
            y_df["k"] = y_df["k"].astype(str)
            y_df["g"] = y_df["g"].astype(str)
            y_df["values"] = pd.to_numeric(y_df["values"], errors="coerce")
            title = "Global dispatch for each generator" if scope == "Global" else f"Local dispatch for {node_idx}"
            fig = px.bar(y_df, x="g", y="values", color="g", title=title, labels={"g": x_label, "values": "Dispatch", "k": "Time"},
                         hover_data={"values": False, "k": False})

        elif x_axis == "line" and y_axis == "power_flow":
            x_label = "Line"
            title = "Power Flow Distribution over all Lines" if scope == "Global" else f"Local Power Flow Distribution for {line_idx}"
            fig = px.histogram(y_df, x="values", color="line", title=title, nbins=10,
                               range_x=[self.vLineP_min, self.vLineP_max])

    if fig is None:
        fig = px.scatter(title="Select a valid combination for the plot")

    fig.update_layout(title_x=0.5)
    fig.update_layout(
        xaxis=dict(domain=[0, 0.85]),
        yaxis=dict(domain=[0, 1]),
        legend=dict(x=0.85, y=1, xanchor="left", yanchor="top"),
        margin=dict(l=0, r=40, t=40, b=40),
        paper_bgcolor="#E1EDED",
        plot_bgcolor="#E1EDED",
        font_size=14,
        xaxis_title_font=dict(size=18, color='black'),
        yaxis_title_font=dict(size=18, color='black')
    )

    return html.Div([dcc.Graph(figure=fig, id="dynamic-plot" + str(random.randint(0, 1000)), style={'height': '100%', 'width': '100%'})],
                    style={'flex': '1', 'min-width': '0', 'height': '90vh', 'margin-top': '0px'})