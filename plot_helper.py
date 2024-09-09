import data_helper as dh
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import plotly.express as px


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
    # remove columns with only 0 values
    columns = [col for col in columns if df[col].sum() != 0]
    # Initialize figure
    fig = go.Figure()

    # Add Traces
    for rp in rps:
        data = df[df.rp == rp]
        base = 0
        base_negative = 0
        for idx, column in enumerate(columns):
            if column == 'Demand' or column == "Sto_Charge":
                fig.add_trace(
                    go.Bar(x=list(data['k']),
                               y=data[column],
                               name=column,
                               base=base_negative,
                                offsetgroup=0,
                               visible=False if rp != 'rp01' else True,
                               hovertext=column,
                               hoverinfo='text',
                               ),
                               )
                base_negative += data[column]
                
            else:
                fig.add_trace(


                go.Bar(x=data['k'], y=data[column], name=column,
                    base=base,
                    offsetgroup=0,
                    visible=False if rp != 'rp01' else True,
                    hovertext=column,
                    hoverinfo='text',))
                
                base += data[column]
            
    buttons = []
    
    for i in range(num_rp):
        visibility = np.array([False]*num_rp*len(columns))
        visibility[i*len(columns):(i+1)*len(columns)] = True
        button = dict(label='rp' + str(i+1),
                    method='update',
                    args=[{'visible': visibility},
                        {'title': 'Energy Sources for rp' + str(i+1)}])
        buttons.append(button)


    # modify the bar base of the first trace

    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
          
            )
        ])
    



    
    # Set title
    fig.update_layout(title_text="Energy Sources for rp1", title_x=0.5)
    # disable selection in legend
    fig.update_layout(legend=dict(traceorder='normal'))


    return fig


def plot_line_load(scenario_folder: str, rp: int = 1):
   

    # load network data and line loads
    _, bus_info = dh.load_network(scenario_folder)
    line_load, _ = dh.load_line_load(scenario_folder)

    # get number of hours
    num_h = line_load['k'].nunique()

    # get the edges of the network as disconnected lines

    # define function to generate traces that represent the lines and nodes
    def generate_traces(rp,k):

        # take values for hour k only
        line_load_k = line_load[line_load['k'] == 'k' + str(k).zfill(4)]
        
        edge_traces = []

        for idx in line_load_k.index:
            edge_x = []
            edge_y = []
            node1 = line_load_k.at[idx, 'node1']
            node2 = line_load_k.at[idx, 'node2']
            node1_int = int(node1[5:])
            node2_int = int(node2[5:])
            if node1_int > node2_int:
                pass
            else:            
                node1_param = bus_info[bus_info['NodeID'] == node1]
                node2_param = bus_info[bus_info['NodeID'] == node2]
                edge_x.append(node1_param['long'].to_numpy()[0])
                edge_x.append(node2_param['long'].to_numpy()[0])
                edge_y.append(node1_param['lat'].to_numpy()[0])
                edge_y.append(node2_param['lat'].to_numpy()[0])

                mid_x = (node1_param['long'].to_numpy()[0] + node2_param['long'].to_numpy()[0]) / 2
                mid_y = (node1_param['lat'].to_numpy()[0] + node2_param['lat'].to_numpy()[0]) / 2
                load = line_load_k.at[idx, 'pLoad_rp' + str(rp)]
                angle = (np.arctan2( edge_y[1] - edge_y[0],edge_x[1] - edge_x[0]) * 180 / np.pi)

                angle = angle + 90 if angle < 0 else angle - 90
                        
                non_zero = 1 if load != 0 else 0

                color = cm.RdYlGn(1-load)
                color = color[0:3]

                edge_traces.append(go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode='lines',
                    line=dict(width=2, color='rgb'+str(color)),
                    hoverinfo='skip',
                    legendgroup='rp'+str(rp),
                    showlegend=False,
                    visible=False

                ))

                # set the hoverinfo for the midpoint marker
                hoverinfo = 'text'
                symbol = 'arrow' if non_zero else 'circle'
                # Add a marker at the midpoint
                edge_traces.append(go.Scatter(
                    x=[mid_x],
                    y=[mid_y],
                    mode='markers',
                    marker=dict(
                        size=20*non_zero,  # Adjust size as needed
                        symbol=symbol,
                        angle=angle,
                        color='rgb'+str(color),  # Use the same color as the line or adjust as needed
                    ),
                    hoverinfo=hoverinfo,
                    legendgroup='rp'+str(rp),
                    showlegend=False,
                    visible=False
                ))

        # add node traces
        node_x = [bus_info.at[idx, 'long'] for idx in bus_info.index]
        node_y = [bus_info.at[idx, 'lat'] for idx in bus_info.index]
        node_id = [bus_info.at[idx, 'NodeID'] for idx in bus_info.index]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hovertext=node_id,
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='RdYlGn',
                reversescale=True,
                color=[],
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Line Load',
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2,
                cmin=0,
                cmax=1,),
                visible=False,
                legendgroup='rp'+str(rp),
                name='rp'+str(rp),
                showlegend=False
            )
        traces = edge_traces
        traces.append(node_trace)
        return traces
    
    num_traces = len(generate_traces(1,1)) # NOTE: Assuming no additional traces are added due to investment decisions
    # create slider steps
    steps = []
    for i in range(1,num_h+1):
        step = dict(
            method="update",
            args=[{"visible": [False] * num_traces*num_h}],
            label=str(i),
        )
        step["args"][0]["visible"][(i-1)*num_traces:i*num_traces] = [True] * len(generate_traces(rp,i))
        steps.append(step)

    # create the sliders
    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Hour: "},
        pad={"t": 50},
        steps=steps
    )]

    # create the figure
    fig = go.Figure()
    for k in range(1,num_h+1):
        fig.add_traces(generate_traces(rp,k))

    # set the first traces visible
    for i in range(num_traces):
        fig.data[i].visible = True

    fig.update_layout(sliders=sliders)
    # Update layout for equal axes
    fig.update_layout(
        xaxis=dict(
            scaleanchor='y',
            scaleratio=1,
        ),
        yaxis=dict(
            scaleanchor='x',
            scaleratio=1,
        ),
    )

    return fig


def plot_storage_level(scenario_folder: str):

    df = dh.load_storage_level(scenario_folder)
    columns = df.columns[2:]
    # remove columns with only 0 values
    columns = [col for col in columns if df[col].sum() != 0]
    num_h = df['h'].nunique()
    # create a range slider



    # create the figure
    fig = go.Figure()

    # add traces

    for idx, column in enumerate(columns):
        fig.add_trace(go.Scatter(x=df['h'], y=df[column], name=column))

    # add range slider

    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
                visible=True
            ),     
           
        )
    )

    return fig

   


