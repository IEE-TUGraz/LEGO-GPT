"""
LEGO-GPT: Graph Plotting Tool for LEGO

This module provides the main application class for visualizing and analyzing
network data from LEGO optimization results. It creates an interactive web
application with maps and dynamic plots.

Architecture:
    LEGO_GPT (orchestrator)
    ├── AppConfig (configuration with validation)
    ├── DataProvider (data access interface)
    ├── LayoutBuilder (UI component construction)
    ├── CallbackManager (reactive behavior)
    └── MarkerJS (map marker generation)

Usage:
    # From command line
    python LEGO_GPT.py [config_path]

    # From Python
    from LEGO_GPT import LEGO_GPT
    app = LEGO_GPT(config_path="config.yml")
    app.run()
"""

import os
import sys
from typing import Optional

import dash

import helper_functions as h
from MarkerJS import MarkerJS
from callback_manager import CallbackManager
from config import load_config
from data_loader import get_data
from data_provider import DataProvider
from layout_builder import LayoutBuilder
from ui_handler import generate_network_map, generate_dynamic_plot


class LEGO_GPT:
    """
    Main application class for LEGO-GPT visualization tool.

    This class orchestrates the various components of the application:
    - Configuration loading and validation
    - Data loading and preprocessing
    - UI layout construction
    - Callback registration for interactivity

    The class follows a composition pattern, delegating specific responsibilities
    to specialized components while maintaining overall application control.

    Attributes:
        config: Application configuration object.
        data_provider: Interface for data access.
        app: Dash application instance.
        js_generator: Marker generator for map visualization.

    Example:
        >>> app = LEGO_GPT(config_path="my_config.yml")
        >>> app.run(debug=True, port=8050)
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the LEGO-GPT application.

        Args:
            config_path: Path to configuration file. If None, uses "config.yml"
                        in the current directory.

        Raises:
            FileNotFoundError: If configuration file doesn't exist.
            ValueError: If configuration is invalid.
        """
        # Determine config path
        config_path = config_path or "config.yml"

        # Initialize components
        self._load_configuration(config_path)
        self._load_data()
        self._create_app()
        self._setup_ui()
        self._register_callbacks()

    # =========================================================================
    # Initialization Methods
    # =========================================================================

    def _load_configuration(self, config_path: str) -> None:
        """
        Load and validate application configuration.

        Args:
            config_path: Path to configuration file.
        """
        self.config = load_config(config_path)

        # Store commonly accessed config values for backward compatibility
        self.input_dir = self.config.input_dir
        self.input_type = self.config.input_type
        self.tables = self.config.tables
        self.map_options = self._config_to_dict(self.config.map_options)
        self.graph_options = self._config_to_dict(self.config.graph_options)
        self.dropdown_options_y = self._dropdown_options_to_list(
            self.config.dropdown_options_y
        )
        self.dropdown_options_x = self._dropdown_options_to_list(
            self.config.dropdown_options_x
        )

    def _load_data(self) -> None:
        """Load and process data from the configured source."""
        # Load data into self (for backward compatibility with handlers)
        get_data(self)

        # Create data provider for clean access
        self.data_provider = DataProvider(self)

        # Store long_format flag
        self.long_format = self.data_provider.is_long_format

        # Create marker generator
        self.js_generator = MarkerJS(self.map_options, self.vGenP)

    def _create_app(self) -> None:
        """Create and configure the Dash application instance."""
        self.app = dash.Dash(
            __name__,
            suppress_callback_exceptions=True,
            prevent_initial_callbacks=False
        )

        # Set app title
        self.app.title = "LEGO-GPT"

    def _setup_ui(self) -> None:
        """Build and assign the application layout."""
        layout_builder = LayoutBuilder(self.config, self.data_provider)
        self.app.layout = layout_builder.build()

    def _register_callbacks(self) -> None:
        """Register all application callbacks."""
        # Create visualization handlers that wrap existing functions
        visualization_handlers = {
            'network_map': self._create_network_map_handler(),
            'dynamic_plot': self._create_dynamic_plot_handler()
        }

        # Create and register callback manager
        callback_manager = CallbackManager(
            app=self.app,
            config=self.config,
            data_provider=self.data_provider,
            visualization_handlers=visualization_handlers
        )
        callback_manager.register_all()

    # =========================================================================
    # Visualization Handler Factories
    # =========================================================================

    def _create_network_map_handler(self):
        """Create handler function for network map updates."""

        def handler(selected_period, selected_time, zoom_level, pq_mode):
            return generate_network_map(
                self=self,
                selected_period=selected_period,
                selected_time=selected_time,
                zoom_level=zoom_level,
                pq_mode=pq_mode
            )

        return handler

    def _create_dynamic_plot_handler(self):
        """Create handler function for dynamic plot updates."""

        def handler(x_axis, y_axis, line_idx, node_idx, selected_period, scope, time_range):
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

        return handler

    # =========================================================================
    # Configuration Conversion Helpers
    # =========================================================================

    @staticmethod
    def _config_to_dict(config_obj) -> dict:
        """
        Convert a configuration object to dictionary.

        Args:
            config_obj: Configuration dataclass or dict.

        Returns:
            Dictionary representation of the configuration.
        """
        if hasattr(config_obj, '__dataclass_fields__'):
            result = {}
            for field_name in config_obj.__dataclass_fields__:
                value = getattr(config_obj, field_name)
                if hasattr(value, '__dataclass_fields__'):
                    result[field_name] = LEGO_GPT._config_to_dict(value)
                else:
                    result[field_name] = value
            return result
        elif isinstance(config_obj, dict):
            return config_obj
        else:
            return {}

    @staticmethod
    def _dropdown_options_to_list(options) -> list[dict]:
        """
        Convert dropdown options to list of dicts.

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
        return result

    # =========================================================================
    # Public Interface
    # =========================================================================

    def run(
            self,
            debug: bool = False,
            host: str = "127.0.0.1",
            port: int = 8050
    ) -> None:
        """
        Start the Dash application server.

        Args:
            debug: Enable debug mode with auto-reload.
            host: Host address to bind to.
            port: Port number to listen on.
        """
        self.app.run(debug=debug, host=host, port=port)

    def get_server(self):
        """
        Get the underlying Flask server.

        Useful for deploying with WSGI servers like gunicorn.

        Returns:
            Flask server instance.
        """
        return self.app.server


# =============================================================================
# Command Line Interface
# =============================================================================

def main():
    """Main entry point for command line execution."""
    # Parse command line arguments
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yml"

    # Check if config exists, create default if not
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        h.copy_default_config(config_path)
        print("Please edit the configuration file and run again.")
        sys.exit(1)

    # Create and run application
    try:
        app = LEGO_GPT(config_path=config_path)
        print(f"Starting LEGO-GPT server...")
        print(f"Open http://127.0.0.1:8050 in your browser")
        app.run(debug=False)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
