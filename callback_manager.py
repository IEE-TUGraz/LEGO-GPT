"""
Callback Manager Module for LEGO-GPT

This module provides a CallbackManager class that registers and manages all Dash callbacks.
It separates callback logic from the main application class for better organization
and maintainability.
"""

from typing import TYPE_CHECKING, Callable

import dash
from dash import Input, Output, State, ctx, dcc
from dash.exceptions import PreventUpdate

from layout_builder import Colors

if TYPE_CHECKING:
    from data_provider import DataProvider
    from config import AppConfig


class CallbackManager:
    """
    Manages Dash callbacks for the LEGO-GPT application.

    This class encapsulates all callback registration and handling logic,
    making it easier to:
    - Add or modify callbacks without changing the main app
    - Test callback logic in isolation
    - Understand the application's reactive behavior

    Attributes:
        app: The Dash application instance.
        config: Application configuration.
        data_provider: Data provider for accessing data.
        visualization_handlers: Dict of visualization handler functions.
    """

    def __init__(
            self,
            app: dash.Dash,
            config: "AppConfig",
            data_provider: "DataProvider",
            visualization_handlers: dict[str, Callable]
    ):
        """
        Initialize the CallbackManager.

        Args:
            app: Dash application instance.
            config: Application configuration.
            data_provider: Data provider instance.
            visualization_handlers: Dict with 'network_map' and 'dynamic_plot' handlers.
        """
        self.app = app
        self.config = config
        self.data = data_provider
        self.handlers = visualization_handlers

    def register_all(self) -> None:
        """Register all callbacks with the Dash application."""
        self._register_network_update_callback()
        self._register_line_click_callback()
        self._register_node_click_callback()
        self._register_slider_sync_callback()
        self._register_scope_toggle_callback()
        self._register_pq_toggle_callback()
        self._register_zoom_store_callback()
        self._register_node_search_zoom_callback()
        self._register_plot_update_callback()
        self._register_plot_panel_toggle_callback()
        self._register_map_export_callback()

    # =========================================================================
    # Network Map Callbacks
    # =========================================================================

    def _register_network_update_callback(self) -> None:
        """Register callback for updating the network map."""

        @self.app.callback(
            [
                Output("network-layer", "children"),
                Output("node-wrapper", "children")
            ],
            [
                Input("rep-period-dropdown", "value"),
                Input("time-slider", "value"),
                Input("map-zoom", "data"),
                Input("network-map", "viewport"),
                Input("pq-toggle-button", "children")
            ]
        )
        def update_network(
                selected_period: str,
                selected_time: int,
                zoom_level: int,
                viewport: dict,
                pq_button_label: str
        ):
            """Update the network map visualization."""
            # Get zoom from viewport if available
            if viewport and 'zoom' in viewport:
                zoom_level = viewport['zoom']

            # Convert button label to mode
            # Button shows "P" or "Q", convert to "vLineP" or "vLineQ"
            pq_mode = "vLineP" if pq_button_label == "P" else "vLineQ"

            # Call the network map handler
            handler = self.handlers.get('network_map')
            if handler:
                return handler(
                    selected_period=selected_period,
                    selected_time=selected_time,
                    zoom_level=zoom_level,
                    pq_mode=pq_mode
                )

            return [], []

    # =========================================================================
    # Click Event Callbacks
    # =========================================================================

    def _register_line_click_callback(self) -> None:
        """Register callback for storing last clicked line."""

        @self.app.callback(
            Output("last-clicked-line", "data"),
            Input("line-click-layer", "clickData")
        )
        def store_last_clicked_line(click_data: dict):
            """Store the ID of the last clicked line."""
            if not click_data:
                return dash.no_update

            props = click_data.get("properties", {})
            clicked_id = props.get("line", props.get("id"))
            if clicked_id is None:
                return dash.no_update

            clicked_id = str(clicked_id)
            print(f"Clicked line: {clicked_id}")
            return clicked_id

    def _register_node_click_callback(self) -> None:
        """Register callback for storing last clicked node."""

        @self.app.callback(
            Output("last-clicked-node", "data"),
            [
                Input("node-layer", "clickData"),
                Input("node-search-dropdown", "value")
            ]
        )
        def store_last_clicked_node(click_data: dict, search_value: str):
            """Store the ID of the last clicked or searched node."""
            if not ctx.triggered:
                return dash.no_update

            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_id == "node-search-dropdown" and search_value:
                return search_value

            elif triggered_id == "node-layer" and click_data:
                props = click_data.get("properties", {})
                clicked_id = props.get("name", props.get("id"))

                if clicked_id:
                    print(f"Clicked node: {clicked_id}")
                    return clicked_id

            return dash.no_update

    # =========================================================================
    # Control Sync Callbacks
    # =========================================================================

    def _register_slider_sync_callback(self) -> None:
        """Register callback for syncing time slider with input field."""

        @self.app.callback(
            [
                Output("time-slider", "value"),
                Output("time-slider-input", "value")
            ],
            [
                Input("time-slider", "value"),
                Input("time-slider-input", "value")
            ]
        )
        def sync_slider_and_input(slider_val: int, input_val: int):
            """Synchronize time slider and number input values."""
            if not ctx.triggered:
                raise PreventUpdate

            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_id == "time-slider":
                return slider_val, slider_val
            else:
                return input_val, input_val

    # =========================================================================
    # Toggle Button Callbacks
    # =========================================================================

    def _register_scope_toggle_callback(self) -> None:
        """Register callback for toggling Local/Global scope."""

        @self.app.callback(
            Output("local-button", "children"),
            Input("local-button", "n_clicks")
        )
        def toggle_scope_label(n_clicks: int) -> str:
            """Toggle between Local and Global scope."""
            if n_clicks % 2 == 0:
                return "Local"
            return "Global"

    def _register_pq_toggle_callback(self) -> None:
        """Register callback for toggling P/Q display mode."""

        @self.app.callback(
            Output("pq-toggle-button", "children"),
            Input("pq-toggle-button", "n_clicks")
        )
        def toggle_pq_label(n_clicks: int) -> str:
            """Toggle between P (Active) and Q (Reactive) power display."""
            if n_clicks % 2 == 0:
                return "P"
            return "Q"

    # =========================================================================
    # Map Control Callbacks
    # =========================================================================

    def _register_zoom_store_callback(self) -> None:
        """Register callback for storing map zoom level."""

        @self.app.callback(
            Output("map-zoom", "data"),
            Input("network-map", "zoom")
        )
        def store_map_zoom(zoom_level: int) -> int:
            """Store the current map zoom level."""
            return zoom_level

    def _register_node_search_zoom_callback(self) -> None:
        """Register callback for zooming to searched node."""

        @self.app.callback(
            Output("network-map", "viewport"),
            Input("node-search-dropdown", "value"),
            prevent_initial_call=True
        )
        def zoom_to_node(node_name: str) -> dict:
            """Zoom map to the selected node."""
            if not node_name:
                return dash.no_update

            coords = self.data.get_node_coordinates(node_name)
            if coords != (0.0, 0.0):
                return {'center': list(coords), 'zoom': 12}

            return dash.no_update

    # =========================================================================
    # Plot Panel Callbacks
    # =========================================================================

    def _register_plot_panel_toggle_callback(self) -> None:
        """Register callback for toggling the plot panel visibility."""

        @self.app.callback(
            [
                Output("plot-panel", "style"),
                Output("plot-panel-visible", "data"),
                Output("toggle-plot-panel", "style"),
            ],
            [
                Input("toggle-plot-panel", "n_clicks"),
                Input("close-plot-panel", "n_clicks"),
                Input("last-clicked-node", "data"),
            ],
            [
                State("plot-panel-visible", "data"),
                State("plot-panel", "style"),
                State("toggle-plot-panel", "style"),
            ],
            prevent_initial_call=True
        )
        def toggle_plot_panel(
                toggle_clicks: int,
                close_clicks: int,
                last_node: str,
                is_visible: bool,
                panel_style: dict,
                button_style: dict
        ):
            """Toggle the plot panel visibility with slide animation."""
            if not ctx.triggered:
                raise PreventUpdate

            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Determine new visibility state
            if triggered_id == "toggle-plot-panel":
                new_visible = not is_visible
            elif triggered_id == "close-plot-panel":
                new_visible = False
            elif triggered_id == "last-clicked-node":
                new_visible = True
            else:
                raise PreventUpdate

            # Update panel style
            new_panel_style = panel_style.copy() if panel_style else {}
            if new_visible:
                new_panel_style["transform"] = "translateX(0)"
            else:
                new_panel_style["transform"] = "translateX(100%)"

            # Update button style to show active state
            new_button_style = button_style.copy() if button_style else {}
            if new_visible:
                new_button_style["backgroundColor"] = "#226885"  # Darker when active
            else:
                new_button_style["backgroundColor"] = Colors.ACCENT  # Normal color

            return new_panel_style, new_visible, new_button_style

    # =========================================================================
    # Map Export Callback
    # =========================================================================

    def _register_map_export_callback(self) -> None:
        """Register callback for exporting the network map as a vector graphic."""

        @self.app.callback(
            Output("map-export-download", "data"),
            Input("export-map-button", "n_clicks"),
            [
                State("rep-period-dropdown", "value"),
                State("time-slider", "value"),
                State("pq-toggle-button", "children"),
                State("map-export-format", "value"),
            ],
            prevent_initial_call=True
        )
        def export_map(
                n_clicks: int,
                selected_period: str,
                selected_time: int,
                pq_button_label: str,
                fmt: str
        ):
            """Export the current network map view as a vector graphic."""
            if not n_clicks:
                raise PreventUpdate

            handler = self.handlers.get('map_export')
            if not handler:
                raise PreventUpdate

            pq_mode = "vLineP" if pq_button_label == "P" else "vLineQ"
            fmt = fmt or "svg"

            file_bytes = handler(
                selected_period=selected_period,
                selected_time=selected_time,
                pq_mode=pq_mode,
                fmt=fmt
            )

            return dcc.send_bytes(lambda buf: buf.write(file_bytes), f"network_map.{fmt}")

    # =========================================================================
    # Plot Update Callback
    # =========================================================================

    def _register_plot_update_callback(self) -> None:
        """Register callback for updating the dynamic plot."""

        @self.app.callback(
            Output("dynamic-plot", "figure"),
            [
                Input("x-axis-dropdown", "value"),
                Input("y-axis-dropdown", "value"),
                Input("last-clicked-line", "data"),
                Input("last-clicked-node", "data"),
                Input("rep-period-dropdown", "value"),
                Input("local-button", "children"),
                Input("time-slider-range", "value")
            ]
        )
        def update_dynamic_plot(
                x_axis: str,
                y_axis: str,
                line_idx: str,
                node_idx: str,
                selected_period: str,
                scope: str,
                time_range: list[int]
        ):
            """Update the dynamic plot based on user selections."""
            print(
                f"Updating plot: x_axis={x_axis}, y_axis={y_axis}, "
                f"selected_period={selected_period}, time_range={time_range}, "
                f"node={node_idx}, line={line_idx}, scope={scope}"
            )

            handler = self.handlers.get('dynamic_plot')
            if handler:
                return handler(
                    x_axis=x_axis,
                    y_axis=y_axis,
                    line_idx=line_idx,
                    node_idx=node_idx,
                    selected_period=selected_period,
                    scope=scope,
                    time_range=time_range
                )

            return {}


