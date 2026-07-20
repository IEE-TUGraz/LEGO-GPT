"""
UI Handler Module for LEGO-GPT

This module provides functions for generating network map visualizations
and dynamic plots. It handles the rendering logic for the main UI components.
"""

import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash_extensions.javascript import assign
import matplotlib
matplotlib.use("Agg")  # Headless backend - figures are only rendered to buffers/colormaps, never shown.
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from map_export import render_network_figure
from plot_definitions import generate_plot

# =============================================================================
# Type Definitions
# =============================================================================

MapLayerResult = tuple[dl.LayerGroup, dl.GeoJSON]


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
            pq_mode: str = "vLineP",
            show_voltage: bool = True
    ) -> MapLayerResult:
        """
        Generate the network map layers.

        Args:
            selected_period: Selected representative period.
            selected_time: Selected time step index (1-based).
            zoom_level: Current map zoom level.
            pq_mode: Power mode ("vLineP" or "vLineQ").
            show_voltage: Whether node labels include the voltage line, or just the name.

        Returns:
            Tuple of (network_layer, node_layer).
        """
        vlinep_filtered, vgenp_filtered, vsocp_filtered, vDchEV_filtered, _ = self._get_filtered_data(
            selected_period, selected_time, pq_mode
        )

        # Generate network layer (lines with arrows)
        network_layer = self._generate_network_layer(
            vlinep_filtered,
            zoom_level
        )

        # Generate node layer (pie charts)
        node_layer = self._generate_node_layer(
            vgenp_filtered,
            vsocp_filtered,
            vDchEV_filtered,
            show_voltage
        )

        return network_layer, node_layer

    def get_export_data(
            self,
            selected_period: str,
            selected_time: int,
            pq_mode: str = "vLineP"
    ) -> dict[str, Any]:
        """
        Get a plain-data (non-Leaflet) representation of the network for static export.

        Reuses the same filtering/aggregation pipeline as `generate()` so the exported
        figure always matches what's shown on the live map.

        Args:
            selected_period: Selected representative period.
            selected_time: Selected time step index (1-based).
            pq_mode: Power mode ("vLineP" or "vLineQ").

        Returns:
            Dict with "lines" (list of line records) and "nodes" (list of geo point
            dicts), plus styling metadata needed to render them.
        """
        vlinep_filtered, vgenp_filtered, vsocp_filtered, vDchEV_filtered, selected_time_value = (
            self._get_filtered_data(selected_period, selected_time, pq_mode)
        )

        line_records = self._build_line_records(vlinep_filtered)
        geo_data = self._build_node_geo_data(vgenp_filtered, vsocp_filtered, vDchEV_filtered)

        js_generator = self._data.js_generator
        return {
            "lines": line_records,
            "nodes": geo_data,
            "line_weight": self._map_options.get("line_weight", 2),
            "pie_radius": {
                "min": js_generator.min_radius,
                "max": js_generator.max_radius,
                "scale_factor": js_generator.scale_factor,
            },
            "selected_period": selected_period,
            "selected_time_value": selected_time_value,
            "pq_mode": pq_mode,
        }

    def _get_filtered_data(
            self,
            selected_period: str,
            selected_time: int,
            pq_mode: str
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Any]:
        """Filter all source dataframes for the selected period/time/mode."""
        # Convert time step index to actual value
        selected_time_value = self._data.k["values"].iloc[selected_time - 1]

        vline_data = self._get_line_data(pq_mode)
        vlinep_filtered = self._filter_by_time(vline_data, selected_period, selected_time_value)
        vgenp_filtered = self._filter_by_time(self._data.vGenP, selected_period, selected_time_value)
        vsocp_filtered = self._get_voltage_data(selected_period, selected_time_value)

        # Filter EV discharge data (V2G)
        vDchEV = getattr(self._data, 'vDchEV', None)
        vDchEV_filtered = self._filter_by_time(vDchEV, selected_period, selected_time_value) if vDchEV is not None else pd.DataFrame()

        return vlinep_filtered, vgenp_filtered, vsocp_filtered, vDchEV_filtered, selected_time_value

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
        if not hasattr(self._data, "vSOCP") or self._data.vSOCP is None:
            return pd.DataFrame(columns=["i", "values"])

        df = self._filter_by_time(self._data.vSOCP, period, time_value)
        return df[["i", "values"]] if not df.empty else pd.DataFrame(columns=["i", "values"])

    def _generate_network_layer(
            self,
            vlinep_filtered: pd.DataFrame,
            zoom_level: int
    ) -> dl.LayerGroup:
        """Generate the network layer with lines and arrows."""
        line_weight = self._map_options.get("line_weight", 2)
        arrow_size = self._compute_arrow_size(zoom_level)
        line_records = self._build_line_records(vlinep_filtered)

        network_elements = []
        click_features = []

        for rec in line_records:
            positions = rec["positions"]
            line_id = rec["line_id"]
            color = rec["color"]

            click_features.append({
                "type": "Feature",
                "properties": {
                    "line": str(line_id),
                    "id": str(line_id),
                    "popup": f"Power Flow: {abs(rec['flow']):.5f} MW, Line rating: {rec['pPmax']:.5f} MW",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon, lat] for lat, lon in positions],
                },
            })

            # Create polyline for arrow base
            polyline_base = dl.Polyline(
                positions=positions,
                color="black",
                weight=line_weight,
                opacity=0,
                id=f"line_base-{line_id}",
                interactive=False
            )

            # Create polyline for the visible line
            polyline_line = dl.Polyline(
                positions=positions,
                color=color,
                weight=line_weight,
                id=str(line_id)
            )

            # Create arrow decorator
            polyline_decorator = dl.PolylineDecorator(
                patterns=[dict(
                    offset='50%',
                    repeat='25%',
                    arrowHead=dict(
                        pixelSize=arrow_size,
                        polygon=False,
                        pathOptions=dict(stroke=True, color=color, interactive=False)
                    )
                )],
                children=[polyline_base],
            )

            network_elements.extend([polyline_decorator, polyline_line])

        network_elements.append(
            dl.GeoJSON(
                id="line-click-layer",
                data={
                    "type": "FeatureCollection",
                    "features": click_features,
                },
                style={
                    "color": "#000000",
                    "weight": max(line_weight + 8, 10),
                    "opacity": 0.0,
                },
                onEachFeature=assign(
                    "function(feature, layer) { layer.bindPopup(feature.properties.popup); }"
                ),
                interactive=True,
            )
        )

        return dl.LayerGroup(
            children=network_elements,
            id=f"network-layer-{uuid.uuid4()}",
            n_clicks=0
        )

    def _compute_arrow_size(self, zoom_level: int) -> int:
        """Compute the arrow decorator pixel size for the current zoom level."""
        arrow_scale = self._map_options.get("arrow_zoom_scale", 0.5)
        arrow_min = self._map_options.get("arrow_min_size", 0.5)
        default_zoom = self._map_options.get("default_zoom", 5)
        zoom = zoom_level or default_zoom
        return max(arrow_min, int(zoom * arrow_scale))

    def _build_line_records(self, vlinep_filtered: pd.DataFrame) -> list[dict]:
        """Build plain-data records (positions, flow, color) for each line."""
        records = []

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

            records.append({
                "line_id": line_id,
                "positions": positions,
                "flow": flow,
                "rel_val": rel_val,
                "pPmax": pPmax,
                "color": self._get_flow_color(rel_val),
            })

        return records

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
            vsocp_filtered: pd.DataFrame,
            vDchEV_filtered: pd.DataFrame = None,
            show_voltage: bool = True
    ) -> dl.GeoJSON:
        """Generate the node layer with pie charts."""
        geo_data = self._build_node_geo_data(vgenp_filtered, vsocp_filtered, vDchEV_filtered, show_voltage)

        print(f"  [Node Layer] Generated {len(geo_data)} geo points")

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

    def _build_node_geo_data(
            self,
            vgenp_filtered: pd.DataFrame,
            vsocp_filtered: pd.DataFrame,
            vDchEV_filtered: pd.DataFrame = None,
            show_voltage: bool = True
    ) -> list[dict]:
        """Build plain-data geo points (pie values/colors per node) for the node layer."""
        buses = self._data.i
        gi = getattr(self._data, 'gi', pd.DataFrame())

        # Handle case where there's no generation data OR no gi mapping
        if vgenp_filtered.empty or gi.empty:
            print("  [Node Layer] No generation data or gi mapping - showing all buses with 'No Generation'")
            # Create empty pivoted dataframe with all buses
            pivoted = pd.DataFrame({'i': buses.index.tolist()})
            pivoted = pivoted.merge(
                buses.reset_index(),
                left_on="i",
                right_on="values",
                how="left"
            )
        else:
            # Merge generation data with generator info
            merged = pd.merge(vgenp_filtered, gi, on="g", how="left")

            # Drop rows where merge failed (generators not in gi)
            merged = merged.dropna(subset=['i', 'tec'])

            if merged.empty:
                print("  [Node Layer] Merge resulted in empty data - showing all buses")
                pivoted = pd.DataFrame({'i': buses.index.tolist()})
                pivoted = pivoted.merge(
                    buses.reset_index(),
                    left_on="i",
                    right_on="values",
                    how="left"
                )
            else:
                grouped = merged.groupby(["i", "tec"])["values"].sum().reset_index()

                # Handle empty grouped data
                if grouped.empty:
                    print("  [Node Layer] Grouping resulted in empty data")
                    pivoted = pd.DataFrame({'i': buses.index.tolist()})
                    pivoted = pivoted.merge(
                        buses.reset_index(),
                        left_on="i",
                        right_on="values",
                        how="left"
                    )
                else:
                    pivoted = grouped.pivot(index="i", columns="tec", values="values").fillna(0)
                    pivoted.reset_index(inplace=True)

                    # Merge with bus info
                    pivoted = pivoted.merge(
                        buses.reset_index(),
                        left_on="i",
                        right_on="values",
                        how="left"
                    )

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

        # Add EV discharge data (V2G) - aggregate by node
        if vDchEV_filtered is not None and not vDchEV_filtered.empty and 'i' in vDchEV_filtered.columns:
            # Filter out rows where i is NaN
            vDchEV_with_node = vDchEV_filtered.dropna(subset=['i'])
            if not vDchEV_with_node.empty:
                ev_discharge_by_node = vDchEV_with_node.groupby("i")["values"].sum().reset_index()
                ev_discharge_by_node = ev_discharge_by_node.rename(columns={"values": "V2G_discharging"})
                pivoted = pivoted.merge(ev_discharge_by_node, on="i", how="left")
                pivoted["V2G_discharging"] = pivoted["V2G_discharging"].fillna(0)
                print(f"  [Node Layer] Added EV discharge data for {len(ev_discharge_by_node)} nodes")

        # Prepare GeoJSON data
        return self._prepare_geo_data(pivoted, show_voltage)

    @staticmethod
    def _add_missing_buses(
            pivoted: pd.DataFrame,
            buses: pd.DataFrame) -> pd.DataFrame:
        """Add missing buses to the pivoted DataFrame."""
        missing_buses = set(buses.index) - set(pivoted["i"])

        if not missing_buses:
            return pivoted

        new_rows = []
        for bus in missing_buses:
            new_row = {
                "i": bus,
                "lat": buses.loc[bus, "lat"] if "lat" in buses.columns else pd.NA,
                "lon": buses.loc[bus, "lon"] if "lon" in buses.columns else pd.NA,
                "pBusMaxV": buses.loc[bus, "pBusMaxV"] if "pBusMaxV" in buses.columns else pd.NA,
                "pBusMinV": buses.loc[bus, "pBusMinV"] if "pBusMinV" in buses.columns else pd.NA
            }
            new_rows.append(new_row)

        if new_rows:
            print(f"  [Node Layer] Adding {len(new_rows)} missing buses")

        return pd.concat([pivoted, pd.DataFrame(new_rows)], ignore_index=True)

    def _prepare_geo_data(
            self,
            pivoted: pd.DataFrame,
            show_voltage: bool = True) -> list[dict]:
        """Prepare GeoJSON data from pivoted DataFrame."""
        # Ensure default colors
        tech_colors = self._technology_colors.copy()
        tech_colors.setdefault("unknown", "#808080")
        tech_colors.setdefault("no_generation", "#000000")

        skip_cols = {"i", "lat", "lon", "values", "voltage_level", "pBusMaxV", "pBusMinV"}

        geo_data = []
        skipped_count = 0

        for idx, row in pivoted.iterrows():
            # Debug logging for first few rows
            if idx < 3:
                print(f"  [GeoData] Row {idx}: i={row.get('i')}, lat={row.get('lat')}, lon={row.get('lon')}")

            if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
                skipped_count += 1
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
                elif col == "V2G_discharging":
                    label = "EV Discharge"

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
                "voltage_min": row.get("pBusMinV", "N/A"),
                "show_voltage": show_voltage
            })

        if skipped_count > 0:
            print(f"  [GeoData] WARNING: Skipped {skipped_count} rows due to missing lat/lon")

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
            time_range: list[int],
            y_range: list[float] = None,
            x_range: list[float] = None
    ) -> go.Figure:
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
            y_range: Fixed [min, max] for the Y-axis, or None to autoscale.
            x_range: Fixed [min, max] for the X-axis, or None to autoscale.

        Returns:
            Plotly Figure object.
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

        # Apply fixed axis ranges (overrides autoscaling), for comparing plots across scenarios
        if y_range:
            fig.update_yaxes(range=y_range)
        if x_range:
            fig.update_xaxes(range=x_range)

        return fig


