"""
Data Provider Module for LEGO-GPT

This module provides a DataProvider class that abstracts data access for the UI components.
It serves as an interface between the raw data (loaded by data_loader) and the UI layer,
enabling loose coupling and easier testing.
"""

from typing import Any, Optional, Protocol

import numpy as np
import pandas as pd


class DataProviderProtocol(Protocol):
    """Protocol defining the interface for data providers."""

    @property
    def is_long_format(self) -> bool:
        """Whether data is in long format (many time steps, few/one rep period)."""
        ...

    def get_node_options(self) -> list[dict[str, str]]:
        """Get node options for dropdowns."""
        ...

    def get_time_step_count(self) -> int:
        """Get total number of time steps."""
        ...

    def get_time_step_labels(self) -> list[str]:
        """Get labels for time steps."""
        ...

    def get_representative_periods(self) -> list[str]:
        """Get list of representative periods."""
        ...


class DataProvider:
    """
    Provides a clean interface to access data for UI components.

    This class wraps the raw data loaded by the data_loader module and provides
    convenient methods for the UI layer to access data without knowing the
    underlying data structure.

    Attributes:
        _data_source: The underlying data source (typically LEGO_GPT instance).
    """

    def __init__(self, data_source: Any):
        """
        Initialize the DataProvider.

        Args:
            data_source: Object containing the loaded data (e.g., LEGO_GPT instance).
        """
        self._data_source = data_source
        self._long_format: Optional[bool] = None

    # =========================================================================
    # Format Detection
    # =========================================================================

    @property
    def is_long_format(self) -> bool:
        """
        Determine if data is in long format.

        Long format: Many time steps (>24) with single or no representative period.
        Short format: Multiple representative periods with fewer time steps each.

        Returns:
            True if data is in long format, False otherwise.
        """
        if self._long_format is None:
            tables = getattr(self._data_source, 'tables', [])
            rp = getattr(self._data_source, 'rp', pd.DataFrame())
            k = getattr(self._data_source, 'k', pd.DataFrame())

            # Long format if no rp table, or single rp with many time steps
            if "rp" not in tables:
                self._long_format = True
            elif len(rp) == 1 and len(k) > 24:
                self._long_format = True
            else:
                self._long_format = False

        return self._long_format

    # =========================================================================
    # Node Data Access
    # =========================================================================

    def get_node_options(self) -> list[dict[str, str]]:
        """
        Get node options for dropdown components.

        Returns:
            List of dicts with 'label' and 'value' keys for each node.
        """
        nodes = self._get_nodes()
        return [{"label": node, "value": node} for node in nodes.index]

    def get_node_ids(self) -> list[str]:
        """
        Get list of all node IDs.

        Returns:
            List of node identifier strings.
        """
        return list(self._get_nodes().index)

    def get_default_node_id(self) -> str:
        """
        Get the default node ID (first node).

        Returns:
            First node ID as string.
        """
        nodes = self._get_nodes()
        return str(nodes.index[0]) if len(nodes) > 0 else ""

    def get_node_coordinates(self, node_id: str) -> tuple[float, float]:
        """
        Get coordinates for a specific node.

        Args:
            node_id: Node identifier.

        Returns:
            Tuple of (latitude, longitude).
        """
        nodes = self._get_nodes()
        if node_id in nodes.index:
            return nodes.loc[node_id, 'lat'], nodes.loc[node_id, 'lon']
        return 0.0, 0.0

    # =========================================================================
    # Time Step Data Access
    # =========================================================================

    def get_time_step_count(self) -> int:
        """
        Get total number of time steps.

        Returns:
            Number of time steps.
        """
        k = self._get_time_steps()
        return len(k)

    def get_time_step_labels(self) -> list[str]:
        """
        Get labels for all time steps.

        Returns:
            List of time step labels.
        """
        k = self._get_time_steps()
        return k["values"].to_list()

    def get_time_step_by_index(self, index: int) -> str:
        """
        Get time step label by index (1-based).

        Args:
            index: 1-based index of time step.

        Returns:
            Time step label.
        """
        k = self._get_time_steps()
        if 1 <= index <= len(k):
            return str(k["values"].iloc[index - 1])
        return str(k["values"].iloc[0])

    # =========================================================================
    # Representative Period Data Access
    # =========================================================================

    def get_representative_periods(self) -> list[str]:
        """
        Get list of representative periods.

        Returns:
            List of representative period identifiers.
        """
        rp = getattr(self._data_source, 'rp', pd.DataFrame())
        if rp.empty:
            return []
        return rp["values"].to_list()

    def get_representative_period_count(self) -> int:
        """
        Get number of representative periods.

        Returns:
            Number of representative periods.
        """
        return len(self.get_representative_periods())

    # =========================================================================
    # Line Data Access
    # =========================================================================

    def get_line_ids(self) -> list[str]:
        """
        Get list of all line IDs.

        Returns:
            List of line identifier strings.
        """
        la = self._get_lines()
        return [str(idx) for idx in la.index]

    def get_default_line_id(self) -> str:
        """
        Get the default line ID (first line).

        Returns:
            First line ID as string.
        """
        la = self._get_lines()
        return str(la.index[0]) if len(la) > 0 else "0"

    def get_line_tuples(self) -> list[tuple]:
        """
        Get line data as list of tuples for iteration.

        Returns:
            List of (index, i, j) tuples.
        """
        la = self._get_lines()
        return list(la.itertuples(index=True))

    # =========================================================================
    # Map Data Access
    # =========================================================================

    def get_map_bounds(self) -> list[list[float]]:
        """
        Get map bounds for initial view.

        Returns:
            List of [[min_lat, min_lon], [max_lat, max_lon]].
        """
        bounds = getattr(self._data_source, 'bounds', None)
        if bounds:
            return bounds

        # Calculate from node coordinates
        nodes = self._get_nodes()
        if 'lat' in nodes.columns and 'lon' in nodes.columns:
            return [
                [float(nodes['lat'].min()), float(nodes['lon'].min())],
                [float(nodes['lat'].max()), float(nodes['lon'].max())]
            ]

        # Default bounds (Europe)
        return [[35.0, -10.0], [60.0, 30.0]]

    def get_map_center(self) -> list[float]:
        """
        Get map center coordinates.

        Returns:
            List of [latitude, longitude].
        """
        nodes = self._get_nodes()
        if 'lat' in nodes.columns and 'lon' in nodes.columns:
            return [float(np.mean(nodes['lat'])), float(np.mean(nodes['lon']))]
        return [47.0, 15.0]  # Default center (Austria)

    # =========================================================================
    # Generator Data Access
    # =========================================================================

    def get_generators_for_node(self, node_id: str) -> list[str]:
        """
        Get generators connected to a specific node.

        Args:
            node_id: Node identifier.

        Returns:
            List of generator IDs.
        """
        gi = getattr(self._data_source, 'gi', pd.DataFrame())
        if gi.empty:
            return []

        mask = gi['i'] == node_id
        return list(gi.loc[mask, 'g'].values)

    # =========================================================================
    # Raw Data Access (for visualization handlers)
    # =========================================================================

    def get_vLineP(self) -> pd.DataFrame:
        """Get line active power flow data."""
        return getattr(self._data_source, 'vLineP', pd.DataFrame())

    def get_vLineQ(self) -> Optional[pd.DataFrame]:
        """Get line reactive power flow data."""
        return getattr(self._data_source, 'vLineQ', None)

    def get_vGenP(self) -> pd.DataFrame:
        """Get generator power data."""
        return getattr(self._data_source, 'vGenP', pd.DataFrame())

    def get_vSOCP_cii(self) -> Optional[pd.DataFrame]:
        """Get voltage data."""
        return getattr(self._data_source, 'vSOCP_cii', None)

    def get_pPmax(self) -> pd.DataFrame:
        """Get line capacity data."""
        return getattr(self._data_source, 'pPmax', pd.DataFrame())

    def get_gi(self) -> pd.DataFrame:
        """Get generator-node mapping."""
        return getattr(self._data_source, 'gi', pd.DataFrame())

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    def _get_nodes(self) -> pd.DataFrame:
        """Get nodes DataFrame."""
        return getattr(self._data_source, 'i', pd.DataFrame())

    def _get_time_steps(self) -> pd.DataFrame:
        """Get time steps DataFrame."""
        return getattr(self._data_source, 'k', pd.DataFrame())

    def _get_lines(self) -> pd.DataFrame:
        """Get lines DataFrame."""
        return getattr(self._data_source, 'la', pd.DataFrame())
