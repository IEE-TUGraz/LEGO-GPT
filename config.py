"""
Configuration Module for LEGO-GPT

This module provides typed configuration classes with validation for the LEGO-GPT application.
It replaces raw dictionary access with structured, validated configuration objects.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml


# =============================================================================
# Nested Configuration Classes
# =============================================================================

@dataclass
class DropdownOption:
    """Single dropdown option configuration."""
    label: str
    value: str


@dataclass
class ClusterOptions:
    """Clustering options for map visualization."""
    cluster_radius: int = 60
    maxZoom: int = 16


@dataclass
class MapConfig:
    """Configuration for map visualization."""
    line_weight: int = 2
    default_zoom: int = 5
    arrow_zoom_scale: float = 0.5
    arrow_min_size: float = 0.5
    pie_chart_min_radius: int = 8
    pie_chart_max_radius: int = 16
    carto_api_key: str = ""
    technology_colors: dict[str, str] = field(default_factory=dict)
    cluster_options: ClusterOptions = field(default_factory=ClusterOptions)

    @classmethod
    def from_dict(cls, data: dict) -> "MapConfig":
        """Create MapConfig from dictionary."""
        cluster_opts = data.pop("cluster_options", {})
        cluster_config = ClusterOptions(**cluster_opts) if cluster_opts else ClusterOptions()
        return cls(cluster_options=cluster_config, **data)


@dataclass
class GraphSaveOptions:
    """Options for saving graphs."""
    format: str = "svg"
    filename: str = "custom_image"
    height: int = 500
    width: int = 700
    scale: int = 1


@dataclass
class AxisConfig:
    """Axis configuration for graphs."""
    domain: list[float] = field(default_factory=lambda: [0, 1])
    title: dict = field(default_factory=dict)


@dataclass
class LegendConfig:
    """Legend configuration for graphs."""
    x: float = 0.85
    y: float = 1
    xanchor: str = "left"
    yanchor: str = "top"


@dataclass
class MarginConfig:
    """Margin configuration for graphs."""
    l: int = 0
    r: int = 40
    t: int = 40
    b: int = 40


@dataclass
class LayoutConfig:
    """Layout configuration for Plotly graphs."""
    xaxis: dict = field(default_factory=dict)
    yaxis: dict = field(default_factory=dict)
    legend: dict = field(default_factory=dict)
    margin: dict = field(default_factory=dict)
    paper_bgcolor: str = "#E1EDED"
    plot_bgcolor: str = "#E1EDED"
    font: dict = field(default_factory=lambda: {"size": 14})
    title: dict = field(default_factory=lambda: {"x": 0.5})


@dataclass
class GraphConfig:
    """Configuration for graph visualization."""
    graph_save_options: dict = field(default_factory=dict)
    layout: dict = field(default_factory=dict)
    colors: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "GraphConfig":
        """Create GraphConfig from dictionary."""
        return cls(**data)


# =============================================================================
# Main Application Configuration
# =============================================================================

@dataclass
class AppConfig:
    """
    Main application configuration with validation.

    This class encapsulates all configuration options for the LEGO-GPT application,
    providing type safety and validation.

    Attributes:
        input_dir: Path to input data directory or file.
        input_type: Type of input data ("sqlite" or "excel").
        tables: List of table names to load.
        dropdown_options_y: Y-axis dropdown options.
        dropdown_options_x: X-axis dropdown options.
        map_options: Map visualization configuration.
        graph_options: Graph visualization configuration.
    """
    input_dir: str
    input_type: Literal["sqlite", "excel", "V2G"]
    tables: list[str]
    dropdown_options_y: list[DropdownOption]
    dropdown_options_x: list[DropdownOption]
    map_options: MapConfig
    graph_options: GraphConfig

    # Required tables for the application to function
    REQUIRED_TABLES: list[str] = field(
        default_factory=lambda: ["i", "la", "vLineP", "pPmax", "k", "vGenP", "gi"],
        repr=False
    )

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_input_type()
        self._validate_required_tables()
        self._validate_input_path()

    def _validate_input_type(self) -> None:
        """Validate that input_type is supported."""
        valid_types = ("sqlite", "excel", "V2G")
        if self.input_type not in valid_types:
            raise ValueError(
                f"Invalid input_type: '{self.input_type}'. "
                f"Must be one of: {valid_types}"
            )

    def _validate_required_tables(self) -> None:
        """Validate that all required tables are present."""
        missing = [t for t in self.REQUIRED_TABLES if t not in self.tables]
        if missing:
            raise ValueError(
                f"Missing required table(s): {', '.join(missing)}. "
                f"Required tables are: {self.REQUIRED_TABLES}"
            )

    def _validate_input_path(self) -> None:
        """Validate that input path exists."""
        path = Path(self.input_dir)
        if not path.exists():
            raise FileNotFoundError(
                f"Input path does not exist: {self.input_dir}"
            )

    @classmethod
    def from_dict(cls, config_dict: dict) -> "AppConfig":
        """
        Create AppConfig from a configuration dictionary.

        Args:
            config_dict: Raw configuration dictionary (e.g., from YAML).

        Returns:
            Validated AppConfig instance.
        """
        # Parse dropdown options
        dropdown_y = [
            DropdownOption(**opt) if isinstance(opt, dict) else opt
            for opt in config_dict.get("dropdown_options_y", [])
        ]
        dropdown_x = [
            DropdownOption(**opt) if isinstance(opt, dict) else opt
            for opt in config_dict.get("dropdown_options_x", [])
        ]

        # Parse map options
        map_opts = config_dict.get("map_options", {})
        map_config = MapConfig.from_dict(map_opts.copy())

        # Parse graph options
        graph_opts = config_dict.get("graph_options", {})
        graph_config = GraphConfig.from_dict(graph_opts.copy())

        return cls(
            input_dir=config_dict["input_dir"],
            input_type=config_dict["input_type"],
            tables=config_dict.get("tables", []),
            dropdown_options_y=dropdown_y,
            dropdown_options_x=dropdown_x,
            map_options=map_config,
            graph_options=graph_config,
        )

    @classmethod
    def from_yaml(cls, config_path: str) -> "AppConfig":
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file.

        Returns:
            Validated AppConfig instance.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, 'r') as f:
            config_dict = yaml.safe_load(f)

        return cls.from_dict(config_dict)


# =============================================================================
# Configuration Utilities
# =============================================================================

def load_config(config_path: str = "config.yml") -> AppConfig:
    """
    Load and validate application configuration.

    Args:
        config_path: Path to configuration file.

    Returns:
        Validated AppConfig instance.
    """
    return AppConfig.from_yaml(config_path)


def get_default_config() -> dict:
    """
    Get default configuration dictionary.

    Returns:
        Default configuration as dictionary.
    """
    return {
        "input_type": "sqlite",
        "input_dir": "PATH_TO_LEGO_RESULTS",
        "tables": [
            "rp", "k", "i", "g", "gi", "la",
            "vLineP", "vLineQ", "vGenP", "vSOCP_cii",
            "pPmax", "vStIntraRes", "coords", "voltage_bounds"
        ],
        "dropdown_options_y": [
            {"label": "Y: Dispatch", "value": "dispatch"},
            {"label": "Y: Power Flow", "value": "power_flow"},
            {"label": "Y: Demand", "value": "demand"},
        ],
        "dropdown_options_x": [
            {"label": "X: Time", "value": "time"},
            {"label": "X: Generator", "value": "generator"},
            {"label": "X: Line", "value": "line"},
        ],
        "map_options": {
            "line_weight": 2,
            "default_zoom": 5,
            "arrow_zoom_scale": 0.5,
            "arrow_min_size": 0.5,
            "pie_chart_min_radius": 8,
            "pie_chart_max_radius": 16,
            "carto_api_key": "",
            "technology_colors": {},
            "cluster_options": {
                "cluster_radius": 60,
                "maxZoom": 16
            }
        },
        "graph_options": {
            "graph_save_options": {
                "toImageButtonOptions": {
                    "format": "svg",
                    "filename": "custom_image",
                    "height": 500,
                    "width": 700,
                    "scale": 1
                }
            },
            "layout": {},
            "colors": []
        }
    }