# =============================================================================
# Public API (Backward Compatibility)
# =============================================================================

def generate_network_map(
        self: Any,
        selected_period: str,
        selected_time: int,
        zoom_level: int,
        pq_mode: str = "vLineP",
        show_voltage: bool = True
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
        show_voltage: Whether node labels include the voltage line, or just the name.

    Returns:
        Tuple of (network_layer, node_layer).
    """
    generator = NetworkMapGenerator(self)
    return generator.generate(selected_period, selected_time, zoom_level, pq_mode, show_voltage)


def generate_map_export(
        self: Any,
        selected_period: str,
        selected_time: int,
        pq_mode: str = "vLineP",
        fmt: str = "svg"
) -> bytes:
    """
    Render the network map as a standalone vector figure for export.

    Unlike the live map, this bypasses dash-leaflet entirely and renders the
    same filtered line/node data with matplotlib, producing a true vector
    file (no raster basemap tiles).

    Args:
        self: Data source object (e.g., LEGO_GPT instance).
        selected_period: Selected representative period.
        selected_time: Selected time step index.
        pq_mode: Power mode ("vLineP" or "vLineQ").
        fmt: Output format - "svg", "pdf", or "png".

    Returns:
        Raw bytes of the rendered figure.
    """
    generator = NetworkMapGenerator(self)
    export_data = generator.get_export_data(selected_period, selected_time, pq_mode)
    return render_network_figure(export_data, fmt=fmt)


def export_plot_image(
        figure: dict,
        fmt: str = "svg",
        toimage_options: dict = None
) -> bytes:
    """
    Render an already-built Plotly figure to a static image file via Kaleido.

    Unlike the modebar's built-in download button (browser-only, no PDF support),
    this uses Kaleido so PDF export is possible. Takes the figure dict exactly as
    currently displayed (including any fixed axis ranges), so the export matches
    what's on screen.

    Runs Kaleido in a short-lived subprocess rather than in-process: calling it
    directly from within the running Dash server was observed to be far slower
    (tens of seconds vs. a consistent ~2s standalone) and prone to timing out
    the browser's callback fetch, likely an asyncio/subprocess interaction with
    the dev server's own event loop.

    Args:
        figure: Plotly figure dict, as read from the dcc.Graph's "figure" prop.
        fmt: Output format - "svg", "pdf", or "png".
        toimage_options: Optional dict with "width"/"height"/"scale", reused from
            the same config used for the modebar's download button.

    Returns:
        Raw bytes of the rendered image.

    Raises:
        RuntimeError: If the export subprocess fails.
    """
    kwargs = {}
    toimage_options = toimage_options or {}
    for key in ("width", "height", "scale"):
        if toimage_options.get(key) is not None:
            kwargs[key] = toimage_options[key]

    worker_script = str(Path(__file__).parent / "_kaleido_worker.py")

    with tempfile.TemporaryDirectory() as tmp_dir:
        figure_path = os.path.join(tmp_dir, "figure.json")
        output_path = os.path.join(tmp_dir, f"plot.{fmt}")

        with open(figure_path, "w", encoding="utf-8") as f:
            json.dump(figure, f)

        result = subprocess.run(
            [sys.executable, worker_script, figure_path, output_path, fmt, json.dumps(kwargs)],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Plot export failed: {result.stderr.decode('utf-8', errors='replace')}")

        with open(output_path, "rb") as f:
            return f.read()


def generate_dynamic_plot(
        self: Any,
        x_axis: str,
        y_axis: str,
        line_idx: str,
        node_idx: str,
        selected_period: str,
        scope: str,
        time_range: list[int],
        y_range: list[float] = None,
        x_range: list[float] = None
) -> go.Figure:
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
        y_range: Fixed [min, max] for the Y-axis, or None to autoscale.
        x_range: Fixed [min, max] for the X-axis, or None to autoscale.

    Returns:
        Plotly Figure object.
    """
    generator = DynamicPlotGenerator(self)
    return generator.generate(
        x_axis=x_axis,
        y_axis=y_axis,
        line_idx=line_idx,
        node_idx=node_idx,
        selected_period=selected_period,
        scope=scope,
        time_range=time_range,
        y_range=y_range,
        x_range=x_range
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
