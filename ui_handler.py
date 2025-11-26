"""
UI Handler Module for LEGO-GPT

This module provides functions for generating network map visualizations
and dynamic plots. It handles the rendering logic for the main UI components.
"""

import uuid
from typing import Any

import dash_leaflet as dl
import dash_leaflet.express as dlx
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from dash import dcc, html

from plot_definitions import generate_plot

# =============================================================================
# Type Definitions
# =============================================================================

MapLayerResult = tuple[dl.LayerGroup, dl.GeoJSON]
PlotResult = html.Div


# =============================================================================
# Network Map Generation
# =============================================================================

class NetworkMapGenerator:
    """Generates network map visualizations."""

    def __init__(self, data_source: Any):
        """
        Initialize the generator.

        Args:
            data_source: Object containing the data (e.g., LEGO_GPT instance).
        """
        self._data = data_source
        self._map_options = data_source.map_options
        self._technology_colors = self._map_options.get("technology_colors", {})
        self._cluster_options = self._map_options.get("cluster_options", {})

    def generate(
            self,
            selected_period: str,
            selected_time: int,
            zoom_level: int,
            pq_mode: str = "vLineP"
    ) -> MapLayerResult:
        """
        Generate the network map layers.

        Args:
            selected_period: Selected representative period.
            selected_time: Selected time step index (1-based).
            zoom_level: Current map zoom level.
            pq_mode: Power mode ("vLineP" or "vLineQ").

        Returns:
            Tuple of (network_layer, node_layer).
        """
        # Convert time step index to actual value
        selected_time_value = self._data.k["values"].iloc[selected_time - 1]

        # Filter data for the selected time step
        vline_data = self._get_line_data(pq_mode)
        vlinep_filtered = self._filter_by_time(vline_data, selected_period, selected_time_value)
        vgenp_filtered = self._filter_by_time(self._data.vGenP, selected_period, selected_time_value)
        vsocp_filtered = self._get_voltage_data(selected_period, selected_time_value)

        # Generate network layer (lines with arrows)
        network_layer = self._generate_network_layer(
            vlinep_filtered,
            zoom_level
        )

        # Generate node layer (pie charts)
        node_layer = self._generate_node_layer(
            vgenp_filtered,
            vsocp_filtered
        )

        return network_layer, node_layer

    def _get_line_data(self, pq_mode: str) -> pd.DataFrame:
        """Get the appropriate line data based on mode."""
        if pq_mode == "vLineQ" and hasattr(self._data, "vLineQ") and self._data.vLineQ is not None:
            return self._data.vLineQ
        return self._data.vLineP

    def _filter_by_time(
            self,
            df: pd.DataFrame,
            period: str,
            time_value: Any
    ) -> pd.DataFrame:
        """Filter DataFrame by period and time."""
        if df is None or df.empty:
            return pd.DataFrame()

        if self._data.long_format:
            return df[df["k"] == time_value]
        else:
            return df[(df["rp"] == period) & (df["k"] == time_value)]

    def _get_voltage_data(
            self,
            period: str,
            time_value: Any
    ) -> pd.DataFrame:
        """Get voltage data for the selected time."""
        if not hasattr(self._data, "vSOCP_cii") or self._data.vSOCP_cii is None:
            return pd.DataFrame(columns=["i", "values"])

        df = self._filter_by_time(self._data.vSOCP_cii, period, time_value)
        return df[["i", "values"]] if not df.empty else pd.DataFrame(columns=["i", "values"])

    def _generate_network_layer(
            self,
            vlinep_filtered: pd.DataFrame,
            zoom_level: int
    ) -> dl.LayerGroup:
        """Generate the network layer with lines and arrows."""
        line_weight = self._map_options.get("line_weight", 2)
        arrow_scale = self._map_options.get("arrow_zoom_scale", 0.5)
        arrow_min = self._map_options.get("arrow_min_size", 0.5)
        default_zoom = self._map_options.get("default_zoom", 5)

        # Calculate arrow size
        zoom = zoom_level or default_zoom
        arrow_size = max(arrow_min, int(zoom * arrow_scale))

        network_elements = []

        for idx, row in vlinep_filtered.iterrows():
            i, j = row["i"], row["j"]
            flow = row["values"]
            rel_val = row.get("rel_values", abs(flow) / max(abs(flow), 1))
            line_id = row["line"]
            pPmax = row.get("pPmax", 0)

            # Determine positions based on flow direction
            if flow < 0:
                positions = [
                    (self._data.i.loc[j, 'lat'], self._data.i.loc[j, 'lon']),
                    (self._data.i.loc[i, 'lat'], self._data.i.loc[i, 'lon'])
                ]
            else:
                positions = [
                    (self._data.i.loc[i, 'lat'], self._data.i.loc[i, 'lon']),
                    (self._data.i.loc[j, 'lat'], self._data.i.loc[j, 'lon'])
                ]

            # Get color from colormap
            color = self._get_flow_color(rel_val)

            # Create polyline for arrow base
            polyline_base = dl.Polyline(
                positions=positions,
                color="black",
                weight=line_weight,
                opacity=0,
                id=f"line_base-{line_id}",
                n_clicks=0
            )

            # Create polyline for the visible line
            polyline_line = dl.Polyline(
                positions=positions,
                color=color,
                weight=line_weight,
                id=str(line_id),
                children=[
                    dl.Popup(f"Power Flow: {abs(flow):.5f} MW, Line rating: {pPmax:.5f} MW")
                ],
                n_clicks=0
            )

            # Create arrow decorator
            polyline_decorator = dl.PolylineDecorator(
                patterns=[dict(
                    offset='50%',
                    repeat='25%',
                    arrowHead=dict(
                        pixelSize=arrow_size,
                        polygon=False,
                        pathOptions=dict(stroke=True, color=color)
                    )
                )],
                children=[polyline_base],
                n_clicks=0
            )

            network_elements.extend([polyline_decorator, polyline_line])

        return dl.LayerGroup(
            children=network_elements,
            id=f"network-layer-{uuid.uuid4()}",
            n_clicks=0
        )

    @staticmethod
    def _get_flow_color(rel_val: float) -> str:
        """Get color for flow value using RdYlGn colormap."""
        rel_val = min(max(rel_val, 0), 1)  # Clamp to [0, 1]
        color_rgb = plt.get_cmap('RdYlGn_r')(rel_val)[:3]
        return "#{:02x}{:02x}{:02x}".format(
            int(color_rgb[0] * 255),
            int(color_rgb[1] * 255),
            int(color_rgb[2] * 255)
        )

    def _generate_node_layer(
            self,
            vgenp_filtered: pd.DataFrame,
            vsocp_filtered: pd.DataFrame
    ) -> dl.GeoJSON:
        """Generate the node layer with pie charts."""
        buses = self._data.i
        gi = self._data.gi

        # Merge generation data with generator info
        merged = pd.merge(vgenp_filtered, gi, on="g", how="left")
        grouped = merged.groupby(["i", "tec"])["values"].sum().reset_index()
        pivoted = grouped.pivot(index="i", columns="tec", values="values").fillna(0)
        pivoted.reset_index(inplace=True)

        # Merge with bus info
        pivoted = pivoted.merge(buses.reset_index(), left_on="i", right_on="values", how="left")

        # Handle missing buses
        pivoted = self._add_missing_buses(pivoted, buses)

        # Add voltage data
        if not vsocp_filtered.empty:
            pivoted = pivoted.merge(
                vsocp_filtered.rename(columns={"values": "voltage_level"}),
                on="i",
                how="left"
            )
        else:
            pivoted["voltage_level"] = pd.NA

        # Prepare GeoJSON data
        geo_data = self._prepare_geo_data(pivoted, buses)

        geojson = dlx.dicts_to_geojson(geo_data)
        geobuf = dlx.geojson_to_geobuf(geojson)

        return dl.GeoJSON(
            id="node-layer",
            data=geobuf,
            format='geobuf',
            cluster=True,
            zoomToBoundsOnClick=True,
            superClusterOptions=dict(
                radius=self._cluster_options.get("cluster_radius", 60),
                maxZoom=self._cluster_options.get("maxZoom", 16)
            ),
            pointToLayer=self._data.js_generator.pointToLayer(),
            clusterToLayer=self._data.js_generator.clusterToLayer(),
        )

    def _add_missing_buses(
            self,
            pivoted: pd.DataFrame,
            buses: pd.DataFrame
    ) -> pd.DataFrame:
        """Add missing buses to the pivoted DataFrame."""
        missing_buses = set(buses.index) - set(pivoted["i"])

        if not missing_buses:
            return pivoted

        new_rows = []
        for bus in missing_buses:
            new_row = {
                "i": bus,
                "lat": buses.loc[bus, "lat"],
                "lon": buses.loc[bus, "lon"],
                "pBusMaxV": buses.loc[bus, "pBusMaxV"] if "pBusMaxV" in buses.columns else pd.NA,
                "pBusMinV": buses.loc[bus, "pBusMinV"] if "pBusMinV" in buses.columns else pd.NA
            }
            new_rows.append(new_row)

        return pd.concat([pivoted, pd.DataFrame(new_rows)], ignore_index=True)

    def _prepare_geo_data(
            self,
            pivoted: pd.DataFrame,
            buses: pd.DataFrame
    ) -> list[dict]:
        """Prepare GeoJSON data from pivoted DataFrame."""
        # Ensure default colors
        tech_colors = self._technology_colors.copy()
        tech_colors.setdefault("unknown", "#808080")
        tech_colors.setdefault("no_generation", "#000000")

        skip_cols = {"i", "lat", "lon", "values", "voltage_level", "pBusMaxV", "pBusMinV"}

        geo_data = []

        for _, row in pivoted.iterrows():
            if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
                continue

            values = []
            colors = []
            labels = []

            for col, val in row.items():
                if col in skip_cols or pd.isna(val) or val <= 0:
                    continue

                color = tech_colors.get(col, tech_colors["unknown"])
                label = col

                # Mark storage discharge
                if col in ["BESS"]:
                    label = f"{col} Discharge"

                values.append(val)
                colors.append(color)
                labels.append(label)

            # Handle no generation case
            if not values:
                values = [0]
                colors = [tech_colors["no_generation"]]
                labels = ["No Generation"]

            geo_data.append({
                "id": row["i"],
                "lat": row["lat"],
                "lon": row["lon"],
                "name": row["i"],
                "values": values,
                "colors": colors,
                "labels": labels,
                "voltage": f"{row.get('voltage_level', 0):.3f} p.u." if pd.notna(row.get('voltage_level')) else "N/A",
                "voltage_max": row.get("pBusMaxV", "N/A"),
                "voltage_min": row.get("pBusMinV", "N/A")
            })

        return geo_data


