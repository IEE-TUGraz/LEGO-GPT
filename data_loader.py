"""
Data Loader Module for LEGO-GPT

This module provides data loading functionality for different input formats (SQLite, Excel).
It uses a strategy pattern to allow easy extension for new data sources.
"""

import os
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

import helper_functions as h


# =============================================================================
# Data Container
# =============================================================================

@dataclass
class LEGOData:
    """Container for all LEGO model data."""

    # Sets
    i: pd.DataFrame = field(default_factory=pd.DataFrame)  # Nodes
    k: pd.DataFrame = field(default_factory=pd.DataFrame)  # Time steps
    rp: pd.DataFrame = field(default_factory=pd.DataFrame)  # Representative periods
    g: pd.DataFrame = field(default_factory=pd.DataFrame)  # Generators
    la: pd.DataFrame = field(default_factory=pd.DataFrame)  # Lines (arcs)
    gi: pd.DataFrame = field(default_factory=pd.DataFrame)  # Generator-node mapping with technology

    # Variables
    vLineP: pd.DataFrame = field(default_factory=pd.DataFrame)  # Active power flow
    vLineQ: Optional[pd.DataFrame] = None  # Reactive power flow
    vGenP: pd.DataFrame = field(default_factory=pd.DataFrame)  # Generator active power
    vSOCP_cii: Optional[pd.DataFrame] = None  # Voltage (SOCP formulation)
    vStIntraRes: Optional[pd.DataFrame] = None  # Storage state of charge

    # Parameters
    pPmax: pd.DataFrame = field(default_factory=pd.DataFrame)  # Line capacity
    coords: pd.DataFrame = field(default_factory=pd.DataFrame)  # Node coordinates
    voltage_bounds: Optional[pd.DataFrame] = None  # Voltage bounds per node

    # Computed attributes
    bounds: list = field(default_factory=list)  # Map bounds [min, max]


# =============================================================================
# Abstract Base Loader
# =============================================================================

class DataLoaderStrategy(ABC):
    """Abstract base class for data loaders."""

    @abstractmethod
    def load(self, input_dir: str, tables: list[str]) -> LEGOData:
        """
        Load data from the specified input directory.

        Args:
            input_dir: Path to the input data directory or file.
            tables: List of table names to load.

        Returns:
            LEGOData container with all loaded data.
        """
        pass


# =============================================================================
# SQLite Data Loader
# =============================================================================

