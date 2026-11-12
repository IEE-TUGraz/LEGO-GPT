"""
Helper Functions Module for LEGO-GPT

This module provides utility functions for line identifiers and configuration handling
used throughout the application.
"""

import os

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
