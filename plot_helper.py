import data_helper as dh
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from ipywidgets import interact # for interactive plots
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def plot_network(scenario_folder: str, show_input: bool, show_line_load: bool = False, rp: int = 1, k: int = 1):
    """
    Plot the network from the excel input files. First the network is loaded and then plotted.

    :param scenario_folder: The folder of the scenario.
    :param show_input: The checkbox for the input.
    :param line_load: The checkbox for the line load plot. If True, the maximum line load is color coded.
    :param rp: The representative period to plot.
    :param k: The hour k to plot.
    """

    # load the network data
    network, bus_info = dh.load_network(scenario_folder)

    # plot the network
    fig, ax = plt.subplots()

    if show_input:

        for idx in network.index:
            node1 = network.at[idx, 'node1']
            node2 = network.at[idx, 'node2']
            
            node1_param = bus_info[bus_info['NodeID'] == node1]
            node2_param = bus_info[bus_info['NodeID'] == node2]

            ax.plot([node1_param['long'], node2_param['long']], [node1_param['lat'], node2_param['lat']], color='b')
            ax.scatter(node1_param['long'], node1_param['lat'], color='black')
            ax.scatter(node2_param['long'], node2_param['lat'], color='black')

    if show_line_load:

        # Create a colormap
        cmap = cm.get_cmap('RdYlGn')
        # invert the colormap
        cmap = cmap.reversed()  
        # load the line load data
        line_load = dh.load_line_load(scenario_folder)

        # take only the rows with the value of k
        line_load = line_load[line_load['k'] == 'k' + str(k).zfill(4)]

        for idx in line_load.index:

            node1 = line_load.at[idx, 'node1']
            node2 = line_load.at[idx, 'node2']
            congestion = line_load.at[idx, 'pLoad_rp' + str(rp)]
            node1_param = bus_info[bus_info['NodeID'] == node1]
            node2_param = bus_info[bus_info['NodeID'] == node2]
            # get the color from the colormap
            color = cmap(congestion)

            ax.plot([node1_param['long'], node2_param['long']],
                    [node1_param['lat'], node2_param['lat']],
                    color=color, linestyle='-')
            ax.scatter(node1_param['long'], node1_param['lat'], color='black')
            ax.scatter(node2_param['long'], node2_param['lat'], color='black')

        # Create a colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        fig.colorbar(sm, ax=ax, orientation='vertical') 


def generate_interactive_plot(scenario_folder: str, plot_type: str):
    """
    Wrapper function to generate interactive plots. The function calls the interact function with the correct plot function.

    :param scenario_folder: The folder of the scenario.
    :param plot_type: The type of plot to generate.
    """

    if plot_type == 'network':
        line_load = dh.load_line_load(scenario_folder)
        rp_max = line_load.shape[1] - 4
        k_max = line_load['k'].nunique()

        plot = plot_network

        # calling the interact function
        interact(plot, scenario_folder=scenario_folder, rp=(1,rp_max), k=(1,k_max), show_input=bool(), show_line_load=bool())

    elif plot_type == 'consumption':
        raise NotImplementedError("Line load plot not implemented yet.")
    
    elif plot_type == 'generation':
        raise NotImplementedError("Generation plot not implemented yet.")


def plot_energy_sources(scenario_folder: str):
    """
    Plot the energy sources from the excel results file uing plotly.

    :param scenario_folder: The folder of the scenario.
    """

    # Load results file
    df = dh.load_total_energy(scenario_folder)
    rps = df.rp.unique()
    num_rp = len(rps)
    columns = df.columns[2:]
    # Initialize figure
    fig = go.Figure()

    # Add Traces
    for rp in rps:
        for column in columns:
            fig.add_trace(
                go.Scatter(x=list(df[df.rp == rp].k),
                        y=list(df[df.rp == rp][column]),
                        name=column))

    buttons = []

    for i in range(num_rp):
        visibility = np.array([False]*num_rp*len(columns))
        visibility[i*len(columns):(i+1)*len(columns)] = True
        button = dict(label='rp' + str(i),
                    method='update',
                    args=[{'visible': visibility},
                        {'title': 'Energy Sources for rp' + str(i)}])
        buttons.append(button)

    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
            )
        ])

    # Set title
    fig.update_layout(title_text="Yahoo")

    fig.show()
