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
    vSOCP: Optional[pd.DataFrame] = None  # Voltage (SOCP formulation)
    vStIntraRes: Optional[pd.DataFrame] = None  # Storage state of charge

    # Parameters
    pPmax: pd.DataFrame = field(default_factory=pd.DataFrame)  # Line capacity
    coords: pd.DataFrame = field(default_factory=pd.DataFrame)  # Node coordinates
    voltage_bounds: Optional[pd.DataFrame] = None  # Voltage bounds per node

    # V2G-specific: Electric Vehicles
    ev: pd.DataFrame = field(default_factory=pd.DataFrame)  # EV set
    ev_availability: Optional[pd.DataFrame] = None  # EV-node-time availability (pAvailable)
    vDchEV: Optional[pd.DataFrame] = None  # EV discharge
    vChEV: Optional[pd.DataFrame] = None  # EV charge
    vSocEV: Optional[pd.DataFrame] = None  # EV state of charge

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
        Load data from a SQLite database with progress tracking.

        Args:
            input_dir: Path to the directory containing result.sqlite or model.sqlite.
            tables: List of table names to load.

        Returns:
            LEGOData container with all loaded data.
        """
        print(f"--- Starting SQLite Data Load ---")
        data = LEGOData()

        # Determine SQLite file path
        db_path = self._find_database(input_dir)
        print(f"Database found: {db_path}")

        with sqlite3.connect(db_path) as conn:
            # Load sets
            print("Loading Sets (i, k, rp, g, la)...")
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
                print("Loading Generator Mappings (gi)...")
                data.gi = self._load_gi(conn)

            # Load variables
            print("Loading Variables (this may take time)...")
            if "vLineP" in tables:
                print("  -> Loading vLineP...")
                data.vLineP = self._load_vline(conn, "vLineP", data.la)
            if "vLineQ" in tables:
                print("  -> Loading vLineQ...")
                data.vLineQ = self._load_vline(conn, "vLineQ", data.la)
            if "vGenP" in tables:
                print("  -> Loading vGenP...")
                data.vGenP = self._load_vgenp(conn)
            if "vSOCP_cii" in tables and "vSOCP_ui" in tables:
                raise ValueError("Cannot load both vSOCP_cii and vSOCP_ui simultaneously.")
            if "vSOCP_cii" in tables and "vSOCP_ui" not in tables:
                print("  -> Loading vSOCP_cii...")
                data.vSOCP = self._load_vsocp_cii(conn)
            if "vSOCP_ui" in tables and "vSOCP_cii" not in tables:
                print("  -> Loading vSOCP_ui...")
                data.vSOCP = self._load_vsocp_ui(conn)
            if "vStIntraRes" in tables:
                print("  -> Loading vStIntraRes...")
                data.vStIntraRes = self._load_vstintrares(conn, data.gi)

            # Load parameters
            print("Loading Parameters...")
            if "pPmax" in tables:
                print("  -> Loading pPmax...")
                data.pPmax = self._load_ppmax(conn, data.la)

            # Load coordinates
            if "coords" in tables:
                print("Loading Coordinates...")
                data.coords = self._load_coords(conn)

            # Load voltage bounds
            if "voltage_bounds" in tables:
                print("Loading Voltage Bounds...")
                data.voltage_bounds = self._load_voltage_bounds(conn)

        print("--- SQLite Data Load Complete ---")
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

    @staticmethod
    def _load_vline(conn: sqlite3.Connection, table_name: str, la: pd.DataFrame) -> pd.DataFrame:
        """
        Load line flow variable (vLineP or vLineQ) using vectorized operations.
        Handles parallel lines by mapping to the first occurrence.

        Args:
            conn: Database connection.
            table_name: Table name (vLineP or vLineQ).
            la: Lines dataframe for line indexing.

        Returns:
            Processed line flow dataframe with line indices and canonical IDs.
        """
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        rename_map = {
            "level_0": "rp", "level_1": "k", "level_2": "i",
            "level_3": "j", "level_4": "c"
        }
        df = df.rename(columns=rename_map)

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # 1. Add canonical IDs
        df = h.add_canonical_line_ids(df, "i", "j")

        # 2. Prepare reference Lines (la) data
        la_ref = la.copy()
        la_ref = h.add_canonical_line_ids(la_ref, "i", "j")
        la_ref = la_ref.reset_index(drop=True)
        la_ref['line_index'] = la_ref.index

        # Handle parallel lines
        la_ref_unique = la_ref.drop_duplicates(subset=["line_id"], keep="first")

        # 3. Vectorized Map
        # Map line index
        line_map = la_ref_unique.set_index("line_id")["line_index"]
        df["line"] = df["line_id"].map(line_map)

        # Map reference nodes (to standardize direction and preserve i/j)
        ref_i_map = la_ref_unique.set_index("line_id")["i"]
        ref_j_map = la_ref_unique.set_index("line_id")["j"]

        df["ref_i"] = df["line_id"].map(ref_i_map)
        df["ref_j"] = df["line_id"].map(ref_j_map)

        # 4. Handle Reverse Flows
        df = df.dropna(subset=["line", "ref_i", "ref_j"])
        is_reverse = df["i"] != df["ref_i"]
        df.loc[is_reverse, "values"] *= -1

        # 5. Aggregate duplicates
        df = df.groupby(["line", "line_id", "k", "rp", "ref_i", "ref_j"], as_index=False)["values"].mean()

        # 6. Final cleanup
        # Rename ref_i/ref_j back to i/j for the UI handler
        df = df.rename(columns={"ref_i": "i", "ref_j": "j"})
        df["line"] = df["line"].astype(int).astype(str)

        return df

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
    def _load_vsocp_ui(conn: sqlite3.Connection) -> pd.DataFrame:
        """Load voltage variable (vSOCP_ui)."""
        df = pd.read_sql_query("SELECT * FROM vSOCP_ui", conn)

        required_cols = ["rp", "k", "i", "values"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"vSOCP_ui missing required column: {col}")

        return df[required_cols]

    @staticmethod
    def _load_vstintrares(conn: sqlite3.Connection, gi: pd.DataFrame) -> pd.DataFrame:
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
        df = df.merge(gi[["g", "i"]], left_on="storageUnits", right_on="g", how="left").drop(columns=["g"])
        return df

    @staticmethod
    def _load_ppmax(conn: sqlite3.Connection, la: pd.DataFrame) -> pd.DataFrame:
        """
        Load line capacity parameter (pPmax) using vectorized operations.
        """
        print("  -> Loading pPmax...")
        df = pd.read_sql_query("SELECT * FROM pPmax", conn)

        # Rename columns: level_0 -> i, level_1 -> j, level_2 -> c
        rename_map = {"level_0": "i", "level_1": "j", "level_2": "c"}
        df = df.rename(columns=rename_map)

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # 1. Add canonical IDs to pPmax data
        df = h.add_canonical_line_ids(df, "i", "j")

        # 2. Prepare reference Lines (la) data
        la_ref = la.copy()
        la_ref = h.add_canonical_line_ids(la_ref, "i", "j")
        la_ref = la_ref.reset_index(drop=True)
        la_ref['line_index'] = la_ref.index

        # Handle parallel lines by keeping the first occurrence
        la_ref_unique = la_ref.drop_duplicates(subset=["line_id"], keep="first")

        # 3. Vectorized Map - Create the required columns
        line_map = la_ref_unique.set_index("line_id")["line_index"]
        ref_i_map = la_ref_unique.set_index("line_id")["i"]
        ref_j_map = la_ref_unique.set_index("line_id")["j"]

        # Apply the maps to create the new columns
        df["line"] = df["line_id"].map(line_map)
        df["ref_i"] = df["line_id"].map(ref_i_map)
        df["ref_j"] = df["line_id"].map(ref_j_map)

        # Drop rows where line mapping failed
        df = df.dropna(subset=["line", "ref_i", "ref_j"])

        # 4. Group by line index
        # We take the mean capacity if multiple entries exist for the same line (e.g. A->B and B->A)
        df = df.groupby(["line", "line_id", "ref_i", "ref_j"], as_index=False)["values"].mean()

        # Ensure line column is string for consistency
        df = df.rename(columns={"ref_i": "i", "ref_j": "j"})
        df["line"] = df["line"].astype(int).astype(str)

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


class V2GDataLoader(DataLoaderStrategy):
    """Data loader for V2G (Vehicle-to-Grid) SQLite database format.

    The V2G database has a different schema than the standard LEGO format:
    - Lines (la): from 'Branches' table (2 columns: from/to, no circuit)
    - Generator-node mapping (gi): from technology tables (PV_Buses, Wind_Buses, Hydro_Buses)
    - Coordinates: from 'lat' and 'lon' tables
    - vLineP/vLineQ: format level_0 (i), level_1 (j), level_2 (k), values - no rp, no circuit
    - pPmax: from 'pPmax_line' table
    - vGenP: from vProd_PV, vProd_Wind, vProd_Hydro tables
    - vStIntraRes: from 'vSOC_Batt' table
    - vSOCP: from 'vCii' table
    - EVs: from 'EVs', 'pAvailable', 'vDch_EV', 'vCh_EV', 'vSoc_EV' tables
    """

    # Technology mapping for V2G generator tables
    TECHNOLOGY_TABLES = {
        "PV_Buses": "Solar",
        "Wind_Buses": "Wind",
        "Hydro_Buses": "RoR",
    }

    def load(self, input_dir: str, tables: list[str]) -> LEGOData:
        """
        Load data from a V2G SQLite database with progress tracking.

        Args:
            input_dir: Path to the directory containing the V2G .sqlite file.
            tables: List of table names to load.

        Returns:
            LEGOData container with all loaded data.
        """
        print("--- Starting V2G Data Load ---")
        data = LEGOData()

        # Determine SQLite file path
        db_path = self._find_database(input_dir)
        print(f"Database found: {db_path}")

        with sqlite3.connect(db_path) as conn:
            # Load sets
            print("Loading Sets (i, k, rp, la)...")
            if "i" in tables:
                data.i = self._load_set(conn, "Buses")
            if "k" in tables:
                data.k = self._load_set(conn, "Time")
            if "rp" in tables:
                # V2G does not use representative periods - create single period DataFrame
                data.rp = pd.DataFrame({"values": ["rp01"]})
            if "la" in tables:
                data.la = self._load_lines(conn)

            # Load generator-node mapping with technology
            if "gi" in tables:
                print("Loading Generator Mappings (gi from technology tables)...")
                data.gi = self._load_gi(conn)
                # Also populate g (generators) from gi
                if not data.gi.empty:
                    data.g = pd.DataFrame({"values": data.gi["g"].unique()})

            # Load variables
            print("Loading Variables...")
            if "vLineP" in tables:
                print("  -> Loading vLineP...")
                data.vLineP = self._load_vline(conn, "vLineP", data.la)
            if "vLineQ" in tables:
                print("  -> Loading vLineQ...")
                data.vLineQ = self._load_vline(conn, "vLineQ", data.la)
            if "vGenP" in tables:
                print("  -> Loading vGenP (from technology production tables)...")
                data.vGenP = self._load_vgenp(conn)

            # Handle voltage - V2G uses vCii instead of vSOCP_cii/vSOCP_ui
            if "vSOCP_cii" in tables or "vSOCP_ui" in tables:
                print("  -> Loading vSOCP (from vCii)...")
                data.vSOCP = self._load_vsocp(conn)

            if "vStIntraRes" in tables:
                print("  -> Loading vStIntraRes (from vSOC_Batt)...")
                data.vStIntraRes = self._load_vstintrares(conn)

            # Load parameters
            print("Loading Parameters...")
            if "pPmax" in tables:
                print("  -> Loading pPmax (from pPmax_line)...")
                data.pPmax = self._load_ppmax(conn, data.la)

            # Load coordinates
            if "coords" in tables:
                print("Loading Coordinates (from lat/lon tables)...")
                data.coords = self._load_coords(conn)

            # Load voltage bounds
            if "voltage_bounds" in tables:
                print("Loading Voltage Bounds (from Vmax/Vmin)...")
                data.voltage_bounds = self._load_voltage_bounds(conn)

            # Load EV-specific data (V2G specific)
            if "ev" in tables:
                print("Loading EV Data...")
                data.ev = self._load_ev_set(conn)
                if "ev_availability" in tables:
                    print("  -> Loading EV availability (pAvailable)...")
                    data.ev_availability = self._load_ev_availability(conn)
                if "vDchEV" in tables:
                    print("  -> Loading vDch_EV...")
                    data.vDchEV = self._load_ev_discharge(conn)
                if "vChEV" in tables:
                    print("  -> Loading vCh_EV...")
                    data.vChEV = self._load_ev_charge(conn)
                if "vSocEV" in tables:
                    print("  -> Loading vSoc_EV...")
                    data.vSocEV = self._load_ev_soc(conn)

                # Post-process: Add node (i) column to EV discharge/charge data
                # by merging with ev_availability which contains the EV-node-time relationship
                # Only use rows where values==1 (EV is actually available at that node/time)
                if data.ev_availability is not None:
                    # Filter to only rows where EV is available (values == 1)
                    ev_avail_active = data.ev_availability[data.ev_availability["values"] == 1]
                    ev_avail_mapping = ev_avail_active[["ev", "i", "k", "rp"]].drop_duplicates()

                    if data.vDchEV is not None and not data.vDchEV.empty:
                        print("  -> Merging vDchEV with ev_availability to add node info...")
                        data.vDchEV = data.vDchEV.merge(
                            ev_avail_mapping,
                            on=["ev", "k", "rp"],
                            how="left"
                        )
                        # Report how many rows got a node assignment
                        assigned = data.vDchEV["i"].notna().sum()
                        print(f"     Node assigned to {assigned}/{len(data.vDchEV)} discharge records")

                    if data.vChEV is not None and not data.vChEV.empty:
                        print("  -> Merging vChEV with ev_availability to add node info...")
                        data.vChEV = data.vChEV.merge(
                            ev_avail_mapping,
                            on=["ev", "k", "rp"],
                            how="left"
                        )
                        assigned = data.vChEV["i"].notna().sum()
                        print(f"     Node assigned to {assigned}/{len(data.vChEV)} charge records")

        print("--- V2G Data Load Complete ---")
        return data

    @staticmethod
    def _find_database(input_dir: str) -> str:
        """Find the SQLite database file in the input directory."""
        # Check for common V2G database names
        for filename in ["v2g_results.sqlite", "model.sqlite", "result.sqlite"]:
            path = os.path.join(input_dir, filename)
            if os.path.exists(path):
                return path

        # If input_dir is the file itself
        if os.path.isfile(input_dir) and input_dir.endswith(".sqlite"):
            return input_dir

        raise FileNotFoundError(
            f"No SQLite database found in {input_dir}. "
            "Expected 'v2g_results.sqlite', 'model.sqlite', or 'result.sqlite'."
        )

    @staticmethod
    def _load_set(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
        """Load a set table and standardize column names."""
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        # Drop index column if present
        if "index" in df.columns:
            df = df.drop(columns=["index"])

        # Rename first column to 'values' (V2G uses '0' for set values)
        if "0" in df.columns:
            df = df.rename(columns={"0": "values"})

        return df

    @staticmethod
    def _load_lines(conn: sqlite3.Connection) -> pd.DataFrame:
        """Load line set (la) from Branches table.

        V2G Branches table has only 2 columns (from/to nodes), no circuit identifier.
        """
        df = pd.read_sql_query("SELECT * FROM Branches", conn)

        # Drop index column if present
        if "index" in df.columns:
            df = df.drop(columns=["index"])

        # Rename columns: 0 -> i (from), 1 -> j (to)
        rename_map = {"0": "i", "1": "j"}
        df = df.rename(columns=rename_map)

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # V2G has no circuit column - add default 'c1' for compatibility
        df["c"] = "c1"

        return df

    def _load_gi(self, conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load generator-node mapping from technology-specific tables.

        V2G stores generator-bus mappings in separate tables per technology:
        - PV_Buses: Solar generators
        - Wind_Buses: Wind generators
        - Hydro_Buses: Hydro generators

        Returns DataFrame with columns: g (generator name), i (bus), tec (technology)
        """
        all_gi = []

        for table_name, technology in self.TECHNOLOGY_TABLES.items():
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

                if df.empty:
                    continue

                # Drop index column if present
                if "index" in df.columns:
                    df = df.drop(columns=["index"])

                # The table has column '0' containing bus names
                # Generator name is derived from technology + bus
                if "0" in df.columns:
                    df = df.rename(columns={"0": "i"})

                # Create generator name: technology_bus (e.g., "PV_Node_0")
                prefix = table_name.replace("_Buses", "")
                df["g"] = prefix + "_" + df["i"].astype(str)
                df["tec"] = technology

                all_gi.append(df[["g", "i", "tec"]])

            except Exception as e:
                print(f"  Warning: Could not load {table_name}: {e}")
                continue

        if all_gi:
            return pd.concat(all_gi, ignore_index=True)
        else:
            return pd.DataFrame(columns=["g", "i", "tec"])

    @staticmethod
    def _load_vline(conn: sqlite3.Connection, table_name: str, la: pd.DataFrame) -> pd.DataFrame:
        """
        Load line flow variable (vLineP or vLineQ) for V2G format.

        V2G format: level_0 (i), level_1 (j), level_2 (k), values
        No representative periods (rp), no circuit column.
        """
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

        # V2G column mapping: level_0=i (from), level_1=j (to), level_2=k (time)
        rename_map = {
            "level_0": "i",
            "level_1": "j",
            "level_2": "k"
        }
        df = df.rename(columns=rename_map)

        # Add default rp column for compatibility with existing workflow
        df["rp"] = "rp01"

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # 1. Add canonical IDs
        df = h.add_canonical_line_ids(df, "i", "j")

        # 2. Prepare reference Lines (la) data
        la_ref = la.copy()
        la_ref = h.add_canonical_line_ids(la_ref, "i", "j")
        la_ref = la_ref.reset_index(drop=True)
        la_ref['line_index'] = la_ref.index

        # Handle parallel lines (though V2G typically doesn't have them)
        la_ref_unique = la_ref.drop_duplicates(subset=["line_id"], keep="first")

        # 3. Vectorized Map
        line_map = la_ref_unique.set_index("line_id")["line_index"]
        df["line"] = df["line_id"].map(line_map)

        # Map reference nodes
        ref_i_map = la_ref_unique.set_index("line_id")["i"]
        ref_j_map = la_ref_unique.set_index("line_id")["j"]

        df["ref_i"] = df["line_id"].map(ref_i_map)
        df["ref_j"] = df["line_id"].map(ref_j_map)

        # 4. Handle Reverse Flows
        df = df.dropna(subset=["line", "ref_i", "ref_j"])
        is_reverse = df["i"] != df["ref_i"]
        df.loc[is_reverse, "values"] *= -1

        # 5. Aggregate duplicates
        df = df.groupby(["line", "line_id", "k", "rp", "ref_i", "ref_j"], as_index=False)["values"].mean()

        # 6. Final cleanup
        df = df.rename(columns={"ref_i": "i", "ref_j": "j"})
        df["line"] = df["line"].astype(int).astype(str)

        return df

    @staticmethod
    def _load_vgenp(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load generator power from technology-specific production tables.

        V2G stores generation in separate tables:
        - vProd_PV: columns PV_Buses, Time, values
        - vProd_Wind: columns Wind_Buses, Time, values (if not empty)
        - vProd_Hydro: columns Hydro_Buses, Time, values (if not empty)

        Returns unified DataFrame with columns: rp, k, g, values
        """
        all_vgenp = []

        # Mapping of table name to (bus column name, technology prefix)
        production_tables = {
            "vProd_PV": ("PV_Buses", "PV"),
            "vProd_Wind": ("Wind_Buses", "Wind"),
            "vProd_Hydro": ("Hydro_Buses", "Hydro"),
        }

        for table_name, (bus_col, prefix) in production_tables.items():
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

                if df.empty or len(df.columns) <= 2:
                    continue

                # Expected columns: bus_col, Time, values
                if bus_col in df.columns and "Time" in df.columns and "values" in df.columns:
                    # Create generator name from bus
                    df["g"] = prefix + "_" + df[bus_col].astype(str)
                    df["k"] = df["Time"]
                    df["rp"] = "rp01"  # V2G has no representative periods

                    all_vgenp.append(df[["rp", "k", "g", "values"]])

            except Exception as e:
                print(f"  Warning: Could not load {table_name}: {e}")
                continue

        if all_vgenp:
            return pd.concat(all_vgenp, ignore_index=True)
        else:
            return pd.DataFrame(columns=["rp", "k", "g", "values"])

    @staticmethod
    def _load_vsocp(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load voltage variable from vCii table.

        V2G uses vCii instead of vSOCP_cii/vSOCP_ui.
        vCii columns: Buses, Time, values

        Returns DataFrame with columns: rp, k, i, values
        """
        df = pd.read_sql_query("SELECT * FROM vCii", conn)

        # Rename columns to match expected format
        df = df.rename(columns={"Buses": "i", "Time": "k"})
        df["rp"] = "rp01"  # V2G has no representative periods

        return df[["rp", "k", "i", "values"]]

    @staticmethod
    def _load_vstintrares(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load storage state of charge from vSOC_Batt table.

        V2G vSOC_Batt columns: Buses, Time, values

        Returns DataFrame with columns: rp, k, storageUnits, i, values
        """
        df = pd.read_sql_query("SELECT * FROM vSOC_Batt", conn)

        # Rename columns to match expected format
        df = df.rename(columns={"Buses": "i", "Time": "k"})
        df["rp"] = "rp01"

        # In V2G, battery storage is identified by bus location
        # Create storageUnits name from bus
        df["storageUnits"] = "BESS_" + df["i"].astype(str)

        return df[["rp", "k", "storageUnits", "i", "values"]]

    @staticmethod
    def _load_ppmax(conn: sqlite3.Connection, la: pd.DataFrame) -> pd.DataFrame:
        """
        Load line capacity parameter from pPmax_line table.

        V2G pPmax_line columns: level_0 (i), level_1 (j), values
        No circuit column.
        """
        df = pd.read_sql_query("SELECT * FROM pPmax_line", conn)

        # Rename columns
        rename_map = {"level_0": "i", "level_1": "j"}
        df = df.rename(columns=rename_map)

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # 1. Add canonical IDs
        df = h.add_canonical_line_ids(df, "i", "j")

        # 2. Prepare reference Lines (la) data
        la_ref = la.copy()
        la_ref = h.add_canonical_line_ids(la_ref, "i", "j")
        la_ref = la_ref.reset_index(drop=True)
        la_ref['line_index'] = la_ref.index

        la_ref_unique = la_ref.drop_duplicates(subset=["line_id"], keep="first")

        # 3. Vectorized Map
        line_map = la_ref_unique.set_index("line_id")["line_index"]
        ref_i_map = la_ref_unique.set_index("line_id")["i"]
        ref_j_map = la_ref_unique.set_index("line_id")["j"]

        df["line"] = df["line_id"].map(line_map)
        df["ref_i"] = df["line_id"].map(ref_i_map)
        df["ref_j"] = df["line_id"].map(ref_j_map)

        # Drop rows where line mapping failed
        df = df.dropna(subset=["line", "ref_i", "ref_j"])

        # 4. Group by line
        df = df.groupby(["line", "line_id", "ref_i", "ref_j"], as_index=False)["values"].mean()

        df = df.rename(columns={"ref_i": "i", "ref_j": "j"})
        df["line"] = df["line"].astype(int).astype(str)

        return df

    @staticmethod
    def _load_coords(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load node coordinates from lat and lon tables.

        V2G format:
        - lat: columns Buses, values
        - lon: columns Buses, values

        Returns DataFrame with columns: values (bus name), lat, lon
        """
        try:
            df_lat = pd.read_sql_query("SELECT * FROM lat", conn)
            df_lon = pd.read_sql_query("SELECT * FROM lon", conn)

            # Rename columns - V2G uses 'Buses' as identifier
            df_lat = df_lat.rename(columns={"Buses": "values", "values": "lat"})
            df_lon = df_lon.rename(columns={"Buses": "values", "values": "lon"})

            # Ensure string type for node identifier
            df_lat["values"] = df_lat["values"].astype(str)
            df_lon["values"] = df_lon["values"].astype(str)

            # Merge on node identifier
            df_coords = pd.merge(df_lat[["values", "lat"]], df_lon[["values", "lon"]],
                                 on="values", how="inner")

            if df_coords.empty:
                raise ValueError("Resulting coordinates table is empty after merge.")

            return df_coords

        except Exception as e:
            raise ValueError(
                f"Error loading coordinates: {e}. "
                "Ensure 'lat' and 'lon' tables exist with 'Buses' and 'values' columns."
            )

    @staticmethod
    def _load_voltage_bounds(conn: sqlite3.Connection) -> pd.DataFrame:
        """Load voltage bounds from Vmax and Vmin tables."""
        try:
            df_max = pd.read_sql_query("SELECT * FROM Vmax", conn)
            df_min = pd.read_sql_query("SELECT * FROM Vmin", conn)

            # Identify bus column (could be 'Buses', 'index', or first column)
            def get_bus_col(df):
                if "Buses" in df.columns:
                    return "Buses"
                elif "index" in df.columns:
                    return "index"
                return df.columns[0]

            max_bus_col = get_bus_col(df_max)
            min_bus_col = get_bus_col(df_min)

            # Standardize column names
            df_max = df_max.rename(columns={max_bus_col: "values", "values": "pBusMaxV"})
            df_min = df_min.rename(columns={min_bus_col: "values", "values": "pBusMinV"})

            # Merge on node name
            df = df_max[["values", "pBusMaxV"]].merge(
                df_min[["values", "pBusMinV"]], on="values", how="outer"
            )
            df = df.set_index("values")

            return df

        except Exception as e:
            print(f"Warning: Could not load voltage bounds: {e}")
            return None

    # =========================================================================
    # EV-specific loading methods (V2G only)
    # =========================================================================

    @staticmethod
    def _load_ev_set(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load EV set from EVs table.

        EVs table columns: index, 0 (EV name)

        Returns DataFrame with columns: values (EV identifier)
        """
        df = pd.read_sql_query("SELECT * FROM EVs", conn)

        # Drop index column if present
        if "index" in df.columns:
            df = df.drop(columns=["index"])

        # Rename first column to 'values'
        if "0" in df.columns:
            df = df.rename(columns={"0": "values"})

        return df

    @staticmethod
    def _load_ev_availability(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load EV availability from pAvailable table.

        pAvailable columns: EVs, Buses, Time, values
        This table relates which EV is available at which node at which time.

        Returns DataFrame with columns: ev, i, k, rp, values
        """
        df = pd.read_sql_query("SELECT * FROM pAvailable", conn)

        # Rename columns to match LEGO conventions
        df = df.rename(columns={
            "EVs": "ev",
            "Buses": "i",
            "Time": "k"
        })
        df["rp"] = "rp01"

        return df[["ev", "i", "k", "rp", "values"]]

    @staticmethod
    def _load_ev_discharge(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load EV discharge from vDch_EV table.

        vDch_EV columns: EVs, Time, values

        Returns DataFrame with columns: ev, k, rp, values
        """
        df = pd.read_sql_query("SELECT * FROM vDch_EV", conn)

        df = df.rename(columns={
            "EVs": "ev",
            "Time": "k"
        })
        df["rp"] = "rp01"

        return df[["ev", "k", "rp", "values"]]

    @staticmethod
    def _load_ev_charge(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load EV charge from vCh_EV table.

        vCh_EV columns: EVs, Time, values

        Returns DataFrame with columns: ev, k, rp, values
        """
        df = pd.read_sql_query("SELECT * FROM vCh_EV", conn)

        df = df.rename(columns={
            "EVs": "ev",
            "Time": "k"
        })
        df["rp"] = "rp01"

        return df[["ev", "k", "rp", "values"]]

    @staticmethod
    def _load_ev_soc(conn: sqlite3.Connection) -> pd.DataFrame:
        """
        Load EV state of charge from vSoc_EV table.

        vSoc_EV columns: EVs, Time, values

        Returns DataFrame with columns: ev, k, rp, values
        """
        df = pd.read_sql_query("SELECT * FROM vSoc_EV", conn)

        df = df.rename(columns={
            "EVs": "ev",
            "Time": "k"
        })
        df["rp"] = "rp01"

        return df[["ev", "k", "rp", "values"]]


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
        ValueError: If the input_type is not "sqlite" or "V2G" or "excel".

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
    elif obj.input_type == "V2G":
        loader = V2GDataLoader()
    elif obj.input_type == "excel":
        print("--- DEPRECATED: Excel Data Loader (Legacy Support) ---")
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
    if data.vSOCP is not None and not data.vSOCP.empty:
        obj.vSOCP= data.vSOCP
    if data.vStIntraRes is not None and not data.vStIntraRes.empty:
        obj.vStIntraRes = data.vStIntraRes

    # Parameters
    if not data.pPmax.empty:
        obj.pPmax = data.pPmax
    if not data.coords.empty:
        obj.coords = data.coords
    if data.voltage_bounds is not None and not data.voltage_bounds.empty:
        obj.voltage_bounds = data.voltage_bounds

    # V2G-specific: Electric Vehicles
    if not data.ev.empty:
        obj.ev = data.ev
    if data.ev_availability is not None and not data.ev_availability.empty:
        obj.ev_availability = data.ev_availability
    if data.vDchEV is not None and not data.vDchEV.empty:
        obj.vDchEV = data.vDchEV
    if data.vChEV is not None and not data.vChEV.empty:
        obj.vChEV = data.vChEV
    if data.vSocEV is not None and not data.vSocEV.empty:
        obj.vSocEV = data.vSocEV


def _postprocess_data(obj) -> None:
    """Apply common post-processing to loaded data with progress logging."""
    print("Starting Post-processing...")

    # Merge coordinates into node info
    if hasattr(obj, "i") and hasattr(obj, "coords"):
        print("  -> Merging coordinates...")
        obj.i = pd.merge(
            obj.i,
            obj.coords,
            left_on="values",
            right_on="values",
            how="left"
        )

    # Add voltage bounds to node info
    if hasattr(obj, "voltage_bounds") and obj.voltage_bounds is not None:
        print("  -> Merging voltage bounds...")
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
    print("  -> Computing relative line flows...")
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

    print("--- Post-processing Complete ---")


def _add_relative_line_values(vline_df: pd.DataFrame, ppmax_df: pd.DataFrame) -> None:
    """Add relative values and pPmax to line flow dataframe."""
    ppmax_map = ppmax_df.set_index("line_id")["values"]

    vline_df["rel_values"] = abs(vline_df["values"]) / vline_df["line_id"].map(ppmax_map)
    vline_df["pPmax"] = vline_df["line_id"].map(ppmax_map)
