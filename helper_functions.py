"""
Helper Functions Module for LEGO-GPT

This module provides utility functions for configuration loading, data extraction,
and common operations used throughout the application.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd


# =============================================================================
# Line ID Utilities
# =============================================================================

def add_canonical_line_ids(
        df: pd.DataFrame,
        i_col: str = "i",
        j_col: str = "j"
) -> pd.DataFrame:
    """
    Add a canonical line identifier column to a dataframe containing node pairs.

    The canonical ID is direction-independent, always using alphabetical ordering
    of node names to create a consistent identifier regardless of flow direction.

    Args:
        df: DataFrame containing node pair columns.
        i_col: Name of the 'from' node column.
        j_col: Name of the 'to' node column.

    Returns:
        DataFrame with added 'line_id' column.

    Example:
        >>> df = pd.DataFrame({'i': ['A', 'B'], 'j': ['B', 'A']})
        >>> df = add_canonical_line_ids(df)
        >>> df['line_id'].tolist()
        ['A_B', 'A_B']
    """
    i_str = df[i_col].astype(str)
    j_str = df[j_col].astype(str)

    df["line_id"] = np.where(
        i_str < j_str,
        i_str + '_' + j_str,
        j_str + '_' + i_str
    )

    return df


def build_line_index(df: pd.DataFrame) -> tuple[dict, list]:
    """
    Build a mapping from node pairs to unique line indices.

    Args:
        df: DataFrame with 'i' and 'j' columns.

    Returns:
        Tuple of (line_index_dict, line_list) where:
            - line_index_dict maps frozenset(i, j) to index
            - line_list contains [i, j] pairs in order
    """
    line_index_dict = {}
    line_list = []

    for _, row in df.iterrows():
        key = frozenset([str(row["i"]), str(row["j"])])
        if key not in line_index_dict:
            line_index_dict[key] = len(line_list)
            line_list.append([str(row["i"]), str(row["j"])])

    return line_index_dict, line_list


def assign_line_indices(
        df: pd.DataFrame,
        line_index_dict: dict,
        line_list: list
) -> pd.DataFrame:
    """
    Assign line indices and detect duplicates in a DataFrame.

    Args:
        df: DataFrame with 'i' and 'j' columns.
        line_index_dict: Mapping from node pairs to indices.
        line_list: List of [i, j] pairs.

    Returns:
        DataFrame with 'line' and 'duplicate' columns added.
    """
    line_indices = []
    duplicates = []

    for _, row in df.iterrows():
        key = frozenset([str(row["i"]), str(row["j"])])
        idx = line_index_dict.get(key, -1)
        line_indices.append(idx)

        # Check if this is a reverse direction (duplicate)
        if idx >= 0 and idx < len(line_list):
            original = line_list[idx]
            is_dup = [str(row["i"]), str(row["j"])] != original
        else:
            is_dup = False
        duplicates.append(is_dup)

    df["line"] = line_indices
    df["duplicate"] = duplicates
    df["line"] = df["line"].astype(str)

    return df


# =============================================================================
# Configuration Utilities
# =============================================================================

def copy_default_config(
        config_path: str = "config.yml",
        default_config_path: str = "config_template.yml"
) -> None:
    """
    Copy default configuration template to specified path if it doesn't exist.

    Args:
        config_path: Destination path for configuration file.
        default_config_path: Source path for template file.
    """
    if os.path.exists(config_path):
        print(f"Configuration file already exists at {config_path}")
        return

    if not os.path.exists(default_config_path):
        raise FileNotFoundError(f"Configuration file not found: {default_config_path}")

    with open(default_config_path, 'r') as f:
        config_content = f.read()

    with open(config_path, 'w') as f:
        f.write(config_content)

    print(f"Copied default configuration to {config_path}")
    print("Please edit the configuration file with your settings, then run again.")


# =============================================================================
# Excel Data Extraction Configuration
# =============================================================================

@dataclass
class ExcelColumnConfig:
    """Configuration for Excel column extraction."""
    filename: str
    sheet_name: Optional[str] = None
    skiprows: int = 7
    usecols: str = "C"
    column_names: Optional[list[str]] = None
    header: Optional[int] = None


# Default Excel configurations for each table type
EXCEL_CONFIGS: dict[str, ExcelColumnConfig] = {
    "i": ExcelColumnConfig(
        filename="Power_BusInfo.xlsx",
        usecols="C",
        column_names=["values"]
    ),
    "rp": ExcelColumnConfig(
        filename="Power_WeightsRP.xlsx",
        usecols="C",
        column_names=["values"]
    ),
    "k": ExcelColumnConfig(
        filename="Power_WeightsK.xlsx",
        usecols="C",
        column_names=["values"]
    ),
    "coords": ExcelColumnConfig(
        filename="Power_BusInfo.xlsx",
        usecols="C,M,N",
        column_names=["values", "lat", "lon"]
    ),
    "voltage_bounds": ExcelColumnConfig(
        filename="Power_BusInfo.xlsx",
        usecols="C,F,G",
        column_names=["values", "pBusMaxV", "pBusMinV"]
    ),
    "pPmax": ExcelColumnConfig(
        filename="Power_Network.xlsx",
        usecols="C,D,K",
        column_names=["i", "j", "values"]
    ),
}


# =============================================================================
# Excel Data Extraction
# =============================================================================

class ExcelExtractor:
    """Handles extraction of data from Excel files."""

    def __init__(self, input_dir: str):
        """
        Initialize the Excel extractor.

        Args:
            input_dir: Directory containing input Excel files.
        """
        self.input_dir = Path(input_dir)

    def _get_filepath(self, filename: str) -> Path:
        """Get full path for a filename."""
        return self.input_dir / filename

    def _file_exists(self, filename: str) -> bool:
        """Check if a file exists."""
        return self._get_filepath(filename).exists()

    def _read_excel(
            self,
            config: ExcelColumnConfig,
            **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        Read an Excel file with the given configuration.

        Args:
            config: Excel column configuration.
            **kwargs: Additional arguments to pass to pd.read_excel.

        Returns:
            DataFrame or None if file doesn't exist.
        """
        filepath = self._get_filepath(config.filename)

        if not filepath.exists():
            print(f"Warning: File not found: {filepath}")
            return None

        try:
            df = pd.read_excel(
                filepath,
                sheet_name=config.sheet_name or 0,
                skiprows=config.skiprows,
                usecols=config.usecols,
                header=config.header,
                **kwargs
            )

            if config.column_names:
                df.columns = config.column_names

            return df

        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None

    def extract_set(self, table: str) -> Optional[pd.DataFrame]:
        """
        Extract a set table (i, rp, k).

        Args:
            table: Table name.

        Returns:
            DataFrame with 'values' column.
        """
        config = EXCEL_CONFIGS.get(table)
        if config is None:
            print(f"No configuration for table: {table}")
            return None

        df = self._read_excel(config)
        if df is not None:
            df = df.drop_duplicates()

        return df

    def extract_bus_info(self) -> Optional[pd.DataFrame]:
        """Extract bus information (nodes)."""
        return self.extract_set("i")

    def extract_rep_periods(self) -> Optional[pd.DataFrame]:
        """Extract representative periods."""
        return self.extract_set("rp")

    def extract_time_steps(self) -> Optional[pd.DataFrame]:
        """Extract time steps."""
        return self.extract_set("k")

    def extract_coordinates(self) -> Optional[pd.DataFrame]:
        """Extract node coordinates."""
        config = EXCEL_CONFIGS["coords"]
        df = self._read_excel(config)

        if df is not None:
            df = df.drop_duplicates(subset=["values"])

        return df

    def extract_voltage_bounds(self) -> Optional[pd.DataFrame]:
        """Extract voltage bounds."""
        config = EXCEL_CONFIGS["voltage_bounds"]
        df = self._read_excel(config)

        if df is not None:
            df = df.drop_duplicates(subset=["values"])
            df = df.set_index("values")

        return df

    def extract_generator_info(self) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Extract generator-node mapping with technology.

        Returns:
            Tuple of (gi DataFrame, g DataFrame).
        """
        filenames = ["Power_VRES.xlsx", "Power_Storage.xlsx"]
        all_data = []

        for filename in filenames:
            filepath = self._get_filepath(filename)
            if not filepath.exists():
                continue

            try:
                df = pd.read_excel(
                    filepath,
                    skiprows=7,
                    usecols="C,D,E",
                    header=None
                )
                df.columns = ["g", "tec", "i"]
                all_data.append(df)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

        if not all_data:
            return None, None

        gi = pd.concat(all_data, ignore_index=True)
        gi = gi.drop_duplicates()

        g = gi[["g"]].drop_duplicates().reset_index(drop=True)
        g.columns = ["values"]

        return gi, g

    def extract_line_flow(
            self,
            variable: str = "vLineP"
    ) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Extract line power flow data.

        Args:
            variable: Variable name ("vLineP" or "vLineQ").

        Returns:
            Tuple of (flow DataFrame, lines DataFrame).
        """
        filepath = self._get_filepath("model.xlsx")
        if not filepath.exists():
            print(f"Warning: File not found: {filepath}")
            return None, None

        try:
            df = pd.read_excel(filepath, sheet_name=variable)
        except Exception as e:
            print(f"Error reading {variable} from {filepath}: {e}")
            return None, None

        # Standardize column names
        df.columns = ["rp", "k", "i", "j", "c", variable]
        df = df.rename(columns={variable: "values"})

        # Ensure string types for node columns
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # Add canonical line identifier
        df = add_canonical_line_ids(df, "i", "j")

        # Build line index and assign
        line_index_dict, line_list = build_line_index(df)
        df = assign_line_indices(df, line_index_dict, line_list)

        # Create lines DataFrame
        df_lines = pd.DataFrame(line_list, columns=["i", "j"])

        return df, df_lines

    def extract_gen_power(self) -> Optional[pd.DataFrame]:
        """Extract generator power variable."""
        filepath = self._get_filepath("model.xlsx")
        if not filepath.exists():
            return None

        try:
            df = pd.read_excel(filepath, sheet_name="vGenP")
            df.columns = ["rp", "k", "g", "vGenP"]
            df = df.rename(columns={"vGenP": "values"})
            return df[["rp", "k", "g", "values"]]
        except Exception as e:
            print(f"Error reading vGenP: {e}")
            return None

    def extract_voltage_socp(self) -> Optional[pd.DataFrame]:
        """Extract SOCP voltage values."""
        filepath = self._get_filepath("model.xlsx")
        if not filepath.exists():
            return None

        try:
            df = pd.read_excel(filepath, sheet_name="vSOCP_cii")
            df.columns = ["rp", "k", "i", "vSOCP_cii"]
            df = df.rename(columns={"vSOCP_cii": "values"})
            return df[["rp", "k", "i", "values"]]
        except Exception as e:
            print(f"Error reading vSOCP_cii: {e}")
            return None

    def extract_line_capacity(self) -> Optional[pd.DataFrame]:
        """Extract line capacity parameter."""
        config = EXCEL_CONFIGS["pPmax"]
        df = self._read_excel(config)

        if df is None:
            return None

        # Ensure string types
        df["i"] = df["i"].astype(str)
        df["j"] = df["j"].astype(str)

        # Add canonical line identifier
        df = add_canonical_line_ids(df, "i", "j")

        # Build line index
        line_index_dict, line_list = build_line_index(df)
        df = assign_line_indices(df, line_index_dict, line_list)

        # Average values for same line (different circuits)
        df = df.groupby("line_id", as_index=False).agg({
            "values": "mean",
            "line": "first"
        })

        return df

    def extract_storage_soc(self) -> Optional[pd.DataFrame]:
        """Extract storage state of charge."""
        filepath = self._get_filepath("model.xlsx")
        if not filepath.exists():
            return None

        try:
            df = pd.read_excel(filepath, sheet_name="vStIntraRes")
            df.columns = ["rp", "k", "storageUnits", "vStIntraRes"]
            df = df.rename(columns={"vStIntraRes": "values"})
            return df[["rp", "k", "storageUnits", "values"]]
        except Exception as e:
            print(f"Error reading vStIntraRes: {e}")
            return None


