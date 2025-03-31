import pandas as pd
import os
import yaml
import time

def load_lat_lon(input_dir: str):
    sheetname = "Power BusInfo"
    filename = os.path.join(input_dir, "Power_BusInfo.xlsx")
    start_row = 7
    df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row-1, header=None)
    df = df[[1, 12, 13]]
    df.columns = ["values", "lat", "lon"]
  
    return df

def extract_table_to_dataframe(con, table_name):
    """
    Extracts a table from an SQLite database into a Pandas DataFrame.

    Parameters:
        con (sqlite3.Connection): SQLite connection object.
        table_name (str): Name of the table to extract.

    Returns:
        pd.DataFrame: DataFrame containing the table data.
    """
    try:
        # Query the table
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, con)
        
        return df
    
    except Exception as e:
        print(f"Error extracting table {table_name}: {e}")
        return None

def extract_excel_to_dataframe(input_dir, table):

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

def copy_default_config(config_path="config.yml", default_config_path="config_template.yml"):
    """
    Copies the default configuration file to the specified path.

    Parameters:
        config_path (str): Path where the configuration file will be copied.
        default_config_path (str): Path of the default configuration file.

    Returns:
        None
    """
    if not os.path.exists(config_path):
        with open(default_config_path, 'r') as f:
            config = f.read()
        with open(config_path, 'w') as f:
            f.write(config)
        print(f"Copied default configuration to {config_path}. Enter path settings in the file.")
        
    else:
        print(f"Configuration file already exists at {config_path}.")

def load_config(config_path="config.yml"):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config