class CallbackRegistry:
    """
    Registry for custom callbacks.

    This class allows plugins or extensions to register additional callbacks
    without modifying the core callback manager.

    Usage:
        registry = CallbackRegistry(app)
        registry.register(
            outputs=[Output("my-component", "value")],
            inputs=[Input("trigger", "n_clicks")],
            handler=my_handler_function
        )
    """

    def __init__(self, app: dash.Dash):
        """
        Initialize the callback registry.

        Args:
            app: Dash application instance.
        """
        self.app = app
        self._callbacks: list[dict] = []

    def register(
            self,
            outputs: list[Output],
            inputs: list[Input],
            handler: Callable,
            prevent_initial_call: bool = False
    ) -> None:
        """
        Register a custom callback.

        Args:
            outputs: List of Output components.
            inputs: List of Input components.
            handler: Callback handler function.
            prevent_initial_call: Whether to prevent initial callback execution.
        """
        callback_info = {
            'outputs': outputs,
            'inputs': inputs,
            'handler': handler,
            'prevent_initial_call': prevent_initial_call
        }
        self._callbacks.append(callback_info)

        # Register with Dash
        self.app.callback(
            outputs,
            inputs,
            prevent_initial_call=prevent_initial_call
        )(handler)

    def get_registered_callbacks(self) -> list[dict]:
        """Get list of registered callbacks."""
        return self._callbacks.copy()
