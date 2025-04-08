def load_data(obj, ):
    import os
    import sqlite3
    import pandas as pd
    import helper_functions as h  # Or whatever your helper module is

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
            self.gi.rename(columns={"0": "g"}, inplace=True)
            self.gi.rename(columns={"1": "i"}, inplace=True)
            self.gi.drop(columns=["index"], inplace=True)
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
        
    elif self.input_type == "excel":
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
    self.vLineP_max = self.vLineP["values"].max()
    self.vLineP_min = self.vLineP["values"].min()   

    # Compute bounds for map display
    self.bounds = [
        [min(self.i['lat']), min(self.i['lon'])],
        [max(self.i['lat']), max(self.i['lon'])]
    ]
