"""
Layout Builder Module for LEGO-GPT

This module provides a LayoutBuilder class that constructs the Dash application UI
using composable component factories. This separates layout logic from the main
application class for better maintainability and extensibility.
"""

from typing import TYPE_CHECKING

import dash_leaflet as dl
from dash import dcc, html

if TYPE_CHECKING:
    from data_provider import DataProvider
    from config import AppConfig


# =============================================================================
# Style Constants
# =============================================================================

class Colors:
    """Application color palette."""
    PRIMARY = "#6BA3A3"
    SECONDARY = "#E1EDED"
    ACCENT = "#2E86AB"
    TEXT = "#333333"
    TEXT_LIGHT = "#666666"
    BACKGROUND = "#6BA3A3"
    SURFACE = "#FFFFFF"
    BORDER = "#CCCCCC"
    ERROR = "#E74C3C"
    SUCCESS = "#2ECC71"


class Spacing:
    """Spacing constants."""
    XS = "4px"
    SM = "8px"
    MD = "12px"
    LG = "16px"
    XL = "24px"
    XXL = "32px"


# =============================================================================
# Base Styles
# =============================================================================

class BaseStyles:
    """Base style definitions for common components."""

    @staticmethod
    def card(padding: str = Spacing.MD) -> dict:
        """Card/panel style with subtle shadow."""
        return {
            "backgroundColor": Colors.SURFACE,
            "borderRadius": "8px",
            "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.1)",
            "padding": padding,
        }

    @staticmethod
    def flex_row(
            gap: str = Spacing.MD,
            align: str = "center",
            justify: str = "flex-start",
            wrap: bool = False
    ) -> dict:
        """Flexbox row layout."""
        return {
            "display": "flex",
            "flexDirection": "row",
            "alignItems": align,
            "justifyContent": justify,
            "gap": gap,
            "flexWrap": "wrap" if wrap else "nowrap",
        }

    @staticmethod
    def flex_column(
            gap: str = Spacing.MD,
            align: str = "stretch"
    ) -> dict:
        """Flexbox column layout."""
        return {
            "display": "flex",
            "flexDirection": "column",
            "alignItems": align,
            "gap": gap,
        }

    @staticmethod
    def button(variant: str = "primary") -> dict:
        """Button styles."""
        base = {
            "padding": f"{Spacing.SM} {Spacing.MD}",
            "borderRadius": "6px",
            "fontWeight": "600",
            "fontSize": "14px",
            "cursor": "pointer",
            "border": "none",
            "transition": "all 0.2s ease",
            "minWidth": "80px",
        }

        if variant == "primary":
            base.update({
                "backgroundColor": Colors.ACCENT,
                "color": Colors.SURFACE,
            })
        elif variant == "secondary":
            base.update({
                "backgroundColor": Colors.SECONDARY,
                "color": Colors.TEXT,
                "border": f"1px solid {Colors.BORDER}",
            })

        return base

    @staticmethod
    def dropdown(width: str = "150px") -> dict:
        """Dropdown styles."""
        return {
            "width": width,
            "fontWeight": "500",
            "fontSize": "14px",
        }

    @staticmethod
    def input_field(width: str = "100px") -> dict:
        """Input field styles."""
        return {
            "width": width,
            "padding": Spacing.SM,
            "borderRadius": "4px",
            "border": f"1px solid {Colors.BORDER}",
            "fontSize": "14px",
        }


# =============================================================================
# Layout Builder
# =============================================================================

