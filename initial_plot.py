import dash
from dash import html
import dash_leaflet as dl
import pandas as pd
import os


# Load and prepare data
nodes = pd.read_excel(os.path.abspath("R:\\07_Datenbank\\Data_PyPSA\\largest_model\\Power_BusInfo.xlsx"), usecols="B,L,M", skiprows=5, names=["i", "lat", "lon"])
edges = pd.read_excel(os.path.abspath("R:\\07_Datenbank\\Data_PyPSA\\largest_model\\Power_Network.xlsx"), usecols="B,C", skiprows=5, names=["i", "j"])

print(nodes.head())
print(edges.head())

# Convert node list to dict for fast lookup
nodes_dict = nodes.set_index('i')[['lat', 'lon']].to_dict('index')

# Create circle markers for each node
markers = [
    dl.CircleMarker(
        center=(row['lat'], row['lon']),
        radius=5,
        color='blue',
        fill=True,
        fillOpacity=0.8,
        children=dl.Tooltip(name)
    ) for name, row in nodes_dict.items()
]

# Create lines for each edge
lines = []
for _, row in edges.iterrows():
    from_node = row['i']
    to_node = row['j']
    if from_node in nodes_dict and to_node in nodes_dict:
        lines.append(dl.Polyline(positions=[
            (nodes_dict[from_node]['lat'], nodes_dict[from_node]['lon']),
            (nodes_dict[to_node]['lat'], nodes_dict[to_node]['lon'])
        ]))

# Build Dash app
app = dash.Dash(__name__)
app.layout = html.Div([
    dl.Map(center=[42, 20], zoom=6, children=[
        dl.TileLayer(),
        dl.LayerGroup(markers + lines)
    ], style={"width": "100%", "height": "1200px"})
])

if __name__ == '__main__':
    app.run(debug=False)