# =============================================================================
# Legacy API (Backward Compatibility)
# =============================================================================

def extract_excel_to_dataframe(
        input_dir: str,
        table: str
) -> Union[pd.DataFrame, tuple, None]:
    """
    Extract data from Excel files into a pandas DataFrame.

    This function provides backward compatibility with the original API.

    Args:
        input_dir: Directory containing input Excel files.
        table: Type of table to extract.

    Returns:
        DataFrame or tuple of DataFrames depending on table type.
    """
    extractor = ExcelExtractor(input_dir)

    if table == "i":
        return extractor.extract_bus_info()

    elif table == "rp":
        return extractor.extract_rep_periods()

    elif table == "k":
        return extractor.extract_time_steps()

    elif table == "gi":
        return extractor.extract_generator_info()

    elif table == "coords":
        return extractor.extract_coordinates()

    elif table == "voltage_bounds":
        return extractor.extract_voltage_bounds()

    elif table == "vLineP":
        return extractor.extract_line_flow("vLineP")

    elif table == "vLineQ":
        return extractor.extract_line_flow("vLineQ")

    elif table == "vGenP":
        return extractor.extract_gen_power()

    elif table == "vSOCP_cii":
        return extractor.extract_voltage_socp()

    elif table == "pPmax":
        return extractor.extract_line_capacity()

    elif table == "vStIntraRes":
        return extractor.extract_storage_soc()

    else:
        print(f"Table '{table}' not implemented or invalid.")
        return None
