import pandas as pd
import os


def load_network(scenario_folder: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the network data from the scenario folder.

    :param scenario_folder: The folder of the scenario.

    :return: The network data and the bus information.

    """

    filepath_network = scenario_folder + '\\Power_Network.xlsx'
    filepath_bus = scenario_folder + '\\Power_BusInfo.xlsx'

    # check if files exist
    if not os.path.exists(filepath_network):
        raise FileNotFoundError(f"File {filepath_network} not found.")
    if not os.path.exists(filepath_bus):
        raise FileNotFoundError(f"File {filepath_bus} not found.")
    
    
    network = pd.read_excel(filepath_network, sheet_name='Power Network', skiprows=6,
                            usecols='B,C,N', header=None, names=['node1', 'node2', 'LineID'])
    bus_info = pd.read_excel(filepath_bus, sheet_name='Power BusInfo', skiprows=2,
                             usecols='B,D,L,M', header=None, names=['NodeID','BaseVolt', 'lat', 'long'])
    return network, bus_info

def load_line_load(scenario_folder: str) -> pd.DataFrame:
    """
    Load the line load data from the scenario folder.

    :param scenario_folder: The folder of the scenario.

    :return: The line load data and the options for rp selection.

    """
    filepath_results = scenario_folder + "\\results\\results.xlsx"

    # check if file exists
    if not os.path.exists(filepath_results):
        raise FileNotFoundError(f"File {filepath_results} not found.")

    line_load = pd.read_excel(filepath_results,  sheet_name='LineP_Perc', skiprows=1, header=None)
    num_rp = line_load.shape[1] - 4

    line_load.columns = ['k', 'node1', 'node2', 'circuit_id'] + ['pLoad_rp' + str(i) for i in range(1, num_rp+1)]
    # take absolute values of all line load colums
    line_load[['pLoad_rp' + str(i) for i in range(1, num_rp+1)]] = line_load[['pLoad_rp' + str(i) for i in range(1, num_rp+1)]].abs()
    # calculate maximum of all representative periods
    line_load['max_line_load'] = line_load[['pLoad_rp' + str(i) for i in range(1, num_rp+1)]].max(axis=1)
    options_network = [{'label': 'rp' + str(i), 'value': i} for i in range(1, num_rp+1)]

    return line_load, options_network

def load_total_energy(scenario_folder: str) -> pd.DataFrame:

    """
    Load the total energy data from the scenario folder.

    :param scenario_folder: The folder of the scenario.

    :return: The total energy data.
    
    """
    
    filepath_results = scenario_folder + "\\results\\results.xlsx"
    df = pd.read_excel(filepath_results, sheet_name='TotalEnrp', skiprows=0, header=0,)
    # rename 'Unnamed: 0' to 'rp'
    df.rename(columns={'Unnamed: 0': 'rp'}, inplace=True)
    # rename 'Unnamed: 1' to 'k'
    df.rename(columns={'Unnamed: 1': 'k'}, inplace=True)

    return df