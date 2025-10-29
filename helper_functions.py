import os
import sqlite3
from typing import Optional

import pandas as pd
import yaml


def add_canonical_line_ids(df: pd.DataFrame, i_col: str = "i", j_col: str = "j") -> pd.DataFrame:
    """Adds a canonical line identifier column to a dataframe containing node pairs."""
    import numpy as np

    # Convert to string to ensure consistent comparison
    i_str = df[i_col].astype(str)
    j_str = df[j_col].astype(str)

    # Vectorized comparison and concatenation
    df["line_id"] = np.where(
        i_str < j_str,
        i_str + '_' + j_str,
        j_str + '_' + i_str
    )

    return df


def extract_table_to_dataframe(con: sqlite3.Connection, table_name: str) -> Optional[pd.DataFrame]:
    """
    Extracts the contents of a database table into a pandas DataFrame.
    Args:
        con (sqlite3.Connection): 
            The database connection object.
        table_name (str): 
            The name of the table to extract data from.
    Returns:
        pandas.DataFrame: 
            A DataFrame containing the data from the specified table, 
            or None if an error occurs.
    Raises:
        Exception: 
            If there is an issue with the database query or connection, 
            an exception is caught and an error message is printed.
    """
    try:
        # Query the table
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, con)

        return df

    except Exception as e:
        print(f"Error extracting table {table_name}: {e}")
        return None


