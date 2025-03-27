import pandas as pd
import os
def load_lat_lon(filepath: str):
    sheetname = "Power BusInfo"

    start_row = 7
    df = pd.read_excel(filepath, sheet_name=sheetname, skiprows=start_row-1, header=None)
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

def extract_excel_to_dataframe(filepath_lego, table):

    if table == "i":
        filename = os.path.join(filepath_lego, "Power_BusInfo.xlsx")
        sheetname = "Power BusInfo"
        start_row = 7
        use_cols = "B"
        df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row-1, usecols=use_cols, header=None)
        df.columns = ["values"]

    elif table == "rp":
        filename = os.path.join(filepath_lego, "results", "results.xlsx")
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
        filename = os.path.join(filepath_lego, "results", "results.xlsx")
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
        filenames = [os.path.join(filepath_lego, tech + ".xlsx") for tech in ["Power_VRES", "Power_ThermalGen", "Power_Storage", "Power_RoR"]]
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
        filename = os.path.join(filepath_lego, "results", "results.xlsx")
        sheetname = "pLineP"

        # Step 1: Load top 3 rows (i, j, c)
        header_df = pd.read_excel(filename, sheet_name=sheetname, header=None, nrows=3)
        i_list = header_df.iloc[0, 2:].tolist()
        j_list = header_df.iloc[1, 2:].tolist()
        c_list = header_df.iloc[2, 2:].tolist()
        unique_line_tuples_set = []
        unique_line_tuples_list = []

        # Step 2: Load the rest of the data (rp, k, and values)
        data_df = pd.read_excel(filename, sheet_name=sheetname, header=None, skiprows=3)

        # Step 3: Prepare final rows
        records = []
        for row in data_df.itertuples(index=False):
            rp = row[0]
            k = row[1]
            values = row[2:]

            for idx, value in enumerate(values):
                i = i_list[idx]
                j = j_list[idx]
                ij_tuple = set([i, j])

                if ij_tuple in unique_line_tuples_set:
                    line = unique_line_tuples_set.index(ij_tuple)
                    # chack if the order of i and j is correct
                    if unique_line_tuples_list[line] != [i,j]:
                        duplicate = True
                    else: 
                        duplicate = False
                else:
                    unique_line_tuples_set.append(ij_tuple)
                    unique_line_tuples_list.append([i,j])
                    line = len(unique_line_tuples_set) - 1
                    duplicate = False
                c = c_list[idx]
                records.append({
                    'rp': rp,
                    'k': k,
                    'i': i,
                    'j': j,
                    'c': c,
                    'values': value,
                    'line': str(int(line)),
                    'duplicate': duplicate
                })

        # Step 4: Create final DataFrame
        df = pd.DataFrame.from_records(records)
        df_lines = pd.DataFrame(unique_line_tuples_list, columns=["i", "j"])

    elif table =="coords":
        filename = os.path.join(filepath_lego, "Power_BusInfo.xlsx")
        sheetname = "Power BusInfo"
        start_row = 7
        use_cols = "B,L,M"
        df = pd.read_excel(filename, sheet_name=sheetname, skiprows=start_row-1, usecols=use_cols, header=None)
        df.columns = ["values", "lon", "lat"]
        # set index to id
        df.set_index("values", inplace=True)
    
    elif table == "vGenP":

        filename = os.path.join(filepath_lego, "results", "results.xlsx")
        sheetname = "GenP"

        # Step 1: Load first row g
        header_df = pd.read_excel(filename, sheet_name=sheetname, header=None, nrows=1)
        g_list = header_df.iloc[0, 1:].tolist()

        # Step 2: Load the rest of the data (h and values)
        data_df = pd.read_excel(filename, sheet_name=sheetname, header=None, skiprows=1)

        # Step 3: Prepare final rows
        records = []
        for row in data_df.itertuples(index=False):
            rp = "rp01" # NOTE: this must change when we have multiple rps
            h = row[0]
            # replace hxxxx with kxxxx
            k = "k" + h[1:]
            values = row[1:]

            for idx, value in enumerate(values):
                g = g_list[idx]
                records.append({
                    'rp': rp,
                    'k': k,
                    'g': g,
                    'values': value,
                })

        # Step 4: Create final DataFrame
        df = pd.DataFrame.from_records(records)

    elif table == "pPmax":
        filename = os.path.join(filepath_lego, "Power_Network.xlsx")
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


# df = extract_excel_to_dataframe(filepath_lego, table) # Expected output: DataFrame with one column named "values" containing the values from the "Power_BusInfo.xlsx" file.
# print(df.head()) # Expected output: First 5 rows of the DataFrame.