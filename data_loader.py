import os
import sqlite3
import pandas as pd
import helper_functions as h

def get_data(obj, ):
    """
    Load and process data from various input sources (SQLite, Excel, or V2G) into the object's attributes.
    This function handles data extraction, transformation, and loading based on the specified input type.
    It supports SQLite databases, Excel files, and V2G-specific formats. The processed data is stored
    as attributes of the provided object (`obj`).
    Args:
        obj: An object with the following attributes:
            - input_type (str): The type of input data. Must be one of "sqlite", "excel", or "V2G".
            - input_dir (str): The directory containing the input files or database.
            - tables (list): A list of table names to load and process.
    Raises:
        ValueError: If the `input_type` is not one of "sqlite", "excel", or "V2G".
    Note:
        - For SQLite input, the function connects to a SQLite database and extracts tables into pandas DataFrames.
        - For Excel input, the function reads tables from Excel files and processes them accordingly.
        - For V2G input, the function processes data specific to the V2G format, including handling duplicate lines and calculating relative values.

    Attributes Set on `obj`:
        - Various attributes corresponding to the loaded tables (e.g., `vLineP`, `pPmax`, `coords`, etc.).
        - `coords`: A DataFrame containing latitude and longitude information.
        - `bounds`: A list of coordinate bounds for map display.
        - `vLineP_max`: The maximum value in the `vLineP` DataFrame.
        - `vLineP_min`: The minimum value in the `vLineP` DataFrame.

    Processing Details:
        - Renames columns and drops unnecessary ones for consistency.
        - Handles duplicate entries in `vLineP` and adjusts flow values accordingly.
        - Computes relative values (`rel_values`) for `vLineP` based on `pPmax`.
        - Merges coordinate data into the `i` DataFrame.
        - Computes bounds for map display based on latitude and longitude.

    Example Usage:

        obj = SomeClass()
        obj.input_type = "sqlite"
        obj.input_dir = "/path/to/data"
        obj.tables = ["vLineP", "pPmax", "coords"]
        get_data(obj)
    """

    self = obj

    if self.input_type == "sqlite":
        # connect to the database
        conn = sqlite3.connect(os.path.join(self.input_dir, "result.sqlite"))
        # print out all tables in the database
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        # print(cursor.fetchall())


        for table in self.tables:
            # load the data as variable with the table name
            setattr(self, table, h.extract_table_to_dataframe(conn, table))
        
        if "rp" in self.tables:
            # region remove unnecessary index column in sets
            self.rp.drop(columns=["index"], inplace=True)
            self.rp.rename(columns={"0": "values"}, inplace=True)
        if "k" in self.tables:
            self.k.drop(columns=["index"], inplace=True)
            self.k.rename(columns={"0": "values"}, inplace=True)
        if "i" in self.tables:
            self.i.drop(columns=["index"], inplace=True)    
            self.i.rename(columns={"0": "values"}, inplace=True)
        if "g" in self.tables:
            self.g.drop(columns=["index"], inplace=True)
            self.g.rename(columns={"0": "values"}, inplace=True)
        if "gi" in self.tables:

            self.gi.drop(columns=["index"], inplace=True)
            self.gi.rename(columns={"0": "g"}, inplace=True)
            self.gi.rename(columns={"1": "i"}, inplace=True)
        if "thermalGenerators" in self.tables: # NOTE define those in the config as tec categories?
            self.thermalGenerators.drop(columns=["index"], inplace=True)
            self.thermalGenerators.rename(columns={"0": "g"}, inplace=True)
        if "rorGenerators" in self.tables:
            self.rorGenerators.drop(columns=["index"], inplace=True)
            self.rorGenerators.rename(columns={"0": "g"}, inplace=True)
        if "vresGenerators" in self.tables:
            self.vresGenerators.drop(columns=["index"], inplace=True)
            self.vresGenerators.rename(columns={"0": "g"}, inplace=True)
        if "storageUnits" in self.tables:
            self.storageUnits.drop(columns=["index"], inplace=True)
            self.storageUnits.rename(columns={"0": "g"}, inplace=True)

        if "la" in self.tables:
            self.la.drop(columns=["index"], inplace=True)
            self.la.rename(columns={"0": "i"}, inplace=True)
            self.la.rename(columns={"1": "j"}, inplace=True)
            self.la.rename(columns={"2": "c"}, inplace=True)
        if "pPmax" in self.tables:
            self.pPmax.rename(columns={"level_0": "i"}, inplace=True)
            self.pPmax.rename(columns={"level_1": "j"}, inplace=True)
            self.pPmax.rename(columns={"level_2": "c"}, inplace=True)
        if "vLineP" in self.tables:
            self.vLineP.rename(columns={"level_0": "rp"}, inplace=True)
            self.vLineP.rename(columns={"level_1": "k"}, inplace=True)
            self.vLineP.rename(columns={"level_2": "i"}, inplace=True)
            self.vLineP.rename(columns={"level_3": "j"}, inplace=True)
            self.vLineP.rename(columns={"level_4": "c"}, inplace=True)
            # Iterate over vLineP DataFrame
            for row_idx, row in enumerate(self.vLineP.itertuples(index=True)):  # Keep index for modification
                node_set = {row.i, row.j}  # Use set for order-independent comparison

                # Iterate over self.la DataFrame to find the matching line
                for idx, line in enumerate(self.la.itertuples(index=False)):
                    if {line.i, line.j} == node_set:
                        # Update the corresponding row in vLineP
                        self.vLineP.at[row_idx, "line"] = str(int(idx))  # Use row index from enumerate
                        break  # Stop searching once a match is found

        self.coords = h.load_lat_lon(self.input_dir)

        # add tec to self.gi
        tec = []
        for generator in self.gi.itertuples(index=True):
            # get the generator name
            g = generator.g

            if hasattr(self, "thermalGenerators") and g in self.thermalGenerators.values:
                tec.append("thermal")
            elif hasattr(self, "rorGenerators") and g in self.rorGenerators.values:
                tec.append("RoR")
            elif hasattr(self, "vresGenerators") and g in self.vresGenerators.values:
                tec.append("vres")
            elif hasattr(self, "storageUnits") and g in self.storageUnits.values:
                tec.append("storage")
            else:
                tec.append("unknown")
        self.gi["tec"] = tec
    
        # close the connection
        conn.close()
    
    elif self.input_type == "excel":
        fast=True
        if not fast:
            for table in self.tables:
                print(f"Loading table {table}...")
                if table == "vLineP":
                    df, df_lines = h.extract_excel_to_dataframe(self.input_dir, table)
                    self.vLineP = df
                    self.la = df_lines
                elif table == "gi":
                    df, df_g = h.extract_excel_to_dataframe(self.input_dir, table)
                    self.gi = df
                    self.g = df_g
                elif table == "la" or table == "g": # get from other dataframe
                    continue
                else:
                    # load the data as variable with the table name
                    setattr(self, table, h.extract_excel_to_dataframe(self.input_dir, table))
            self.coords = h.extract_excel_to_dataframe(self.input_dir, "coords")

            # only take values where duplicate is False
            self.vLineP = self.vLineP[self.vLineP["duplicate"] == False].copy()
            # drop duplicate column
            self.vLineP.drop(columns=["duplicate"], inplace=True)

            # save all the modified tables to a sqlite database
            # create a new database
            conn = sqlite3.connect(os.path.join(self.input_dir, "test_data.sqlite"))
            # save all the tables to the database
            for table in self.tables:
                if table == "vLineP":
                    self.vLineP.to_sql(table, conn, if_exists="replace", index=False)
                elif table == "la":
                    self.la.to_sql(table, conn, if_exists="replace", index=False)
                elif table == "i":
                    self.i.to_sql(table, conn, if_exists="replace", index=False)
                elif table == "pPmax":
                    pass
                elif table == "k":
                    self.k.to_sql(table, conn, if_exists="replace", index=False) 
                elif table == "g":
                    self.g.to_sql(table, conn, if_exists="replace", index=False)
                elif table == "gi":
                    self.gi.to_sql(table, conn, if_exists="replace", index=False)
                elif table == "rp":
                    self.rp.to_sql(table, conn, if_exists="replace", index=False)
                elif table == "coords":
                    # save the coords dataframe to the database
                    self.coords.to_sql(table, conn, if_exists="replace", index=False)
                elif table == "vGenP":
                    # save the vGenP dataframe to the database
                    self.vGenP.to_sql(table, conn, if_exists="replace", index=False)
                    self.vGenP["values"] = self.vGenP["values"].astype(float)

                elif table == "pDemandP":
                    # save the pDemandP dataframe to the database
                    self.pDemandP.to_sql(table, conn, if_exists="replace", index=False)
                # elif table == "vStIntraRes":
                #     # save the vStIntraRes dataframe to the database
                #     self.vStIntraRes.to_sql(table, conn, if_exists="replace", index=False)
                # elif table == "vStInterRes":
                #     # save the vStInterRes dataframe to the database
                #     self.vStInterRes.to_sql(table, conn, if_exists="replace", index=False)

            self.coords.to_sql("coords", conn, if_exists="replace", index=False)    

        else:
            # load from the database
            # connect to the database
            conn = sqlite3.connect(os.path.join(self.input_dir, "test_data.sqlite"))
            for table in self.tables:
                # load the data as variable with the table name
                setattr(self, table, h.extract_table_to_dataframe(conn, table)) 
            self.coords = h.extract_excel_to_dataframe(self.input_dir, "coords")

            # set value column of vGenP to float type
            self.vGenP["values"] = self.vGenP["values"].astype(float)

    elif self.input_type == "V2G":

        # connect to the database
        conn = sqlite3.connect(os.path.join(self.input_dir, "result.sqlite"))
        # print out all tables in the database
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        # print(cursor.fetchall())

        for table in self.tables:
            print(f"Loading table {table}...")

            if table == "vLineP":
                table_name = "vP"
            elif table == "la":
                table_name = "Branches"
            elif table == "i":
                table_name = "Buses"
            elif table == "pPmax":
                table_name = "thermal_lim"
            elif table == "k":
                table_name = "Time"
            else:
                table_name = table
            # load the data as variable with the table name
            setattr(self, table, h.extract_table_to_dataframe(conn, table_name))   

        # merge self.lat and self.lon
        buses = self.lat["Buses"].values.astype(str)
        lat = self.lat["values"].values
        lon = self.lon["values"].values
        self.coords = pd.DataFrame({"values": buses, "lat": lat, "lon": lon})
        # delete self.lat and self.long
        del self.lat
        del self.lon

        # rename i columns
        self.i.drop(columns=["index"], inplace=True)    
        self.i.rename(columns={"0": "values"}, inplace=True)
        # make sure the values are strings
        self.i["values"] = self.i["values"].astype(str)

        # rename pPmax columns
        self.pPmax.rename(columns={"level_0": "i"}, inplace=True)
        self.pPmax.rename(columns={"level_1": "j"}, inplace=True)
        # transform i and j to type str
        self.pPmax["i"] = self.pPmax["i"].astype(str)
        self.pPmax["j"] = self.pPmax["j"].astype(str)

        # rename la columns
        self.la.drop(columns=["index"], inplace=True)
        self.la.rename(columns={"0": "i"}, inplace=True)
        self.la.rename(columns={"1": "j"}, inplace=True) 
        # transform i and j to type str
        self.la["i"] = self.la["i"].astype(str)
        self.la["j"] = self.la["j"].astype(str)


        # iterate over la and find lines based on set(i, j)
        line_index_dict = {}  # frozenset(i,j) -> line index
        line_list = []        # list of [i, j] in order
        for row_idx, row in enumerate(self.la.itertuples(index=True)):  # Keep index for modification
            ij_key = frozenset([row.i, row.j])

            if ij_key not in line_index_dict:
                line_index_dict[ij_key] = len(line_index_dict)
                line_list.append([row.i, row.j])

        # overwrite self.la with line_list df
        self.la = pd.DataFrame(line_list, columns=["i", "j"])
        # rename vLineP columns
        self.vLineP.rename(columns={"level_0": "i"}, inplace=True)
        self.vLineP.rename(columns={"level_1": "j"}, inplace=True)
        self.vLineP.rename(columns={"level_2": "k"}, inplace=True) 
        # change the k column to k0001, k0002, ...
        self.vLineP["k"] = self.vLineP["k"].apply(lambda x: f"k{int(x+1):04d}") 
        # transform i and j to type str
        self.vLineP["i"] = self.vLineP["i"].astype(str)
        self.vLineP["j"] = self.vLineP["j"].astype(str)

        # initialize "is_duplicate" column to vLineP
        self.vLineP["duplicate"] = False
    
        # iterate over vLineP and find lines based on set(i, j)
        for row_idx, row in enumerate(self.vLineP.itertuples(index=True)):  # Keep index for modification
            ij_key = frozenset([row.i, row.j])
            line = line_index_dict[ij_key]
            is_duplicate = [row.i, row.j] != line_list[line]
            # Update the corresponding row in vLineP
            self.vLineP.at[row_idx, "line"] = str(int(line))
            self.vLineP.at[row_idx, "duplicate"] = is_duplicate
        
        # reverse  the value of the flow if the line is duplicate
        self.vLineP.loc[self.vLineP["duplicate"] == True, "values"] = -self.vLineP.loc[self.vLineP["duplicate"] == True, "values"]
        # always find the two rows with the same "line" and "k" and set their "values" to the mean of the two values
        self.vLineP["values"] = self.vLineP.groupby(["line", "k"])["values"].transform(lambda x: x.mean() if len(x) > 1 else x)       
        # drop all entries where the "duplicate" is True
        self.vLineP = self.vLineP[self.vLineP["duplicate"] == False].copy() 
        # drop duplicate column
        self.vLineP.drop(columns=["duplicate"], inplace=True) 
        # reset index
        self.vLineP.reset_index(drop=True, inplace=True)    


        # iterate over pPmax and add drop duplicate lines
        for row_idx, row in enumerate(self.pPmax.itertuples(index=True)):  # Keep index for modification
            node_list = [row.i, row.j]
            # check if the line is in the line_list
            if node_list not in line_list:
                # drop the line from pPmax
                self.pPmax.drop(row_idx, inplace=True)
        # reset index
        self.pPmax.reset_index(drop=True, inplace=True)


        # create gi dataframe
        self.gi = pd.DataFrame(columns=["g", "i", "tec"])

        # add PV generators
        pv_generators = []
        if hasattr(self, "PV_Buses"):
            # rename the columns
            self.PV_Buses.rename(columns={"0": "i"}, inplace=True)
            # drop the index column
            self.PV_Buses.drop(columns=["index"], inplace=True)
            for row_idx, row in enumerate(self.PV_Buses.itertuples(index=True)):
                # get the generator name
                g = row.i + "_PV"
                # get the bus name
                i = row.i
                # get tec
                tec = "Solar"
                # add to the list
                pv_generators.append([g, i, tec])

        # add wind generators
        wind_generators = []
        if hasattr(self, "Wind_Buses"):
            # rename the columns
            self.Wind_Buses.rename(columns={"0": "i"}, inplace=True)
            # drop the index column
            self.Wind_Buses.drop(columns=["index"], inplace=True)
            for row_idx, row in enumerate(self.Wind_Buses.itertuples(index=True)):
                # get the generator name
                g = row.i + "_Wind"
                # get the bus name
                i = row.i
                # get tec
                tec = "Wind"
                # add to the list
                wind_generators.append([g, i, tec])
        # add charging buses
        charging_buses = []
        if hasattr(self, "Charging_Buses"):
            # rename the columns
            self.Charging_Buses.rename(columns={"0": "i"}, inplace=True)
            # drop the index column
            self.Charging_Buses.drop(columns=["index"], inplace=True)
            for row_idx, row in enumerate(self.Charging_Buses.itertuples(index=True)):
                # get the generator name
                g = row.i + "_Discharging"
                # get the bus name
                i = row.i
                # get tec
                tec = "V2G_discharging"
                # add to the list
                charging_buses.append([g, i, tec])
        
        
        # put all the generators in one dataframe
        if hasattr(self, "PV_Buses"):
            self.gi = pd.concat([self.gi, pd.DataFrame(pv_generators, columns=["g", "i", "tec"])], ignore_index=True)
        if hasattr(self, "Wind_Buses"):
            self.gi = pd.concat([self.gi, pd.DataFrame(wind_generators, columns=["g", "i", "tec"])], ignore_index=True)
        if hasattr(self, "Charging_Buses"):
            self.gi = pd.concat([self.gi, pd.DataFrame(charging_buses, columns=["g", "i", "tec"])], ignore_index=True)
        
        # add all the generation to the vGenP dataframe
        self.vGenP = pd.DataFrame(columns=["k", "g", "values"]).astype({
                                                                "k": "str",  # or int, str, etc. — whatever matches your data
                                                                "g": "str",
                                                                "values": "float"})
        pv_production = []
        if hasattr(self, "vPV_production") and not self.vPV_production.empty:
            for row_idx, row in enumerate(self.vPV_production.itertuples(index=True)):
                # get the generator name
                g = row.PV_Buses + "_PV"
                # get the time
                k = row.Time
                # get the value
                value = row.values

                # add to the list
                pv_production.append([k, g, value])

        wind_production = []
        if hasattr(self, "vWind_production") and not self.vWind_production.empty:
            for row_idx, row in enumerate(self.vWind_production.itertuples(index=True)):
                # get the generator name
                g = row.Wind_Buses + "_Wind"
                # get the time
                k = row.Time
                # get the value
                value = row.values

                # add to the list
                wind_production.append([k, g, value])
        charging_production = []
        if hasattr(self, "vCharging_production") and not self.vCharging_production.empty:
            for row_idx, row in enumerate(self.vCharging_production.itertuples(index=True)):
                # get the generator name
                g = row.Charging_Buses + "_Discharging"
                # get the time
                k = row.Time
                # get the value
                value = row.values

                # add to the list
                charging_production.append([k, g, value])
        # put all the generators in one dataframe
        if hasattr(self, "vPV_production") and not self.vPV_production.empty:
            self.vGenP = pd.concat([self.vGenP, pd.DataFrame(pv_production, columns=["k", "g", "values"])], ignore_index=True)
        if hasattr(self, "vWind_production") and not self.vWind_production.empty:
            self.vGenP = pd.concat([self.vGenP, pd.DataFrame(wind_production, columns=["k", "g", "values"])], ignore_index=True)
        if hasattr(self, "vCharging_production") and not self.vCharging_production.empty:
            self.vGenP = pd.concat([self.vGenP, pd.DataFrame(charging_production, columns=["k", "g", "values"])], ignore_index=True)
        print(self.vWind_production)

        self.vGenP["k"] = self.vGenP["k"].apply(lambda x: f"k{int(x+1):04d}")

        # close the connection
        conn.close()

    else:
        raise ValueError("Invalid input type. Please choose either 'excel', 'sqlite' or V2G.")
    

    # add the coordinates in coords to the i dataframe
    self.i = pd.merge(self.i, self.coords, left_on="values", right_on="values", how="left")
    # set the index to the values column
    self.i.set_index("values", inplace=True)


    # iterate over pPmax and add the line number to the dataframe
    for row_idx, row in enumerate(self.pPmax.itertuples(index=True)):  # Keep index for modification
        node_set = {row.i, row.j}  # Use set for order-independent comparison

        # Iterate over self.la DataFrame to find the matching line
        for idx, line in enumerate(self.la.itertuples(index=False)):
            if {line.i, line.j} == node_set:
                # Update the corresponding row in vLineP
                self.pPmax.at[row_idx, "line"] = str(int(idx))
                break  # Stop searching once a match is found


    # add to every line in vLineP the value divided by pPmax
    self.vLineP["rel_values"] = abs(self.vLineP["values"]) / self.vLineP["line"].map(
        self.pPmax.set_index("line")["values"]
    )
    self.vLineP["pPmax"] = self.vLineP["line"].map(
        self.pPmax.set_index("line")["values"]
    )
 
    # Compute bounds for map display
    self.bounds = [
        [min(self.i['lat']), min(self.i['lon'])],
        [max(self.i['lat']), max(self.i['lon'])]
    ]