# =============================================================================
# Dynamic Plot Generation
# =============================================================================

class DynamicPlotGenerator:
    """Generates dynamic plots based on user selections."""

    def __init__(self, data_source: Any):
        """
        Initialize the generator.

        Args:
            data_source: Object containing the data (e.g., LEGO_GPT instance).
        """
        self._data = data_source
        self._graph_options = data_source.graph_options

    def generate(
            self,
            x_axis: str,
            y_axis: str,
            line_idx: str,
            node_idx: str,
            selected_period: str,
            scope: str,
            time_range: list[int]
    ) -> PlotResult:
        """
        Generate a dynamic plot.

        Args:
            x_axis: X-axis variable.
            y_axis: Y-axis variable.
            line_idx: Selected line index.
            node_idx: Selected node index.
            selected_period: Selected representative period.
            scope: "Global" or "Local".
            time_range: Time range [start, end].

        Returns:
            HTML Div containing the plot.
        """
        print(
            f"Generating plot: x={x_axis}, y={y_axis}, period={selected_period}, "
            f"range={time_range}, node={node_idx}, line={line_idx}, scope={scope}"
        )

        # Generate the plot figure
        fig = generate_plot(
            data_source=self._data,
            x_axis=x_axis,
            y_axis=y_axis,
            line_idx=line_idx,
            node_idx=node_idx,
            selected_period=selected_period,
            scope=scope,
            time_range=time_range
        )

        # Handle case where no valid plot could be created
        if fig is None:
            fig = px.scatter(title="Select a valid combination for the plot")

        # Apply layout options
        fig.update_layout(**self._graph_options.get("layout", {}))

        return html.Div(
            children=[
                dcc.Graph(
                    figure=fig,
                    id="dynamic-plot",
                    style={'height': '100%', 'width': '100%'},
                    config=self._graph_options.get("graph_save_options", {})
                )
            ],
            style={
                'flex': '1',
                'minWidth': '0',
                'height': '90vh',
                'marginTop': '0px'
            }
        )