class LayoutBuilder:
    """
    Builds the Dash application layout using composable components.

    This class encapsulates all layout-related logic, making it easier to:
    - Modify individual UI components
    - Add new controls or visualizations
    - Customize styling from a central location

    Attributes:
        config: Application configuration.
        data_provider: Interface to access data for UI components.
    """

    def __init__(self, config: "AppConfig", data_provider: "DataProvider"):
        """
        Initialize the LayoutBuilder.

        Args:
            config: Application configuration object.
            data_provider: Data provider for accessing data attributes.
        """
        self.config = config
        self.data = data_provider

    def build(self) -> html.Div:
        """
        Build the complete application layout.

        Returns:
            Root Div element containing the entire layout.
        """
        return html.Div(
            children=[
                self._build_header(),
                self._build_control_panel(),
                self._build_stores(),
                self._build_main_content(),
            ],
            style={
                "backgroundColor": Colors.BACKGROUND,
                "minHeight": "100vh",
                "padding": Spacing.MD,
            }
        )

    # =========================================================================
    # Header
    # =========================================================================

    @staticmethod
    def _build_header() -> html.Div:
        """Build the application header."""
        return html.Div(
            children=[
                html.H1(
                    "LEGO-GPT",
                    style={
                        "margin": "0",
                        "fontSize": "24px",
                        "fontWeight": "700",
                        "color": Colors.SURFACE,
                    }
                ),
                html.Span(
                    "Graph Plotting Tool",
                    style={
                        "fontSize": "14px",
                        "color": "rgba(255, 255, 255, 0.8)",
                        "marginLeft": Spacing.MD,
                    }
                ),
            ],
            style={
                **BaseStyles.flex_row(align="baseline"),
                "marginBottom": Spacing.MD,
            }
        )

    # =========================================================================
    # Control Panel
    # =========================================================================

    def _build_control_panel(self) -> html.Div:
        """Build the control panel with all controls."""
        return html.Div(
            children=[
                self._build_map_controls(),
                self._build_plot_controls(),
            ],
            style={
                **BaseStyles.card(padding=Spacing.MD),
                "marginBottom": Spacing.MD,
            }
        )

    def _build_map_controls(self) -> html.Div:
        """Build map-related controls."""
        return html.Div(
            children=[
                html.Label(
                    "Map Controls",
                    style={
                        "fontWeight": "600",
                        "fontSize": "12px",
                        "color": Colors.TEXT_LIGHT,
                        "textTransform": "uppercase",
                        "marginBottom": Spacing.SM,
                    }
                ),
                html.Div(
                    children=[
                        self._build_period_dropdown(),
                        self._build_node_search(),
                        self._build_pq_toggle(),
                        self._build_time_slider(),
                    ],
                    style=BaseStyles.flex_row(gap=Spacing.LG, wrap=True),
                ),
            ],
            style={
                **BaseStyles.flex_column(gap=Spacing.SM),
                "marginBottom": Spacing.LG,
            }
        )

    def _build_plot_controls(self) -> html.Div:
        """Build plot-related controls."""
        return html.Div(
            children=[
                html.Label(
                    "Plot Controls",
                    style={
                        "fontWeight": "600",
                        "fontSize": "12px",
                        "color": Colors.TEXT_LIGHT,
                        "textTransform": "uppercase",
                        "marginBottom": Spacing.SM,
                    }
                ),
                html.Div(
                    children=[
                        self._build_x_axis_dropdown(),
                        self._build_y_axis_dropdown(),
                        self._build_scope_button(),
                        self._build_time_range_slider(),
                    ],
                    style=BaseStyles.flex_row(gap=Spacing.LG, wrap=True),
                ),
            ],
            style=BaseStyles.flex_column(gap=Spacing.SM),
        )

    # =========================================================================
    # Individual Controls
    # =========================================================================

    def _build_period_dropdown(self) -> html.Div:
        """Build representative period dropdown."""
        is_long_format = self.data.is_long_format

        if is_long_format:
            options = [{"label": "All Periods", "value": "All"}]
            value = "All"
        else:
            periods = self.data.get_representative_periods()
            options = [{"label": f"Period {p}", "value": p} for p in periods]
            value = periods[0] if periods else "All"

        return html.Div(
            children=[
                html.Label(
                    "Period",
                    style=self._label_style()
                ),
                dcc.Dropdown(
                    id="rep-period-dropdown",
                    options=options,
                    value=value,
                    clearable=False,
                    style=BaseStyles.dropdown(width="140px"),
                ),
            ],
            style={
                **BaseStyles.flex_column(gap=Spacing.XS),
                "display": "none" if is_long_format else "flex",
            }
        )

    def _build_node_search(self) -> html.Div:
        """Build node search dropdown."""
        node_options = self.data.get_node_options()

        return html.Div(
            children=[
                html.Label(
                    "Search Node",
                    style=self._label_style()
                ),
                dcc.Dropdown(
                    id="node-search-dropdown",
                    options=node_options,
                    placeholder="Type to search...",
                    clearable=True,
                    style=BaseStyles.dropdown(width="180px"),
                ),
            ],
            style=BaseStyles.flex_column(gap=Spacing.XS),
        )

    def _build_pq_toggle(self) -> html.Div:
        """Build P/Q toggle button."""
        return html.Div(
            children=[
                html.Label(
                    "Display Mode",
                    style=self._label_style()
                ),
                html.Button(
                    "Active Power (P)",
                    id="pq-toggle-button",
                    n_clicks=0,
                    style=BaseStyles.button("secondary"),
                ),
            ],
            style=BaseStyles.flex_column(gap=Spacing.XS),
        )

    def _build_time_slider(self) -> html.Div:
        """Build time slider with optional number input."""
        time_count = self.data.get_time_step_count()
        time_labels = self.data.get_time_step_labels()
        is_long_format = self.data.is_long_format

        # Create marks for slider
        marks = self._create_slider_marks(time_count, time_labels)

        return html.Div(
            children=[
                html.Label(
                    "Time Step",
                    style=self._label_style()
                ),
                html.Div(
                    children=[
                        html.Div(
                            dcc.Slider(
                                id="time-slider",
                                min=1,
                                max=time_count,
                                step=1,
                                marks=marks,
                                tooltip={"placement": "top", "always_visible": False},
                                value=1,
                            ),
                            style={"flex": "1", "minWidth": "200px"},
                        ),
                        dcc.Input(
                            id="time-slider-input",
                            type="number",
                            min=1,
                            max=time_count,
                            step=1,
                            value=1,
                            style={
                                **BaseStyles.input_field(width="70px"),
                                "display": "block" if is_long_format else "none",
                            },
                        ),
                    ],
                    style=BaseStyles.flex_row(gap=Spacing.SM),
                ),
            ],
            style={
                **BaseStyles.flex_column(gap=Spacing.XS),
                "flex": "1",
                "minWidth": "250px",
            },
        )

    def _build_y_axis_dropdown(self) -> html.Div:
        """Build Y-axis selection dropdown."""
        options = self._get_dropdown_options(self.config.dropdown_options_y)

        return html.Div(
            children=[
                html.Label(
                    "Y-Axis",
                    style=self._label_style()
                ),
                dcc.Dropdown(
                    id="y-axis-dropdown",
                    options=options,
                    value=options[0]["value"] if options else None,
                    clearable=False,
                    style=BaseStyles.dropdown(width="160px"),
                ),
            ],
            style=BaseStyles.flex_column(gap=Spacing.XS),
        )

    def _build_x_axis_dropdown(self) -> html.Div:
        """Build X-axis selection dropdown."""
        options = self._get_dropdown_options(self.config.dropdown_options_x)

        return html.Div(
            children=[
                html.Label(
                    "X-Axis",
                    style=self._label_style()
                ),
                dcc.Dropdown(
                    id="x-axis-dropdown",
                    options=options,
                    value=options[0]["value"] if options else None,
                    clearable=False,
                    style=BaseStyles.dropdown(width="160px"),
                ),
            ],
            style=BaseStyles.flex_column(gap=Spacing.XS),
        )

    def _build_scope_button(self) -> html.Div:
        """Build Local/Global scope toggle button."""
        return html.Div(
            children=[
                html.Label(
                    "Scope",
                    style=self._label_style()
                ),
                html.Button(
                    "Local",
                    id="local-button",
                    n_clicks=0,
                    style=BaseStyles.button("secondary"),
                ),
            ],
            style=BaseStyles.flex_column(gap=Spacing.XS),
        )

    def _build_time_range_slider(self) -> html.Div:
        """Build time range slider (only visible in long format)."""
        time_count = self.data.get_time_step_count()
        time_labels = self.data.get_time_step_labels()
        is_long_format = self.data.is_long_format

        marks = self._create_slider_marks(time_count, time_labels)
        default_end = min(24, time_count)

        return html.Div(
            children=[
                html.Label(
                    "Time Range",
                    style=self._label_style()
                ),
                dcc.RangeSlider(
                    id="time-slider-range",
                    min=1,
                    max=time_count,
                    step=1,
                    marks=marks,
                    tooltip={"placement": "top", "always_visible": False},
                    value=[1, default_end],
                    pushable=min(24, time_count // 2),
                ),
            ],
            style={
                **BaseStyles.flex_column(gap=Spacing.XS),
                "flex": "1",
                "minWidth": "250px",
                "display": "flex" if is_long_format else "none",
            },
        )

    # =========================================================================
    # Store Components
    # =========================================================================

    def _build_stores(self) -> html.Div:
        """Build dcc.Store components for state management."""
        default_line = self.data.get_default_line_id()
        default_node = self.data.get_default_node_id()
        default_zoom = self.config.map_options.default_zoom

        return html.Div([
            dcc.Store(id="last-clicked-line", data=default_line),
            dcc.Store(id="last-clicked-node", data=default_node),
            dcc.Store(id="map-zoom", data=default_zoom),
        ])

    # =========================================================================
    # Main Content
    # =========================================================================

    def _build_main_content(self) -> html.Div:
        """Build main content area with map and graph."""
        return html.Div(
            children=[
                self._build_map_panel(),
                self._build_graph_panel(),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": Spacing.MD,
                "height": "calc(100vh - 200px)",
                "minHeight": "500px",
            }
        )

    def _build_map_panel(self) -> html.Div:
        """Build the map visualization panel."""
        bounds = self.data.get_map_bounds()
        center = self.data.get_map_center()

        return html.Div(
            children=[
                dl.Map(
                    children=[
                        dl.TileLayer(
                            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                        ),
                        dl.ZoomControl(position="topright"),
                        html.Div(id="network-layer"),
                        html.Div(id="node-wrapper"),
                    ],
                    bounds=bounds,
                    style={"height": "100%", "width": "100%", "borderRadius": "8px"},
                    id="network-map",
                    zoomControl=False,
                    center=center,
                ),
            ],
            style={
                **BaseStyles.card(padding="0"),
                "overflow": "hidden",
                "height": "100%",
            }
        )

    def _build_graph_panel(self) -> html.Div:
        """Build the graph visualization panel."""
        return html.Div(
            children=[
                dcc.Graph(
                    id="dynamic-plot",
                    style={"height": "100%", "width": "100%"},
                ),
            ],
            id="dynamic-plot-container",
            style={
                **BaseStyles.card(padding=Spacing.SM),
                "height": "100%",
            }
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @staticmethod
    def _label_style() -> dict:
        """Get consistent label styling."""
        return {
            "fontSize": "12px",
            "fontWeight": "500",
            "color": Colors.TEXT_LIGHT,
        }

    @staticmethod
    def _create_slider_marks(
            count: int,
            labels: list[str]
    ) -> dict:
        """Create slider marks for start, middle, and end."""
        if count < 1:
            return {}

        marks = {
            1: {"label": str(labels[0]) if labels else "1"},
        }

        if count > 2:
            mid = count // 2
            marks[mid] = {"label": str(labels[mid - 1]) if len(labels) >= mid else str(mid)}

        if count > 1:
            marks[count] = {"label": str(labels[-1]) if labels else str(count)}

        return marks

    @staticmethod
    def _get_dropdown_options(options: list) -> list[dict]:
        """
        Convert dropdown options to standard format.

        Args:
            options: List of DropdownOption objects or dicts.

        Returns:
            List of dicts with 'label' and 'value' keys.
        """
        result = []
        for opt in options:
            if hasattr(opt, 'label') and hasattr(opt, 'value'):
                result.append({"label": opt.label, "value": opt.value})
            elif isinstance(opt, dict):
                result.append(opt)
            else:
                result.append({"label": str(opt), "value": str(opt)})
        return result
