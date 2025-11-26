"""
Plot Definitions Module for LEGO-GPT

This module provides plot generation functionality for the LEGO-GPT application.
It defines various plot types and handles data filtering for visualization.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol, Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# =============================================================================
# Type Definitions
# =============================================================================

class PlotType(Enum):
    """Supported plot types."""
    AREA = "area"
    LINE = "line"
    BAR = "bar"
    HISTOGRAM = "histogram"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class DataSourceProtocol(Protocol):
    """Protocol defining required data attributes for plot generation."""

    @property
    def vGenP(self) -> pd.DataFrame: ...

    @property
    def vLineP(self) -> pd.DataFrame: ...

    @property
    def vStIntraRes(self) -> Optional[pd.DataFrame]: ...

    @property
    def pDemandP(self) -> Optional[pd.DataFrame]: ...

    @property
    def gi(self) -> pd.DataFrame: ...

    @property
    def k(self) -> pd.DataFrame: ...

    @property
    def long_format(self) -> bool: ...

    @property
    def graph_options(self) -> dict: ...


@dataclass
class PlotConfig:
    """Configuration for a single plot."""
    x_column: str
    y_column: str
    color_column: Optional[str] = None
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    plot_type: PlotType = PlotType.LINE
    hover_data: Optional[dict] = None


# =============================================================================
# Plot Registry
# =============================================================================

# Maps (x_axis, y_axis) combinations to plot configurations
PLOT_REGISTRY: dict[tuple[str, str], dict] = {
    ("time", "dispatch"): {
        "data_source": "vGenP",
        "plot_type": PlotType.AREA,
        "x_col": "k",
        "y_col": "values",
        "color_col": "g",
        "title_global": "Global Dispatch Over Time",
        "title_local": "Local Dispatch for {node} Over Time",
        "x_label": "Time",
        "y_label": "Dispatch [MW]",
        "legend_title": "Generator",
    },
    ("time", "demand"): {
        "data_source": "pDemandP",
        "plot_type": PlotType.LINE,
        "x_col": "k",
        "y_col": "values",
        "color_col": None,
        "title_global": "Global Demand Over Time",
        "title_local": "Local Demand for {node} Over Time",
        "x_label": "Time",
        "y_label": "Demand [MW]",
        "legend_title": None,
    },
    ("time", "power_flow"): {
        "data_source": "vLineP",
        "plot_type": PlotType.LINE,
        "x_col": "k",
        "y_col": "values",
        "color_col": "line",
        "title_global": "Power Flow Over Time",
        "title_local": "Power Flow for Line {line} Over Time",
        "x_label": "Time",
        "y_label": "Power Flow [MW]",
        "legend_title": "Line",
        "hover_data": {"values": True, "line": True, "i": True, "j": True},
    },
    ("time", "soc"): {
        "data_source": "vStIntraRes",
        "plot_type": PlotType.LINE,
        "x_col": "k",
        "y_col": "values",
        "color_col": "i",
        "title_global": "State of Charge Over Time",
        "title_local": "State of Charge for {node} Over Time",
        "x_label": "Time",
        "y_label": "State of Charge",
        "legend_title": "Storage Unit",
        "hover_data": {"values": True, "i": True},
    },
    ("generator", "dispatch"): {
        "data_source": "vGenP",
        "plot_type": PlotType.BAR,
        "x_col": "g",
        "y_col": "values",
        "color_col": "g",
        "title_global": "Total Dispatch per Generator",
        "title_local": "Total Dispatch for {node}",
        "x_label": "Generator",
        "y_label": "Dispatch [MW]",
        "legend_title": "Generator",
        "aggregation": "sum",
    },
    ("line", "power_flow"): {
        "data_source": "vLineP",
        "plot_type": PlotType.HISTOGRAM,
        "x_col": "values",
        "y_col": None,
        "color_col": "line",
        "title_global": "Power Flow Distribution",
        "title_local": "Power Flow Distribution for Line {line}",
        "x_label": "Power Flow [MW]",
        "y_label": "Count",
        "legend_title": "Line",
        "nbins": 20,
    },
}


# =============================================================================
# Data Filtering
# =============================================================================

class DataFilter:
    """Handles filtering of data for plot generation."""

    def __init__(self, data_source: Any):
        """
        Initialize the DataFilter.

        Args:
            data_source: Object containing the data (e.g., LEGO_GPT instance).
        """
        self._data = data_source

    def filter(
            self,
            data_attr: str,
            rp: Optional[str] = None,
            scope: str = "Global",
            local_node: Optional[str] = None,
            local_line: Optional[str] = None,
            k_range: Optional[list] = None
    ) -> Optional[pd.DataFrame]:
        """
        Filter a DataFrame based on provided criteria.

        Args:
            data_attr: Name of the data attribute to filter.
            rp: Representative period to filter by.
            scope: "Global" or "Local" scope.
            local_node: Node ID for local filtering.
            local_line: Line ID for local filtering.
            k_range: List of time steps to include.

        Returns:
            Filtered DataFrame or None if data doesn't exist.
        """
        df = getattr(self._data, data_attr, None)
        if df is None or df.empty:
            return None

        df = df.copy()

        # Filter by representative period if not long format
        if not self._data.long_format and rp is not None and "rp" in df.columns:
            df = df[df["rp"] == rp]

        # Filter by time range
        if k_range and "k" in df.columns:
            df = df[df["k"].isin(k_range)]

        # Apply scope-specific filtering
        df = self._apply_scope_filter(df, data_attr, scope, local_node, local_line)

        return df

    def _apply_scope_filter(
            self,
            df: pd.DataFrame,
            data_attr: str,
            scope: str,
            local_node: Optional[str],
            local_line: Optional[str]
    ) -> pd.DataFrame:
        """Apply scope-specific filtering based on data type."""

        if scope == "Global":
            # For demand, aggregate globally
            if data_attr == "pDemandP" and "k" in df.columns:
                df = df.groupby("k", as_index=False)["values"].sum()
            return df

        # Local scope filtering
        if data_attr == "vGenP" and local_node:
            gi = getattr(self._data, "gi", pd.DataFrame())
            if not gi.empty:
                local_generators = gi[gi["i"] == local_node]["g"].tolist()
                df = df[df["g"].isin(local_generators)]

        elif data_attr == "pDemandP" and local_node:
            if "i" in df.columns:
                df = df[df["i"] == local_node]

        elif data_attr == "vLineP" and local_line:
            if "line" in df.columns:
                df = df[df["line"] == local_line]

        elif data_attr == "vStIntraRes" and local_node:
            if "i" in df.columns:
                df = df[df["i"] == local_node]

        return df


# =============================================================================
# Plot Generator
# =============================================================================

class PlotGenerator:
    """Generates plots based on configuration and data."""

    def __init__(self, data_source: Any):
        """
        Initialize the PlotGenerator.

        Args:
            data_source: Object containing the data and graph options.
        """
        self._data = data_source
        self._filter = DataFilter(data_source)
        self._colors = data_source.graph_options.get("colors", px.colors.qualitative.Plotly)

    def generate(
            self,
            x_axis: str,
            y_axis: str,
            scope: str = "Global",
            node_idx: Optional[str] = None,
            line_idx: Optional[str] = None,
            selected_period: Optional[str] = None,
            time_range: Optional[list[int]] = None
    ) -> Optional[go.Figure]:
        """
        Generate a plot based on the specified configuration.

        Args:
            x_axis: X-axis variable selection.
            y_axis: Y-axis variable selection.
            scope: "Global" or "Local" scope.
            node_idx: Node identifier for local plots.
            line_idx: Line identifier for local plots.
            selected_period: Selected representative period.
            time_range: Time range [start, end] for filtering.

        Returns:
            Plotly Figure object or None if invalid configuration.
        """
        # Look up plot configuration
        config = PLOT_REGISTRY.get((x_axis, y_axis))
        if config is None:
            return self._create_placeholder_plot(
                f"No plot defined for X: {x_axis}, Y: {y_axis}"
            )

        # Compute time range
        k_range = self._compute_k_range(time_range)

        # Filter data
        df = self._filter.filter(
            data_attr=config["data_source"],
            rp=selected_period,
            scope=scope,
            local_node=node_idx,
            local_line=line_idx,
            k_range=k_range
        )

        if df is None or df.empty:
            return self._create_placeholder_plot("No data available for selection")

        # Generate title
        title = self._format_title(config, scope, node_idx, line_idx)

        # Create the plot
        return self._create_plot(df, config, title)

    def _compute_k_range(self, time_range: Optional[list[int]]) -> Optional[list]:
        """Compute the list of time steps from the range."""
        if not self._data.long_format or time_range is None:
            return None

        k_values = self._data.k["values"].values
        start_idx = max(0, time_range[0] - 1)
        end_idx = min(len(k_values), time_range[1])
        return k_values[start_idx:end_idx].tolist()

    @staticmethod
    def _format_title(
            config: dict,
            scope: str,
            node_idx: Optional[str],
            line_idx: Optional[str]) -> str:
        """Format the plot title based on scope."""
        if scope == "Global":
            return config["title_global"]

        title_template = config["title_local"]
        return title_template.format(node=node_idx, line=line_idx)

    def _create_plot(
            self,
            df: pd.DataFrame,
            config: dict,
            title: str
    ) -> go.Figure:
        """Create the actual plot based on configuration."""
        plot_type = config["plot_type"]
        x_col = config["x_col"]
        y_col = config.get("y_col", "values")
        color_col = config.get("color_col")
        hover_data = config.get("hover_data")

        # Apply aggregation if specified
        if config.get("aggregation") == "sum" and color_col:
            df = df.groupby(color_col, as_index=False)[y_col].sum()

        # Ensure proper types for categorical plots
        if plot_type == PlotType.BAR and color_col:
            df[x_col] = df[x_col].astype(str)
            df[color_col] = df[color_col].astype(str)

        # Create plot based on type
        fig = self._create_figure(
            df=df,
            plot_type=plot_type,
            x_col=x_col,
            y_col=y_col,
            color_col=color_col,
            title=title,
            config=config,
            hover_data=hover_data
        )

        return fig

    def _create_figure(
            self,
            df: pd.DataFrame,
            plot_type: PlotType,
            x_col: str,
            y_col: Optional[str],
            color_col: Optional[str],
            title: str,
            config: dict,
            hover_data: Optional[dict] = None
    ) -> go.Figure:
        """Create a Plotly figure based on plot type."""

        labels = {
            x_col: config.get("x_label", x_col),
        }
        if y_col:
            labels[y_col] = config.get("y_label", y_col)
        if color_col and config.get("legend_title"):
            labels[color_col] = config["legend_title"]

        common_args = {
            "title": title,
            "labels": labels,
            "color_discrete_sequence": self._colors,
        }

        if plot_type == PlotType.AREA:
            fig = px.area(
                df, x=x_col, y=y_col, color=color_col,
                **common_args
            )

        elif plot_type == PlotType.LINE:
            fig = px.line(
                df, x=x_col, y=y_col, color=color_col,
                hover_data=hover_data,
                **common_args
            )

        elif plot_type == PlotType.BAR:
            fig = px.bar(
                df, x=x_col, y=y_col, color=color_col,
                **common_args
            )

        elif plot_type == PlotType.HISTOGRAM:
            fig = px.histogram(
                df, x=x_col, color=color_col,
                nbins=config.get("nbins", 10),
                **common_args
            )

        elif plot_type == PlotType.SCATTER:
            fig = px.scatter(
                df, x=x_col, y=y_col, color=color_col,
                hover_data=hover_data,
                **common_args
            )

        else:
            fig = self._create_placeholder_plot("Unsupported plot type")

        return fig

    @staticmethod
    def _create_placeholder_plot(message: str) -> go.Figure:
        """Create a placeholder plot with a message."""
        fig = px.scatter(title=message)
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        return fig


# =============================================================================
# Public API
# =============================================================================

def generate_plot(
        data_source: Any,
        x_axis: str,
        y_axis: str,
        scope: str,
        node_idx: Optional[str] = None,
        line_idx: Optional[str] = None,
        selected_period: Optional[str] = None,
        time_range: Optional[list[int]] = None,
) -> Optional[go.Figure]:
    """
    Generate a plot based on the provided parameters.

    This is the main entry point for plot generation, maintaining backward
    compatibility with the existing API while using the new PlotGenerator.

    Args:
        data_source: Object containing the data (e.g., LEGO_GPT instance).
        x_axis: X-axis variable selection.
        y_axis: Y-axis variable selection.
        scope: "Global" or "Local" scope.
        node_idx: Node identifier for local plots.
        line_idx: Line identifier for local plots.
        selected_period: Selected representative period.
        time_range: Time range [start, end] for filtering.

    Returns:
        Plotly Figure object or None.
    """
    generator = PlotGenerator(data_source)
    return generator.generate(
        x_axis=x_axis,
        y_axis=y_axis,
        scope=scope,
        node_idx=node_idx,
        line_idx=line_idx,
        selected_period=selected_period,
        time_range=time_range
    )