# =============================================================================
# Public API (Backward Compatibility)
# =============================================================================

def generate_network_map(
        self: Any,
        selected_period: str,
        selected_time: int,
        zoom_level: int,
        pq_mode: str = "vLineP"
) -> MapLayerResult:
    """
    Generate the network map visualization.

    This function provides backward compatibility with the existing API.

    Args:
        self: Data source object (e.g., LEGO_GPT instance).
        selected_period: Selected representative period.
        selected_time: Selected time step index.
        zoom_level: Current map zoom level.
        pq_mode: Power mode ("vLineP" or "vLineQ").

    Returns:
        Tuple of (network_layer, node_layer).
    """
    generator = NetworkMapGenerator(self)
    return generator.generate(selected_period, selected_time, zoom_level, pq_mode)


def generate_dynamic_plot(
        self: Any,
        x_axis: str,
        y_axis: str,
        line_idx: str,
        node_idx: str,
        selected_period: str,
        scope: str,
        time_range: list[int]
) -> PlotResult:
    """
    Generate a dynamic plot.

    This function provides backward compatibility with the existing API.

    Args:
        self: Data source object (e.g., LEGO_GPT instance).
        x_axis: X-axis variable.
        y_axis: Y-axis variable.
        line_idx: Selected line index.
        node_idx: Selected node index.
        selected_period: Selected representative period.
        scope: "Global" or "Local".
        time_range: Time range [start, end].

    Returns:
        HTML Div containing the plot.
    """
    generator = DynamicPlotGenerator(self)
    return generator.generate(
        x_axis=x_axis,
        y_axis=y_axis,
        line_idx=line_idx,
        node_idx=node_idx,
        selected_period=selected_period,
        scope=scope,
        time_range=time_range
    )


# Legacy function - kept for compatibility
def generate_node_layer(
        buses: pd.DataFrame,
        gi: pd.DataFrame,
        vGenP_filtered: pd.DataFrame,
        vSOCP_cii_filtered: pd.DataFrame,
        js_generator: Any,
        technology_colors: dict,
        cluster_options: dict
) -> dl.GeoJSON:
    """
    Generate node layer with pie charts.

    This is a legacy wrapper - prefer using NetworkMapGenerator directly.
    """

    # Create a minimal data source for the generator
    class MinimalDataSource:
        def __init__(self):
            self.i = buses
            self.gi = gi
            self.vGenP = vGenP_filtered
            self.vSOCP_cii = vSOCP_cii_filtered
            self.js_generator = js_generator
            self.map_options = {
                "technology_colors": technology_colors,
                "cluster_options": cluster_options
            }

    data_source = MinimalDataSource()
    generator = NetworkMapGenerator(data_source)

    return generator._generate_node_layer(vGenP_filtered, vSOCP_cii_filtered)