class SQLiteDataLoader(DataLoaderStrategy):
    """Data loader for SQLite database format."""

    # Technology inference rules based on generator name prefixes
    TECHNOLOGY_PREFIXES = {
        "PV_": "Solar",
        "WIND_": "Wind",
        "BSS_": "BESS",
        "HS_": "HS",
        "HPS_": "HPS",
        "ROR_": "RoR",
        "COAL_": "Coal",
        "GAS_": "Gas",
        "NUC_": "Nuclear",
        "OIL_": "Oil",
    }

    def load(self, input_dir: str, tables: list[str]) -> LEGOData:
        """
        Load data from a SQLite database.

        Args:
            input_dir: Path to the directory containing result.sqlite or model.sqlite.
            tables: List of table names to load.

        Returns:
            LEGOData container with all loaded data.
        """
        data = LEGOData()

        # Determine SQLite file path
        db_path = self._find_database(input_dir)

        with sqlite3.connect(db_path) as conn:
            # Load sets
            if "i" in tables:
                data.i = self._load_set(conn, "i")
            if "k" in tables:
                data.k = self._load_set(conn, "k")
            if "rp" in tables:
                data.rp = self._load_set(conn, "rp")
            if "g" in tables:
                data.g = self._load_set(conn, "g")
            if "la" in tables:
                data.la = self._load_lines(conn)

            # Load generator-node mapping with technology
            if "gi" in tables:
                data.gi = self._load_gi(conn)

            # Load variables
            if "vLineP" in tables:
                data.vLineP = self._load_vline(conn, "vLineP", data.la)
            if "vLineQ" in tables:
                data.vLineQ = self._load_vline(conn, "vLineQ", data.la)
            if "vGenP" in tables:
                data.vGenP = self._load_vgenp(conn)
            if "vSOCP_cii" in tables:
                data.vSOCP_cii = self._load_vsocp_cii(conn)
            if "vStIntraRes" in tables:
                data.vStIntraRes = self._load_vstintrares(conn, data.gi)

            # Load parameters
            if "pPmax" in tables:
                data.pPmax = self._load_ppmax(conn, data.la)

            # Load coordinates (try coords table, otherwise create dummy)
            if "coords" in tables:
                data.coords = self._load_coords(conn, data.i)

            # Load voltage bounds
            if "voltage_bounds" in tables:
                data.voltage_bounds = self._load_voltage_bounds(conn)

        return data

    @staticmethod
    def _find_database(input_dir: str) -> str:
        """Find the SQLite database file in the input directory."""
        for filename in ["model.sqlite", "result.sqlite"]:
            path = os.path.join(input_dir, filename)
            if os.path.exists(path):
                return path

        # If input_dir is the file itself
        if os.path.isfile(input_dir) and input_dir.endswith(".sqlite"):
            return input_dir

        raise FileNotFoundError(
            f"No SQLite database found in {input_dir}. "
            "Expected 'model.sqlite' or 'result.sqlite'."
        )

    @staticmethod
    def _load_set(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
        """Load a set table (i, k, rp, g) and standardize column names."""
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        # Drop index column if present
        if "index" in df.columns:
            df = df.drop(columns=["index"])

        # Rename first column to 'values'
        if "0" in df.columns:
            df = df.rename(columns={"0": "values"})

        return df

    @staticmethod
    def _load_lines(conn: sqlite3.Connection) -> pd.DataFrame:
        """Load line set (la) and standardize column names."""
        df = pd.read_sql_query("SELECT * FROM la", conn)

        # Drop index column if present
        if "index" in df.columns:
            df = df.drop(columns=["index"])

        # Rename columns: 0 -> i, 1 -> j, 2 -> c
        rename_map = {"0": "i", "1": "j", "2": "c"}
        df = df.rename(columns=rename_map)

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)
        if "c" in df.columns:
            df["c"] = df["c"].astype(str)

        return df

    def _load_gi(self, conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load generator-node mapping and infer technology type.

        Uses gi table for generators and gi_storage for storage units.
        Technology is inferred from generator name prefixes.
        """
        # Load main gi table
        df_gi = pd.read_sql_query("SELECT * FROM gi", conn)
        if "index" in df_gi.columns:
            df_gi = df_gi.drop(columns=["index"])
        df_gi = df_gi.rename(columns={"0": "g", "1": "i"})

        # Load gi_storage if exists
        try:
            df_gi_storage = pd.read_sql_query("SELECT * FROM gi_storage", conn)
            if "index" in df_gi_storage.columns:
                df_gi_storage = df_gi_storage.drop(columns=["index"])
            df_gi_storage = df_gi_storage.rename(columns={"0": "g", "1": "i"})

            # Combine gi and gi_storage
            df_gi = pd.concat([df_gi, df_gi_storage], ignore_index=True).drop_duplicates()
        except Exception:
            pass  # gi_storage may not exist

        # Infer technology from generator names
        df_gi["tec"] = df_gi["g"].apply(self._infer_technology)

        return df_gi

    def _infer_technology(self, generator_name: str) -> str:
        """Infer technology type from generator name prefix."""
        gen_upper = generator_name.upper()

        for prefix, technology in self.TECHNOLOGY_PREFIXES.items():
            if gen_upper.startswith(prefix):
                return technology

        return "unknown"

    def _load_vline(
            self,
            conn: sqlite3.Connection,
            table_name: str,
            la: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Load line flow variable (vLineP or vLineQ) and process duplicates.

        Args:
            conn: Database connection.
            table_name: Table name (vLineP or vLineQ).
            la: Lines dataframe for line indexing.

        Returns:
            Processed line flow dataframe with line indices and canonical IDs.
        """
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        # Rename columns from level_X format
        rename_map = {
            "level_0": "rp",
            "level_1": "k",
            "level_2": "i",
            "level_3": "j",
            "level_4": "c"
        }
        df = df.rename(columns=rename_map)

        # Ensure string types for node columns
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # Add canonical line identifier for safe merging
        df = h.add_canonical_line_ids(df, "i", "j")

        # Generate unique line index (direction-insensitive)
        line_index_dict = self._build_line_index(la)

        # Map each row to its line index and detect duplicates
        df["line"] = df.apply(
            lambda row: self._get_line_index(row, line_index_dict),
            axis=1
        )
        df["duplicate"] = df.apply(
            lambda row: self._is_duplicate(row, la, line_index_dict),
            axis=1
        )

        # Reverse flow values for duplicate (reverse direction) entries
        df.loc[df["duplicate"], "values"] *= -1

        # Average flows for same line and time step
        df["values"] = df.groupby(["line", "k"])["values"].transform(
            lambda x: x.mean() if len(x) > 1 else x
        )

        # Keep only non-duplicate entries
        df = df[~df["duplicate"]].copy()
        df = df.drop(columns=["duplicate"])
        df = df.reset_index(drop=True)

        # Convert line to string for consistency with callback IDs
        df["line"] = df["line"].astype(str)

        return df

    @staticmethod
    def _build_line_index(la: pd.DataFrame) -> dict:
        """Build a mapping from frozenset(i, j) to line index."""
        line_index = {}
        for idx, row in la.iterrows():
            key = frozenset([str(row["i"]), str(row["j"])])
            if key not in line_index:
                line_index[key] = len(line_index)
        return line_index

    @staticmethod
    def _get_line_index(row: pd.Series, line_index_dict: dict) -> int:
        """Get the line index for a row."""
        key = frozenset([str(row["i"]), str(row["j"])])
        return line_index_dict.get(key, -1)

    @staticmethod
    def _is_duplicate(
            row: pd.Series,
            la: pd.DataFrame,
            line_index_dict: dict) -> bool:
        """Check if row is a duplicate (reverse direction) entry."""
        key = frozenset([str(row["i"]), str(row["j"])])
        line_idx = line_index_dict.get(key, -1)

        if line_idx < 0 or line_idx >= len(la):
            return False

        original_line = la.iloc[line_idx]
        return [str(row["i"]), str(row["j"])] != [str(original_line["i"]), str(original_line["j"])]

    @staticmethod
    def _load_vgenp(conn: sqlite3.Connection) -> pd.DataFrame:
        """Load generator power variable (vGenP)."""
        df = pd.read_sql_query("SELECT * FROM vGenP", conn)

        # Table should already have proper column names: rp, k, g, values
        required_cols = ["rp", "k", "g", "values"]

        # Ensure all required columns exist
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"vGenP missing required column: {col}")

        return df[required_cols]

    @staticmethod
    def _load_vsocp_cii(conn: sqlite3.Connection) -> pd.DataFrame:
        """Load voltage variable (vSOCP_cii)."""
        df = pd.read_sql_query("SELECT * FROM vSOCP_cii", conn)

        required_cols = ["rp", "k", "i", "values"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"vSOCP_cii missing required column: {col}")

        return df[required_cols]

    @staticmethod
    def _load_vstintrares(
            conn: sqlite3.Connection,
            gi: pd.DataFrame) -> pd.DataFrame:
        """
        Load storage state of charge variable (vStIntraRes).

        Adds node information from gi mapping.
        """
        df = pd.read_sql_query("SELECT * FROM vStIntraRes", conn)

        # Rename storage unit column
        if "intraStorageUnits" in df.columns:
            df = df.rename(columns={"intraStorageUnits": "storageUnits"})

        required_cols = ["rp", "k", "storageUnits", "values"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"vStIntraRes missing required column: {col}")

        # Add node information from gi
        df = df.merge(
            gi[["g", "i"]],
            left_on="storageUnits",
            right_on="g",
            how="left"
        ).drop(columns=["g"])

        return df

    def _load_ppmax(self, conn: sqlite3.Connection, la: pd.DataFrame) -> pd.DataFrame:
        """Load line capacity parameter (pPmax)."""
        df = pd.read_sql_query("SELECT * FROM pPmax", conn)

        # Rename columns from level_X format
        rename_map = {
            "level_0": "i",
            "level_1": "j",
            "level_2": "c"
        }
        df = df.rename(columns=rename_map)

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # Add canonical line identifier
        df = h.add_canonical_line_ids(df, "i", "j")

        # Build line index
        line_index_dict = self._build_line_index(la)

        # Map to line indices
        df["line"] = df.apply(
            lambda row: self._get_line_index(row, line_index_dict),
            axis=1
        )

        # Average values for duplicate lines (same line, different directions)
        df = (
            df.groupby("line_id", as_index=False)
            .agg({"values": "mean", "line": "first"})
        )

        # Convert line to string for consistency
        df["line"] = df["line"].astype(str)

        return df

    @staticmethod
    def _load_coords(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load node coordinates from 'coordsLat' and 'coordsLon' tables.

        Raises:
            ValueError: If tables are missing, malformed, or cannot be merged.
        """
        try:
            # 1. Load the raw tables
            df_lat = pd.read_sql_query("SELECT * FROM coordsLat", conn)
            df_lon = pd.read_sql_query("SELECT * FROM coordsLon", conn)

            # 2. Helper to standardize columns (Node ID -> 'values', Coord -> 'lat'/'lon')
            def standardize_table(df, coord_name):
                # Remove generic index if present
                if "index" in df.columns:
                    df = df.drop(columns=["index"])

                # Identify the Node ID column (usually 'i' or '0')
                node_col = None
                if "i" in df.columns:
                    node_col = "i"
                elif "0" in df.columns:
                    node_col = "0"
                else:
                    # Fallback: assume the first column is the ID if 'i' isn't found
                    node_col = df.columns[0]

                # Identify the Value column (usually 'values', '1', or the remaining column)
                # We assume the column that isn't the node_col is the data
                value_cols = [c for c in df.columns if c != node_col]
                if not value_cols:
                    raise ValueError(f"Could not identify coordinate value column in {coord_name} table")
                val_col = value_cols[0]

                # Rename and cast
                df = df.rename(columns={node_col: "values", val_col: coord_name})
                df["values"] = df["values"].astype(str)

                return df[["values", coord_name]]

            # 3. Process both dataframes
            df_lat = standardize_table(df_lat, "lat")
            df_lon = standardize_table(df_lon, "lon")

            # 4. Merge on the node identifier ('values')
            df_coords = pd.merge(df_lat, df_lon, on="values", how="inner")

            # 5. Validation
            if df_coords.empty:
                raise ValueError("Resulting coordinates table is empty after merge.")

            return df_coords

        except Exception as e:
            raise ValueError(
                f"Error loading coordinates: {e}. "
                "Ensure 'coordsLat' and 'coordsLon' tables exist and contain matching node IDs."
            )

    @staticmethod
    def _load_voltage_bounds(conn: sqlite3.Connection) -> pd.DataFrame:
        """Load voltage bounds (pBusMaxV and pBusMinV)."""
        try:
            df_max = pd.read_sql_query("SELECT * FROM pBusMaxV", conn)
            df_min = pd.read_sql_query("SELECT * FROM pBusMinV", conn)

            # Rename value columns
            df_max = df_max.rename(columns={"values": "pBusMaxV"})
            df_min = df_min.rename(columns={"values": "pBusMinV"})

            # Merge on node name
            df = df_max.merge(df_min[["i", "pBusMinV"]], on="i", how="outer")
            df = df.rename(columns={"i": "values"})
            df = df.set_index("values")

            return df

        except Exception as e:
            print(f"Warning: Could not load voltage bounds: {e}")
            return None


# =============================================================================
# Excel Data Loader (Backwards Compatibility)
# =============================================================================

class ExcelDataLoader(DataLoaderStrategy):
    """Data loader for Excel file format (legacy support)."""

    def load(self, input_dir: str, tables: list[str]) -> LEGOData:
        """
        Load data from Excel files.

        Args:
            input_dir: Path to the directory containing Excel files.
            tables: List of table names to load.

        Returns:
            LEGOData container with all loaded data.
        """
        data = LEGOData()

        for table in tables:
            if table == "vLineP":
                df, df_lines = h.extract_excel_to_dataframe(input_dir, table)
                data.vLineP = df
                data.la = df_lines
            elif table == "vLineQ":
                df, _ = h.extract_excel_to_dataframe(input_dir, table)
                data.vLineQ = df
            elif table == "gi":
                df, df_g = h.extract_excel_to_dataframe(input_dir, table)
                data.gi = df
                data.g = df_g
            elif table in ("la", "g"):
                # These are loaded from other tables
                continue
            elif table == "coords":
                data.coords = h.extract_excel_to_dataframe(input_dir, table)
            elif table == "voltage_bounds":
                data.voltage_bounds = h.extract_excel_to_dataframe(input_dir, table)
            else:
                result = h.extract_excel_to_dataframe(input_dir, table)
                if result is not None:
                    setattr(data, table, result)

        # Process vLineP duplicates
        if data.vLineP is not None and "duplicate" in data.vLineP.columns:
            data.vLineP = data.vLineP[~data.vLineP["duplicate"]].copy()
            data.vLineP = data.vLineP.drop(columns=["duplicate"])

        # Process vLineQ duplicates
        if data.vLineQ is not None and "duplicate" in data.vLineQ.columns:
            data.vLineQ = data.vLineQ[~data.vLineQ["duplicate"]].copy()
            data.vLineQ = data.vLineQ.drop(columns=["duplicate"])

        # Add storage node info
        if data.vStIntraRes is not None and data.gi is not None:
            if "storageUnits" in data.vStIntraRes.columns:
                data.vStIntraRes = data.vStIntraRes.merge(
                    data.gi[["g", "i"]],
                    left_on="storageUnits",
                    right_on="g",
                    how="left"
                ).drop(columns=["g"])

        return data


# =============================================================================
# Main Data Loading Function
# =============================================================================

def get_data(obj) -> None:
    """
    Load and process data from various input sources into the object's attributes.

    This function handles data extraction, transformation, and loading based on 
    the specified input type. It supports SQLite databases and Excel files.

    Args:
        obj: An object with the following attributes:
            - input_type (str): The type of input data ("sqlite" or "excel").
            - input_dir (str): The directory containing the input files or database.
            - tables (list): A list of table names to load and process.

    Raises:
        ValueError: If the input_type is not "sqlite" or "excel".

    Note:
        The processed data is stored as attributes of the provided object.
        After calling this function, the object will have attributes like:
        - i: Node information DataFrame (indexed by 'values')
        - k: Time steps DataFrame
        - rp: Representative periods DataFrame
        - gi: Generator-node mapping with technology
        - la: Lines DataFrame
        - vLineP: Line active power flow DataFrame
        - vGenP: Generator power DataFrame
        - pPmax: Line capacity DataFrame
        - coords: Node coordinates DataFrame
        - bounds: Map bounds for visualization
    """
    # Select appropriate loader
    loader: DataLoaderStrategy

    if obj.input_type == "sqlite":
        loader = SQLiteDataLoader()
    elif obj.input_type == "excel":
        loader = ExcelDataLoader()
    else:
        raise ValueError(
            f"Invalid input type: {obj.input_type}. "
            "Please choose either 'sqlite' or 'excel'."
        )

    # Load data
    data = loader.load(obj.input_dir, obj.tables)

    # Transfer data to object attributes
    _transfer_data_to_object(obj, data)

    # Post-processing
    _postprocess_data(obj)


def _transfer_data_to_object(obj, data: LEGOData) -> None:
    """Transfer data from LEGOData container to object attributes."""
    # Sets
    if not data.i.empty:
        obj.i = data.i
    if not data.k.empty:
        obj.k = data.k
    if not data.rp.empty:
        obj.rp = data.rp
    if not data.g.empty:
        obj.g = data.g
    if not data.la.empty:
        obj.la = data.la
    if not data.gi.empty:
        obj.gi = data.gi

    # Variables
    if not data.vLineP.empty:
        obj.vLineP = data.vLineP
    if data.vLineQ is not None and not data.vLineQ.empty:
        obj.vLineQ = data.vLineQ
    if not data.vGenP.empty:
        obj.vGenP = data.vGenP
    if data.vSOCP_cii is not None and not data.vSOCP_cii.empty:
        obj.vSOCP_cii = data.vSOCP_cii
    if data.vStIntraRes is not None and not data.vStIntraRes.empty:
        obj.vStIntraRes = data.vStIntraRes

    # Parameters
    if not data.pPmax.empty:
        obj.pPmax = data.pPmax
    if not data.coords.empty:
        obj.coords = data.coords
    if data.voltage_bounds is not None and not data.voltage_bounds.empty:
        obj.voltage_bounds = data.voltage_bounds


def _postprocess_data(obj) -> None:
    """Apply common post-processing to loaded data."""

    # Merge coordinates into node info
    if hasattr(obj, "i") and hasattr(obj, "coords"):
        obj.i = pd.merge(
            obj.i,
            obj.coords,
            left_on="values",
            right_on="values",
            how="left"
        )

    # Add voltage bounds to node info
    if hasattr(obj, "voltage_bounds") and obj.voltage_bounds is not None:
        obj.i = pd.merge(
            obj.i,
            obj.voltage_bounds,
            left_on="values",
            right_index=True,
            how="left"
        )

    # Set node index to 'values' for easier lookup
    if hasattr(obj, "i") and "values" in obj.i.columns:
        obj.i.set_index("values", inplace=True)

    # Compute relative line flow values
    if hasattr(obj, "vLineP") and hasattr(obj, "pPmax"):
        _add_relative_line_values(obj.vLineP, obj.pPmax)

    if hasattr(obj, "vLineQ") and obj.vLineQ is not None and hasattr(obj, "pPmax"):
        _add_relative_line_values(obj.vLineQ, obj.pPmax)

    # Compute map bounds
    if hasattr(obj, "i") and "lat" in obj.i.columns and "lon" in obj.i.columns:
        obj.bounds = [
            [obj.i["lat"].min(), obj.i["lon"].min()],
            [obj.i["lat"].max(), obj.i["lon"].max()]
        ]


def _add_relative_line_values(vline_df: pd.DataFrame, ppmax_df: pd.DataFrame) -> None:
    """Add relative values and pPmax to line flow dataframe."""
    ppmax_map = ppmax_df.set_index("line_id")["values"]

    vline_df["rel_values"] = abs(vline_df["values"]) / vline_df["line_id"].map(ppmax_map)
    vline_df["pPmax"] = vline_df["line_id"].map(ppmax_map)