def extract_excel_to_dataframe(input_dir: str, table: str) -> pd.DataFrame | tuple:
    """
    Extract data from Excel files into a pandas DataFrame based on the specified table type.
    This function processes various Excel files and sheets, extracting and transforming data
    into pandas DataFrames according to the provided `table` parameter. The function supports
    multiple table types, each corresponding to a specific data extraction and transformation logic.

    Parameters:

        input_dir (str): The directory containing the input Excel files.
        table (str): The type of table to extract. Supported values are:

            - "i": Extracts data from "Power_BusInfo.xlsx".
            - "rp": Extracts unique values from "Power_WeightsRP.xlsx".
            - "k": Extracts unique values from "Power_WeightsK.xlsx".
            - "gi": Combines data from multiple Excel files ("Power_VRES", "Power_ThermalGen",
              "Power_Storage", "Power_RoR") into a DataFrame with columns "g" and "i".
            - "vLineP": Processes line data from "model.xlsx" (sheet "vLineP") and returns
              two DataFrames: one for the main data and one for line tuples.
            - "coords": Extracts coordinates (longitude and latitude) from "Power_BusInfo.xlsx".
            - "vGenP": Processes generator data from "model.xlsx" into a long-format DataFrame.
            - "pPmax": Extracts power network data from "Power_Network.xlsx".
            - "pDemand": Placeholder for future implementation.

    Returns:

        pandas.DataFrame or tuple:
            - For most table types, returns a single DataFrame containing the extracted data.
            - For "vLineP", returns a tuple of two DataFrames: (main data, line tuples).
            - For "gi", returns a tuple of two DataFrames: (main data, unique "g" values).
            - Returns None if the table type is invalid or not yet implemented.
    Note:

        - The function uses hardcoded file and sheet names for specific table types.
        - Some table types include additional preprocessing steps, such as removing duplicates or resetting the index.

    Raises:
        FileNotFoundError: If the specified Excel files or sheets are not found.
        ValueError: If the table type is invalid or not supported.
    """

    df, df_lines, df_g = None, None, None

    if table == "i":
        filename = os.path.join(input_dir, "Power_BusInfo.xlsx")
        skiprows = 7
        use_cols = "C"
        df = pd.read_excel(filename, skiprows=skiprows, usecols=use_cols, header=None)
        df.columns = ["values"]
        df = df.drop_duplicates()

    elif table == "rp":
        filename = os.path.join(input_dir, "Power_WeightsRP.xlsx")
        skiprows = 7
        use_cols = "C"
        df = pd.read_excel(filename, skiprows=skiprows, usecols=use_cols, header=None)
        df.columns = ["values"]
        df = df.drop_duplicates()

    elif table == "k":
        filename = os.path.join(input_dir, "Power_WeightsK.xlsx")
        skiprows = 7
        use_cols = "C"
        df = pd.read_excel(filename, skiprows=skiprows, usecols=use_cols, header=None)
        df.columns = ["values"]
        df = df.drop_duplicates()

    elif table == "gi":
        filenames = [os.path.join(input_dir, tech + ".xlsx") for tech in
                     ["Power_VRES", "Power_ThermalGen", "Power_Storage"]]  # TODO: Power_ROR?
        skiprows = 7
        use_cols = "C,D,E"
        df = pd.DataFrame(columns=["g", "tec", "i"])
        for filename in filenames:
            temp_df = pd.read_excel(filename, skiprows=skiprows, usecols=use_cols, header=None)
            temp_df.columns = ["g", "tec", "i"]
            df = pd.concat([df, temp_df], ignore_index=True)
        # reset index
        df.reset_index(drop=True, inplace=True)
        df_g = df[["g"]].drop_duplicates().reset_index(drop=True)

    elif table == "coords":
        filename = os.path.join(input_dir, "Power_BusInfo.xlsx")
        start_row = 7
        use_cols = "C,M,N"
        df = pd.read_excel(filename, skiprows=start_row, usecols=use_cols, header=None)
        df.columns = ["values", "lat", "lon"]
        # set index to i
        df.set_index("values", inplace=True)

    elif table == "voltage_bounds":
        filename = os.path.join(input_dir, "Power_BusInfo.xlsx")
        start_row = 7
        use_cols = "C,F,G"  # Columns C (bus name), F (max V), G (min V)
        df = pd.read_excel(filename, skiprows=start_row, usecols=use_cols, header=None)
        df.columns = ["values", "pBusMaxV", "pBusMinV"]
        df.set_index("values", inplace=True)  # Set bus name as index

    elif table == "vLineP":
        filename = os.path.join(input_dir, "model.xlsx")
        sheet_name = "vLineP"

        # Load the data
        df = pd.read_excel(filename, sheet_name=sheet_name)

        # Standardize column names
        df.columns = ["rp", "k", "i", "j", "c", "vLineP"]

        df = df.rename(columns={"vLineP": "values"})

        # Add canonical line identifier for safe merging with pPmax
        df = add_canonical_line_ids(df, "i", "j")

        # Generate unique line index (direction-insensitive) - kept for backward compatibility
        line_index_dict = {}
        line_list = []
        line_indices = []
        for idx, row in df.iterrows():
            ij_key = frozenset([row["i"], row["j"]])
            if ij_key not in line_index_dict:
                line_index_dict[ij_key] = len(line_index_dict)
                line_list.append([row["i"], row["j"]])
            line_indices.append(line_index_dict[ij_key])

        df["line"] = line_indices

        # Detect duplicates (direction differences)
        df["duplicate"] = [
            [row.i, row.j] != line_list[df.loc[idx, "line"]]
            for idx, row in df.iterrows()
        ]

        # Rename for consistency with other tables
        df_lines = pd.DataFrame(line_list, columns=["i", "j"])

    elif table == "vLineQ":
        filename = os.path.join(input_dir, "model.xlsx")
        sheet_name = "vLineQ"

        # Load the data
        df = pd.read_excel(filename, sheet_name=sheet_name)

        # Standardize column names
        df.columns = ["rp", "k", "i", "j", "c", "vLineQ"]

        df = df.rename(columns={"vLineQ": "values"})

        # Add canonical line identifier for safe merging with pPmax
        df = add_canonical_line_ids(df, "i", "j")

        # Generate unique line index (direction-insensitive) - kept for backward compatibility
        line_index_dict = {}
        line_list = []
        line_indices = []
        for idx, row in df.iterrows():
            ij_key = frozenset([row["i"], row["j"]])
            if ij_key not in line_index_dict:
                line_index_dict[ij_key] = len(line_index_dict)
                line_list.append([row["i"], row["j"]])
            line_indices.append(line_index_dict[ij_key])

        df["line"] = line_indices

        # Detect duplicates (direction differences)
        df["duplicate"] = [
            [row.i, row.j] != line_list[df.loc[idx, "line"]]
            for idx, row in df.iterrows()
        ]

        # Rename for consistency with other tables
        df_lines = pd.DataFrame(line_list, columns=["i", "j"])

    elif table == "vGenP":
        filename = os.path.join(input_dir, "model.xlsx")
        sheet_name = "vGenP"

        # Load the data
        df = pd.read_excel(filename, sheet_name=sheet_name)

        # Standardize column names
        df.columns = ["rp", "k", "g", "vGenP"]

        # Rename for consistency with other tables
        df = df.rename(columns={"vGenP": "values"})
        df = df[["rp", "k", "g", "values"]]

    elif table == "vSOCP_cii":
        filename = os.path.join(input_dir, "model.xlsx")
        sheet_name = "vSOCP_cii"

        # Load the data
        df = pd.read_excel(filename, sheet_name=sheet_name)

        # Standardize column names based on the provided format
        df.columns = ["rp", "k", "i", "vSOCP_cii"]

        # Rename for consistency with other tables
        df = df.rename(columns={"vSOCP_cii": "values"})
        df = df[["rp", "k", "i", "values"]]

    elif table == "pPmax":
        filename = os.path.join(input_dir, "Power_Network.xlsx")

        start_row = 7
        use_cols = "C,D,K"
        df = pd.read_excel(filename, skiprows=start_row, usecols=use_cols, header=None)
        df.columns = ["i", "j", "values"]

        # Add canonical line identifier for safe merging with vLineP/vLineQ
        df = add_canonical_line_ids(df, "i", "j")

        # Generate unique line index (direction-insensitive) - kept for backward compatibility
        line_index_dict = {}
        line_list = []
        line_indices = []

        for _, row in df.iterrows():
            ij_key = frozenset([row["i"], row["j"]])
            if ij_key not in line_index_dict:
                line_index_dict[ij_key] = len(line_index_dict)
                line_list.append([row["i"], row["j"]])
            line_indices.append(line_index_dict[ij_key])

        df["line"] = line_indices

        # Average values for duplicate lines (same line with different directions)
        df = (
            df.groupby("line_id", as_index=False)
            .agg({"values": "mean", "line": "first"})
        )

    elif table == "pDemand":  # TODO
        pass

    elif table == "vStIntraRes":
        filename = os.path.join(input_dir, "model.xlsx")
        sheet_name = "vStIntraRes"

        # Load the data
        df = pd.read_excel(filename, sheet_name=sheet_name)

        # Standardize column names
        df.columns = ["rp", "k", "storageUnits", "vStIntraRes"]

        # Rename for consistency with other tables
        df = df.rename(columns={"vStIntraRes": "values"})

        # Reorder columns to match old structure
        df = df[["rp", "k", "storageUnits", "values"]]

    else:
        print(f"Table {table} not yet implemented or invalid.")
        df = None

    if table == "vLineP" or table == "vLineQ":
        return df, df_lines
    elif table == "gi":
        return df, df_g
    else:
        return df


