import pandas as pd
import os
import yaml
import time
import sqlite3

def load_lat_lon(input_dir: str):
    """
    Loads latitude and longitude data from an Excel file.
    This function reads an Excel file named "Power_BusInfo.xlsx" located in the specified 
    input directory. It extracts data from the sheet named "Power BusInfo", starting from 
    row 7 (zero-indexed). The function selects specific columns, renames them, and returns 
    the resulting DataFrame.
    Args:
        input_dir (str): The directory path where the "Power_BusInfo.xlsx" file is located.
    Returns:
        pandas.DataFrame: A DataFrame containing three columns:
            - "values": Data from column 1 of the Excel sheet.
            - "lat": Latitude data from column 12 of the Excel sheet.
            - "lon": Longitude data from column 13 of the Excel sheet.
    """
    sheetname = "Power BusInfo"
    filename = os.path.join(input_dir, "Power_BusInfo.xlsx")
    start_row = 7
    df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row-1, header=None)
    df = df[[1, 12, 13]]
    df.columns = ["values", "lat", "lon"]
  
    return df

def extract_table_to_dataframe(con: sqlite3.Connection, table_name: str) -> pd.DataFrame:
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

def extract_excel_to_dataframe(input_dir: str, table: str) -> pd.DataFrame:
    """
    Extract data from Excel files into a pandas DataFrame based on the specified table type.
    This function processes various Excel files and sheets, extracting and transforming data 
    into pandas DataFrames according to the provided `table` parameter. The function supports 
    multiple table types, each corresponding to a specific data extraction and transformation logic.

    Parameters:

        input_dir (str): The directory containing the input Excel files.
        table (str): The type of table to extract. Supported values are:
        
            - "i": Extracts data from "Power_BusInfo.xlsx" (sheet "Power BusInfo").
            - "rp": Extracts unique values from "results.xlsx" (sheet "TotalEnrp").
            - "k": Extracts unique values from "results.xlsx" (sheet "TotalEnrp").
            - "gi": Combines data from multiple Excel files ("Power_VRES", "Power_ThermalGen", 
              "Power_Storage", "Power_RoR") into a DataFrame with columns "g" and "i".
            - "vLineP": Processes line data from "results.xlsx" (sheet "pLineP") and returns 
              two DataFrames: one for the main data and one for line tuples.
            - "coords": Extracts coordinates (longitude and latitude) from "Power_BusInfo.xlsx" 
              (sheet "Power BusInfo").
            - "vGenP": Processes generator data from "results.xlsx" (sheet "GenP") into a long-format DataFrame.
            - "pPmax": Extracts power network data from "Power_Network.xlsx" (sheet "Power Network").
            - "pDemand": Placeholder for future implementation.

    Returns:

        pandas.DataFrame or tuple: 
            - For most table types, returns a single DataFrame containing the extracted data.
            - For "vLineP", returns a tuple of two DataFrames: (main data, line tuples).
            - For "gi", returns a tuple of two DataFrames: (main data, unique "g" values).
            - Returns None if the table type is invalid or not yet implemented.
    Note:
    
        - The function uses hardcoded file and sheet names for specific table types.
        - Some table types include additional preprocessing steps, such as removing duplicates 
          or resetting the index.
        - For "vLineP" and "vGenP", the function includes performance timing for processing.

    Raises:
        FileNotFoundError: If the specified Excel files or sheets are not found.
        ValueError: If the table type is invalid or not supported.
        
    """

    if table == "i":
        filename = os.path.join(input_dir, "Power_BusInfo.xlsx")
        sheetname = "Power BusInfo"
        start_row = 7
        use_cols = "B"
        df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row-1, usecols=use_cols, header=None)
        df.columns = ["values"]

    elif table == "rp":
        filename = os.path.join(input_dir, "results", "results.xlsx")
        sheetname = "TotalEnrp"
        start_row = 1
        use_cols = "A"
        df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row, usecols=use_cols, header=None)
        df.columns = ["values"]
        # only take unique values
        df = df.drop_duplicates()
        # reset index
        df.reset_index(drop=True, inplace=True)

    elif table == "k":
        filename = os.path.join(input_dir, "results", "results.xlsx")
        sheetname = "TotalEnrp"
        start_row = 1
        use_cols = "B"
        df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row, usecols=use_cols, header=None)
        df.columns = ["values"]
        # only take unique values
        df = df.drop_duplicates()
        # reset index
        df.reset_index(drop=True, inplace=True)

    elif table == "gi":
        filenames = [os.path.join(input_dir, tech + ".xlsx") for tech in ["Power_VRES", "Power_ThermalGen", "Power_Storage", "Power_RoR"]]
        sheetnames = ["Power VRES", "Power ThermalGen", "Power Storage", "Power RoR"]
        use_cols = "B,D"
        skiprows = 7
        df = pd.DataFrame(columns=["g", "i"])
        for filename, sheetname in zip(filenames, sheetnames):
            temp_df = pd.read_excel(filename, sheet_name=sheetname, usecols=use_cols, skiprows=skiprows-1, header=None)
            temp_df.columns = ["g", "i"]
            df = pd.concat([df, temp_df], ignore_index=True)
        # reset index
        df.reset_index(drop=True, inplace=True)
        df_g = df["g"].drop_duplicates().reset_index(drop=True)

    elif table == "vLineP":

        start = time.time()
        filename = os.path.join(input_dir, "results", "results.xlsx")
        sheetname = "pLineP"

        # Step 1: Load header rows
        header_df = pd.read_excel(filename, sheet_name=sheetname, header=None, nrows=3)
        i_list = header_df.iloc[0, 2:].tolist()
        j_list = header_df.iloc[1, 2:].tolist()
        c_list = header_df.iloc[2, 2:].tolist()

        # Step 2: Load the rest of the data
        data_df = pd.read_excel(filename, sheet_name=sheetname, header=None, skiprows=3)

        # Step 3: Preprocess unique line tuples with direction
        line_index_dict = {}  # frozenset(i,j) -> line index
        line_list = []        # list of [i, j] in order
        records = []

        for idx, (i, j) in enumerate(zip(i_list, j_list)):
            ij_key = frozenset([i, j])
            if ij_key not in line_index_dict:
                line_index_dict[ij_key] = len(line_index_dict)
                line_list.append([i, j])

        # Step 4: Main loop (fast, flat)
        for row in data_df.itertuples(index=False):
            rp = row[0]
            k = row[1]
            values = row[2:]

            for idx, value in enumerate(values):
                i = i_list[idx]
                j = j_list[idx]
                c = c_list[idx]
                ij_key = frozenset([i, j])
                line = line_index_dict[ij_key]
                is_duplicate = [i, j] != line_list[line]

                records.append({
                    'rp': rp,
                    'k': k,
                    'i': i,
                    'j': j,
                    'c': c,
                    'values': value,
                    'line': str(line),
                    'duplicate': is_duplicate
                })

        # Final outputs
        df = pd.DataFrame.from_records(records)
        df_lines = pd.DataFrame(line_list, columns=['i', 'j'])

        end = time.time()
        print(f"Time taken to process vLineP: {end - start:.2f} seconds")

    elif table =="coords":
        filename = os.path.join(input_dir, "Power_BusInfo.xlsx")
        sheetname = "Power BusInfo"
        start_row = 7
        use_cols = "B,L,M"
        df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row-1, usecols=use_cols, header=None)
        df.columns = ["values", "lon", "lat"]
        # set index to id
        df.set_index("values", inplace=True)
    
    elif table == "vGenP":

        start = time.time()
        filename = os.path.join(input_dir, "results", "results.xlsx")
        sheetname = "GenP"

        # Step 1: Load data once
        raw_df = pd.read_excel(filename, sheet_name=sheetname, header=None)

        # Step 2: Extract header and data
        g_list = raw_df.iloc[0, 1:].tolist()  # generators
        data_df = raw_df.iloc[1:, :]          # rest of the rows
        

        # Step 3: Rename columns
        data_df.columns = ['h'] + g_list
        data_df = data_df.copy()  # ← ensures it's a real copy, not a slice view
        # Step 4: Create 'k' column from 'h'
        data_df['k'] = data_df['h'].apply(lambda h: 'k' + h[1:] if isinstance(h, str) and h.startswith('h') else h)
        data_df['rp'] = 'rp01'  # Hardcoded for now



        # Step 5: Melt the data into long format
        df = pd.melt(
            data_df,
            id_vars=['rp', 'k'],
            value_vars=g_list,
            var_name='g',
            value_name='values'
        )


        # Optional: reorder columns
        df = df[['rp', 'k', 'g', 'values']]

        end = time.time()
        print(f"Time taken to process vGenP: {end - start:.2f} seconds")

    elif table == "pPmax":
        filename = os.path.join(input_dir, "Power_Network.xlsx")
        sheetname = "Power Network"

        start_row = 7
        use_cols = "B,C,K"
        df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row-1, usecols=use_cols, header=None)
        df.columns = ["i", "j", "values"]

    elif table == "pDemand":
        pass

    else:
        print(f"Table {table} not yet implemented or invalid.")
        df = None

    if table == "vLineP":
        return df, df_lines
    elif table == "gi":
        return df, df_g
    else:
        return df 

def copy_default_config(config_path: str="config.yml", default_config_path: str="config_template.yml") -> None:
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

def load_config(config_path: str="config.yml") -> dict:
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

