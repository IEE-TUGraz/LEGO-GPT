"""
Callback Manager Module for LEGO-GPT

This module provides a CallbackManager class that registers and manages all Dash callbacks.
It separates callback logic from the main application class for better organization
and maintainability.
"""

from typing import TYPE_CHECKING, Callable

import dash
from dash import Input, Output, ctx
from dash.exceptions import PreventUpdate

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
                pq_mode: str
        ):
            """Update the network map visualization."""
            # Get zoom from viewport if available
            if viewport and 'zoom' in viewport:
                zoom_level = viewport['zoom']

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
        # Get all line IDs for creating Input components
        line_tuples = self.data.get_line_tuples()

        @self.app.callback(
            Output("last-clicked-line", "data"),
            [Input(str(line.Index), "n_clicks") for line in line_tuples]
        )
        def store_last_clicked_line(*args):
            """Store the ID of the last clicked line."""
            if not ctx.triggered:
                return dash.no_update

            clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
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
                clicked_id = click_data["properties"]["id"]
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
            """Toggle between vLineP and vLineQ display."""
            if n_clicks % 2 == 0:
                return "vLineP"
            return "vLineQ"

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
    # Plot Update Callback
    # =========================================================================

    def _register_plot_update_callback(self) -> None:
        """Register callback for updating the dynamic plot."""

        @self.app.callback(
            Output("dynamic-plot-container", "children"),
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

            return None


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
