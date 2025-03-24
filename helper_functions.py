import pandas as pd
def load_lat_lon(filepath: str):
    sheetname = "Power BusInfo"

    start_row = 7
    df = pd.read_excel(filepath, sheet_name=sheetname, skiprows=start_row-1, header=None)
    df = df[[1, 12, 13]]
    df.columns = ["id", "lat", "lon"]
    # set index to id
    df.set_index("id", inplace=True)
  
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
    




