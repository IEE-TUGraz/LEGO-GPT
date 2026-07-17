"""
Layout Builder Module for LEGO-GPT

This module provides a LayoutBuilder class that constructs the Dash application UI
with a map-focused design and collapsible plot panel.
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
    PRIMARY = "#4A8A8A"
    PRIMARY_LIGHT = "#6BA3A3"
    SECONDARY = "#E1EDED"
    ACCENT = "#1b5066"
    TEXT = "#333333"
    TEXT_LIGHT = "#666666"
    TEXT_INVERSE = "#FFFFFF"
    BACKGROUND = "#5A9A9A"
    SURFACE = "#FFFFFF"
    BORDER = "#CCCCCC"
    OVERLAY = "rgba(0, 0, 0, 0.3)"


class Spacing:
    """Spacing constants."""
    XS = "4px"
    SM = "8px"
    MD = "12px"
    LG = "16px"
    XL = "24px"


# =============================================================================
# Layout Builder
# =============================================================================

class LayoutBuilder:
    """
    Builds the Dash application layout with map-focused design.
    """

    def __init__(self, config: "AppConfig", data_provider: "DataProvider"):
        self.config = config
        self.data = data_provider

    def build(self) -> html.Div:
        """Build the complete application layout."""
        return html.Div(
            children=[
                # Top control bar
                self._build_control_bar(),

                # Main content area (map + collapsible panel)
                self._build_main_area(),

                # State stores
                self._build_stores(),
            ],
            style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "right": "0",
                "bottom": "0",
                "height": "100vh",
                "width": "100vw",
                "overflow": "hidden",
                "display": "flex",
                "flexDirection": "column",
                "backgroundColor": Colors.BACKGROUND,
                "margin": "0",
                "padding": "0",
            }
        )

    # =========================================================================
    # Control Bar
    # =========================================================================

    def _build_control_bar(self) -> html.Div:
        """Build the top control bar with Left, Center, and Right sections."""
        return html.Div(
            children=[
                # 1. LEFT SECTION: Logo, Node, PQ
                html.Div(
                    children=[
                        # Logo
                        html.Div(
                            children=[
                                html.Span("LEGO-GPT", style={"fontWeight": "700"})
                            ],
                            style={
                                "fontSize": "20px",
                                "color": Colors.TEXT_INVERSE,
                                "marginRight": Spacing.XL,
                                "flexShrink": "0",
                            }
                        ),
                        # Left Controls
                        self._build_period_control(),
                        self._build_node_search_control(),
                        self._build_pq_toggle_control(),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": Spacing.MD,
                    }
                ),

                # 2. CENTER SECTION: Time Slider
                html.Div(
                    children=[self._build_time_slider_control()],
                    style={
                        "position": "absolute",
                        "left": "50%",
                        "transform": "translateX(-50%)",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                    }
                ),

                # 3. RIGHT SECTION: Map Export, Plot Toggle
                html.Div(
                    children=[
                        self._build_map_export_control(),
                        self._build_plot_toggle_button(),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": Spacing.SM,
                    }
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": f"{Spacing.SM} {Spacing.LG}",
                "backgroundColor": Colors.PRIMARY,
                "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                "zIndex": "1000",
                "flexShrink": "0",
                "height": "45px",
                "position": "relative",  # Required for absolute positioning of center element
            }
        )

    def _build_period_control(self) -> html.Div:
        """Build compact period dropdown."""
        is_long_format = self.data.is_long_format

        if is_long_format:
            options = [{"label": "All", "value": "All"}]
            value = "All"
        else:
            periods = self.data.get_representative_periods()
            options = [{"label": f"P{p}", "value": p} for p in periods]
            value = periods[0] if periods else "All"

        return html.Div(
            children=[
                dcc.Dropdown(
                    id="rep-period-dropdown",
                    options=options,
                    value=value,
                    clearable=False,
                    style={"width": "100px", "fontSize": "13px"},
                    placeholder="Period",
                ),
            ],
            style={"display": "none" if is_long_format else "block"},
            title="Representative Period"
        )

    def _build_node_search_control(self) -> html.Div:
        """Build compact node search."""
        node_options = self.data.get_node_options()

        return html.Div(
            children=[
                dcc.Dropdown(
                    id="node-search-dropdown",
                    options=node_options,
                    placeholder="🔍  Node",
                    clearable=True,
                    style={"width": "180px", "fontSize": "13px"},
                ),
            ],
            title="Search Node"
        )

    @staticmethod
    def _build_pq_toggle_control() -> html.Button:
        """Build P/Q toggle button."""
        return html.Button(
            "P",
            id="pq-toggle-button",
            n_clicks=0,
            style={
                "width": "50px",
                "height": "38px",
                "borderRadius": "4px",
                "border": "none",
                "backgroundColor": Colors.SURFACE,
                "color": Colors.TEXT,
                "fontWeight": "700",
                "fontSize": "16px",
                "cursor": "pointer",
                "boxShadow": "0 1px 3px rgba(0,0,0,0.2)"
            },
            title="Toggle Active/Reactive Power (P/Q)"
        )

    def _build_time_slider_control(self) -> html.Div:
        """Build centralized time slider."""
        time_count = self.data.get_time_step_count()

        # Generate marks: Only for start and end to keep it clean
        marks = {}
        if time_count > 0:
            marks[1] = "1"
            if time_count > 1:
                marks[time_count] = str(time_count)

        return html.Div(
            children=[
                html.Span("Time Selection", style={
                    "color": Colors.TEXT_INVERSE,
                    "fontSize": "14px",
                    "fontWeight": "600",
                    "marginRight": Spacing.MD,
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px"
                }),
                html.Div(
                    dcc.Slider(
                        id="time-slider",
                        min=1,
                        max=time_count,
                        step=1,
                        marks=marks,  # Only start and end marks
                        tooltip={"placement": "bottom", "always_visible": False},
                        value=1,
                        updatemode='drag',
                    ),
                    style={"width": "350px"},
                ),
                dcc.Input(
                    id="time-slider-input",
                    type="number",
                    min=1,
                    max=time_count,
                    step=1,
                    value=1,
                    style={
                        "width": "60px",
                        "height": "32px",
                        "border": "none",
                        "borderRadius": "4px",
                        "textAlign": "center",
                        "fontSize": "14px",
                        "marginLeft": Spacing.MD,
                        "fontWeight": "600",
                        "color": Colors.TEXT
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "backgroundColor": "rgba(0,0,0,0.1)",
                "padding": "4px 16px",
                "borderRadius": "8px",
            },
            title="Time Step Selection"
        )

    @staticmethod
    def _build_map_export_control() -> html.Div:
        """Build the map export format selector and download button."""
        return html.Div(
            children=[
                dcc.Dropdown(
                    id="map-export-format",
                    options=[
                        {"label": "SVG", "value": "svg"},
                        {"label": "PDF", "value": "pdf"},
                    ],
                    value="svg",
                    clearable=False,
                    searchable=False,
                    style={"width": "80px", "fontSize": "13px"},
                ),
                html.Button(
                    children=[
                        html.Span("⬇", style={"marginRight": Spacing.XS}),
                        html.Span("Export Map"),
                    ],
                    id="export-map-button",
                    n_clicks=0,
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "padding": f"{Spacing.SM} {Spacing.MD}",
                        "borderRadius": "6px",
                        "border": "none",
                        "backgroundColor": Colors.ACCENT,
                        "color": Colors.TEXT_INVERSE,
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "cursor": "pointer",
                    },
                    title="Export the current map view as a vector graphic"
                ),
                dcc.Download(id="map-export-download"),
            ],
            style={"display": "flex", "alignItems": "center", "gap": Spacing.XS},
        )

    @staticmethod
    def _build_plot_toggle_button() -> html.Button:
        """Build the plot panel toggle button."""
        return html.Button(
            children=[
                html.Span("📊", style={"marginRight": Spacing.XS}),
                html.Span("Plots"),
            ],
            id="toggle-plot-panel",
            n_clicks=0,
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": f"{Spacing.SM} {Spacing.MD}",
                "borderRadius": "6px",
                "border": "none",
                "backgroundColor": Colors.ACCENT,
                "color": Colors.TEXT_INVERSE,
                "fontWeight": "600",
                "fontSize": "14px",
                "cursor": "pointer",
                "transition": "all 0.2s ease",
            },
            title="Toggle Plot Panel"
        )

    # =========================================================================
    # Main Area
    # =========================================================================

    def _build_main_area(self) -> html.Div:
        """Build the main content area."""
        return html.Div(
            children=[
                self._build_map_container(),
                self._build_plot_panel(),
            ],
            style={
                "flex": "1",
                "display": "flex",
                "position": "relative",
                "overflow": "hidden",
            }
        )

    def _build_map_container(self) -> html.Div:
        """Build the map container."""
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
                        dl.ZoomControl(position="bottomright"),
                        html.Div(id="network-layer"),
                        html.Div(id="node-wrapper"),
                    ],
                    bounds=bounds,
                    style={"height": "100%", "width": "100%"},
                    id="network-map",
                    zoomControl=False,
                    center=center,

                    zoomDelta=0.25,
                    zoomSnap=0.25,
                    wheelPxPerZoomLevel=120,
                ),
            ],
            style={
                "flex": "1",
                "height": "100%",
                "transition": "margin-right 0.3s ease",
                "marginRight": "0px",  # Initial state
            },
            id="map-container"
        )

    def _build_plot_panel(self) -> html.Div:
        """Build the collapsible plot panel."""
        return html.Div(
            children=[
                self._build_panel_header(),
                self._build_plot_controls(),
                html.Div(
                    children=[
                        dcc.Graph(
                            id="dynamic-plot",
                            style={"height": "100%", "width": "100%"},
                            config={
                                "displayModeBar": True,
                                "displaylogo": False,
                                "toImageButtonOptions": self.config.graph_options.graph_save_options.get(
                                    "toImageButtonOptions", {}
                                ),
                            },
                        ),
                    ],
                    id="dynamic-plot-container",
                    style={
                        "flex": "1",
                        "overflow": "hidden",
                        "backgroundColor": Colors.SECONDARY,
                        "borderRadius": "8px",
                        "margin": Spacing.SM,
                    }
                ),
            ],
            id="plot-panel",
            style={
                "width": "50vw",  # Half screen
                "height": "100%",
                "backgroundColor": Colors.SURFACE,
                "boxShadow": "-4px 0 12px rgba(0,0,0,0.1)",
                "display": "flex",
                "flexDirection": "column",
                "position": "absolute",
                "right": "0",
                "top": "0",
                "transform": "translateX(100%)",
                "transition": "transform 0.3s ease",
                "zIndex": "500",
            }
        )

    @staticmethod
    def _build_panel_header() -> html.Div:
        """Build the plot panel header."""
        return html.Div(
            children=[
                html.Span("📊 Analysis Panel", style={
                    "fontWeight": "600",
                    "fontSize": "15px",
                    "color": Colors.TEXT,
                }),
                html.Button(
                    "✕",
                    id="close-plot-panel",
                    n_clicks=0,
                    style={
                        "width": "28px",
                        "height": "28px",
                        "borderRadius": "4px",
                        "border": "none",
                        "backgroundColor": "transparent",
                        "color": Colors.TEXT_LIGHT,
                        "fontSize": "16px",
                        "cursor": "pointer",
                    },
                    title="Close Panel"
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "space-between",
                "padding": Spacing.MD,
                "borderBottom": f"1px solid {Colors.BORDER}",
                "flexShrink": "0",
            }
        )

    def _build_plot_controls(self) -> html.Div:
        """Build the plot controls."""
        time_count = self.data.get_time_step_count()
        time_labels = self.data.get_time_step_labels()
        is_long_format = self.data.is_long_format

        y_options = self._get_dropdown_options(self.config.dropdown_options_y)
        x_options = self._get_dropdown_options(self.config.dropdown_options_x)

        return html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div([
                            html.Label("Y-Axis", style=self._label_style()),
                            dcc.Dropdown(
                                id="y-axis-dropdown",
                                options=y_options,
                                value=y_options[0]["value"] if y_options else None,
                                clearable=False,
                                style={"fontSize": "13px"},
                            ),
                        ], style={"flex": "1"}),
                        html.Div([
                            html.Label("X-Axis", style=self._label_style()),
                            dcc.Dropdown(
                                id="x-axis-dropdown",
                                options=x_options,
                                value=x_options[0]["value"] if x_options else None,
                                clearable=False,
                                style={"fontSize": "13px"},
                            ),
                        ], style={"flex": "1"}),
                        html.Div([
                            html.Label("Scope", style=self._label_style()),
                            html.Button(
                                "Local",
                                id="local-button",
                                n_clicks=0,
                                style={
                                    "width": "100%",
                                    "height": "36px",
                                    "borderRadius": "4px",
                                    "border": f"1px solid {Colors.BORDER}",
                                    "backgroundColor": Colors.SURFACE,
                                    "color": Colors.TEXT,
                                    "fontWeight": "500",
                                    "fontSize": "13px",
                                    "cursor": "pointer",
                                },
                            ),
                        ], style={"width": "70px", "flexShrink": "0"}),
                    ],
                    style={
                        "display": "flex",
                        "gap": Spacing.SM,
                        "marginBottom": Spacing.SM,
                    }
                ),
                html.Div(
                    children=[
                        self._build_axis_range_control("Y-Axis", "y"),
                        self._build_axis_range_control("X-Axis", "x"),
                    ],
                    style={
                        "display": "flex",
                        "gap": Spacing.LG,
                        "marginBottom": Spacing.SM,
                    }
                ),
                html.Div(
                    children=[
                        html.Label("Time Range", style=self._label_style()),
                        dcc.RangeSlider(
                            id="time-slider-range",
                            min=1,
                            max=time_count,
                            step=1,
                            marks=self._create_slider_marks(time_count, time_labels),
                            tooltip={"placement": "bottom", "always_visible": False},
                            value=[1, min(24, time_count)],
                            pushable=1,
                        ),
                    ],
                    style={"display": "block" if is_long_format else "none"}
                ),
            ],
            style={
                "padding": Spacing.MD,
                "borderBottom": f"1px solid {Colors.BORDER}",
                "flexShrink": "0",
                "backgroundColor": Colors.SURFACE,
            }
        )

    def _build_axis_range_control(self, axis_label: str, prefix: str) -> html.Div:
        """Build a fixed-range control (checkbox + min/max inputs) for one plot axis."""
        return html.Div(
            children=[
                dcc.Checklist(
                    id=f"{prefix}-axis-fixed",
                    options=[{"label": f" Fix {axis_label}", "value": "fixed"}],
                    value=[],
                    style={"fontSize": "12px", "color": Colors.TEXT_LIGHT, "whiteSpace": "nowrap"},
                ),
                dcc.Input(
                    id=f"{prefix}-axis-min",
                    type="number",
                    placeholder="Min",
                    style={"width": "64px", "fontSize": "12px", "height": "28px"},
                ),
                dcc.Input(
                    id=f"{prefix}-axis-max",
                    type="number",
                    placeholder="Max",
                    style={"width": "64px", "fontSize": "12px", "height": "28px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "gap": Spacing.XS},
        )

    def _build_stores(self) -> html.Div:
        """Build stores."""
        default_line = self.data.get_default_line_id()
        default_node = self.data.get_default_node_id()
        default_zoom = self.config.map_options.default_zoom

        return html.Div([
            dcc.Store(id="last-clicked-line", data=default_line),
            dcc.Store(id="last-clicked-node", data=default_node),
            dcc.Store(id="map-zoom", data=default_zoom),
            dcc.Store(id="plot-panel-visible", data=False),
        ])

    @staticmethod
    def _label_style() -> dict:
        return {
            "fontSize": "11px",
            "fontWeight": "500",
            "color": Colors.TEXT_LIGHT,
            "marginBottom": "2px",
            "display": "block",
        }

    @staticmethod
    def _create_slider_marks(count: int, labels: list[str]) -> dict:
        if count < 1: return {}
        marks = {1: str(labels[0]) if labels else "1"}
        if count > 2:
            mid = count // 2
            marks[mid] = str(labels[mid - 1]) if len(labels) >= mid else str(mid)
        if count > 1:
            marks[count] = str(labels[-1]) if labels else str(count)
        return marks

    @staticmethod
    def _get_dropdown_options(options: list) -> list[dict]:
        result = []
        for opt in options:
            if hasattr(opt, 'label') and hasattr(opt, 'value'):
                label = opt.label
                if label.startswith("Y: ") or label.startswith("X: "): label = label[3:]
                result.append({"label": label, "value": opt.value})
            elif isinstance(opt, dict):
                label = opt.get("label", "")
                if label.startswith("Y: ") or label.startswith("X: "): label = label[3:]
                result.append({"label": label, "value": opt.get("value", "")})
            else:
                result.append({"label": str(opt), "value": str(opt)})
        return result