def copy_default_config(config_path: str = "config.yml", default_config_path: str = "config_template.yml") -> None:
    """
    Copies a default configuration file to a specified path if it does not already exist.

    Args:
        config_path (str): The path where the configuration file should be created.
            Defaults to "config.yml".
        default_config_path (str): The path to the default configuration template file.
            Defaults to "config_template.yml".

    Behavior:
        - If the file at `config_path` does not exist, the function reads the content of
          `default_config_path` and writes it to `config_path`.
        - If the file at `config_path` already exists, no action is taken, and a message
          is printed to indicate this.

    Prints:
        - A message indicating that the default configuration has been copied, or that
          the configuration file already exists.
    """
    if not os.path.exists(config_path):
        with open(default_config_path, 'r') as f:
            config = f.read()
        with open(config_path, 'w') as f:
            f.write(config)
        print(f"Copied default configuration to {config_path}. Enter path settings in the file, then rerun.")

    else:
        print(f"Configuration file already exists at {config_path}.")


def load_config(config_path: str = "config.yml") -> dict:
    """
    Loads a YAML configuration file and returns its contents as a dictionary.

    Args:
        config_path (str): The path to the YAML configuration file. 
                           Defaults to "config.yml".

    Returns:
        dict: The contents of the YAML configuration file as a dictionary.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML file.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config
