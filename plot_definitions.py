import plotly.express as px
import pandas as pd

def generate_plot(self: pd.DataFrame, x_axis: str, y_axis: str, scope: str, node_idx: int, line_idx: int, selected_period: str, time_range: list,):
   
    k_range = [str(f"k{time:04d}") for time in range(time_range[0], time_range[1] + 1)] if self.long_format else self.k["values"].values.tolist()
    color_sequence = self.graph_options["colors"]

    if y_axis == "demand":
        y_df = filter_dataframe(self, "pDemandP", rp=selected_period, scope=scope, local_node=node_idx, k_range=k_range)
    elif y_axis == "dispatch":
        y_df = filter_dataframe(self, "vGenP", rp=selected_period, scope=scope, local_node=node_idx, k_range=k_range)
    elif y_axis == "power_flow":
        y_df = filter_dataframe(self, "vLineP", rp=selected_period, scope=scope, local_line=line_idx, k_range=k_range)
    elif y_axis == "soc":
        y_df = filter_dataframe(self, "vStIntraRes", rp=selected_period, scope=scope, local_node=node_idx, k_range=k_range)
    else:
        y_df = None    


    if y_df is  None or y_df.empty:
        fig = None
    else:

        if x_axis == "time" and y_axis == "dispatch":
            x_label = "Time"
            title = "Global dispatch over time" if scope == "Global" else f"Local dispatch for {node_idx} over time"
            fig = px.area(y_df, x="k", y="values", color="g", title=title, labels={"k": x_label, "values": "Dispatch", "g": "Generator"}, color_discrete_sequence=color_sequence,)    
        elif x_axis == "time" and y_axis == "demand":
            x_label = "Time"
            title = "Global demand over time" if scope == "Global" else f"Local demand for {node_idx} over time"
            fig = px.line(y_df, x="k", y="values", title="Demand Over Time", labels={"i": x_label, "values": "Demand"}, color_discrete_sequence=color_sequence,)       
        elif x_axis == "time" and y_axis == "power_flow":
            x_label = "Time"
            title = "Power Flow over time" if scope == "Global" else f"Local Power Flow for {line_idx} over time"
            fig = px.line(y_df, x="k", y="values", color="line", title=title, labels={"k": x_label, "values": "Power Flow", "line": "Line"},
                              hover_data={"values": True, "line": True, "i": True, "j": True}, color_discrete_sequence=color_sequence,)
        elif x_axis == "generator" and y_axis == "dispatch":
            x_label = "Generator"
            y_df["k"] = y_df["k"].astype(str).copy()
            y_df["g"] = y_df["g"].astype(str).copy()
            y_df["values"] = pd.to_numeric(y_df["values"], errors="coerce")
            title = "Global dispatch for each generator" if scope == "Global" else f"Local dispatch for {node_idx}"
            fig = px.bar(y_df, x="g", y="values", color="g", title=title, labels={"g": x_label, "values": "Dispatch", "k": "Time"},
                         hover_data={"values": False, "k": False}, color_discrete_sequence=color_sequence)
        elif x_axis == "line" and y_axis == "power_flow":
            x_label = "Line"
            title = "Power Flow Distribution over all Lines" if scope == "Global" else f"Local Power Flow Distribution for {line_idx}"
            fig = px.histogram(y_df, x="values", color="line", title=title, nbins=10,
                               color_discrete_sequence=color_sequence)  
        elif x_axis == "time" and y_axis == "soc":
            x_label = "time"
            title = "vStIntraRes for all Storage Units over time" if scope == "Global" else f"vStIntraRes for storage units of {node_idx} over time"
            fig = px.line(y_df, x="k", y="values", color="i", title=title, labels={"k": x_label, "values": "State of Charge", "i": "Storage Unit"},
                              hover_data={"values": True, "i": True}, color_discrete_sequence=color_sequence)
        else:
            fig = None # return None if no valid x_axis and y_axis combination is found       
    return fig


def filter_dataframe(self, attr_str: str, rp: str, scope: str, local_node: str=None, local_line: str=None, k_range: list=[]) -> pd.DataFrame:
    """
    Filters a DataFrame based on the provided attributes, scope, and conditions.

    Args:
        attr_str (str): The attribute string specifying which DataFrame to filter.
                        Options include "vGenP", "pDemandP", and "vLineP".
        rp (str): The representative period to filter by, applicable when `long_format` is False.
        scope (str): The scope of filtering. Options include "Local" and "Global".
                    - "Local": Filters data specific to a local node or line.
                    - "Global": Aggregates data globally (only applicable for "pDemandP").
        local_node (str, optional): The local node identifier for filtering when `scope` is "Local".
                                    Defaults to None.
        local_line (str, optional): The local line identifier for filtering when `scope` is "Local".
                                    Defaults to None.
        k_range (list, optional): A list of `k` values to filter the DataFrame by. Defaults to an empty list.

    Returns:
        pd.DataFrame: The filtered DataFrame based on the specified conditions.
                    Returns None if the specified DataFrame is not available.

    Note:
        - The method operates on different DataFrames (`vGenP`, `pDemandP`, `vLineP`) based on `attr_str`.
        - If `long_format` is False, the DataFrame is filtered by the representative period (`rp`).
        - For "pDemandP" with "Global" scope, the data is aggregated by summing over `k` values.
        - For "vGenP" with "Local" scope, filtering is based on the local node's group (`g`).
        - For "vLineP" with "Local" scope, filtering is based on the local line identifier.

    """
   
    df = None

    if attr_str == "vGenP":
        df = self.vGenP
        if df is None:
            return None
        if not self.long_format:
            df = df[df["rp"] == rp]
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            g_local = self.gi[self.gi["i"] == local_node]
            df = df[df["g"].isin(g_local["g"])]

    elif attr_str == "pDemandP":
        df = self.pDemandP
        if df is None:
            return None
        if not self.long_format:
            df = df[df["rp"] == rp]
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            df = df[df["i"] == local_node]
        elif scope == "Global":
            df = df.groupby(["k"]).sum().reset_index()

    elif attr_str == "vLineP":
        df = self.vLineP
        if df is None:
            return None
        if not self.long_format:
            df = df[df["rp"] == rp]
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            df = df[df["line"] == local_line]

    elif attr_str == "vStIntraRes":
        df = self.vStIntraRes
        if df is None:
            return None
        if not self.long_format:
            df = df[df["rp"] == rp]
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            df = df[df["i"] == local_node]
    return df