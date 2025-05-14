import os
import json
import pandas as pd
import yaml
import networkx as nx
from collections import defaultdict
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from NetworkPlotRenderer import NetworkPlotRenderer

class NetworkPlot:

    def __init__(self, json_data_path: os.path, network_level: str, powerplant_data_path: os.path, powerplant_sheet_name: str): 
        """
        Initializes the NetworkPlot object with the provided parameters and configuration.

        Args:
            json_data_path (os.path): The file path to the JSON data containing network information.
            network_level (str): The level of the network to be plotted (NOT USED).
            powerplant_data_path (os.path): The file path to the powerplant data file.
            powerplant_sheet_name (str): The name of the sheet in the powerplant data file to be used.

        Attributes:
            json_data_path (os.path): Stores the provided JSON data file path.
            network_level (str): Stores the provided network level.
            powerplant_data_path (os.path): Stores the provided powerplant data file path.
            powerplant_sheet_name (str): Stores the provided powerplant sheet name.
            config (dict): Configuration loaded from the "config.yml" file.
            mode (str): Graph style mode, defaulting to "default" if not specified in the configuration.
        """
        self.json_data_path = json_data_path
        self.network_level = network_level
        self.powerplant_data_path = powerplant_data_path
        self.powerplant_sheet_name = powerplant_sheet_name
        with open("config.yml", "r") as file:
            self.config = yaml.safe_load(file)
        self.mode = self.config.get("graph_style", {}).get("mode", "default")


    def load_json_data(self,):
        """
        Loads JSON data from a specified file path, parses it, and extracts graph nodes and edges.
        This method reads a JSON file from the path specified by `self.json_data_path`, 
        parses the JSON content to extract the graph structure, and assigns the nodes 
        and edges to `self.nodes` and `self.edges` respectively.
        Raises:
            FileNotFoundError: If the file specified by `self.json_data_path` does not exist.
            json.JSONDecodeError: If the file content is not valid JSON or if the JSON structure 
                                does not match the expected format.
        Attributes:
            self.nodes (list): A list of nodes extracted from the graph data.
            self.edges (list): A list of edges (links) extracted from the graph data.
        """
 
        ### Load JSON file ###
        with open(self.json_data_path, "r") as file:
            json_data = json.load(file)
        # Parse JSON
        graph_data = json.loads(json_data["data"])  # Extract actual graph structure
        
        # Extract nodes and edges
        self.nodes = graph_data["graph"]["nodes"]
        self.edges = graph_data["graph"]["links"]

    def load_powerplant_data(self):
        """
        Loads power plant data from an Excel sheet and processes generator configurations.
        This method reads the power plant data from the specified Excel file and sheet,
        processes the generator configurations defined in the `self.config`, and assigns
        the processed data to attributes of the class.
        Steps:
        1. Reads the raw power plant data from the Excel file.
        2. Normalizes generator types to create attribute names.
        3. Renames node identifiers in the data for better readability.
        4. Assigns the processed generator data to class attributes.
        Attributes:
            - Dynamically creates attributes for each generator type defined in the configuration.
            For example, a generator type "Wind" will create an attribute `self.wind`.
        Helper Functions:
            - `rename_nodes(node_list)`: Renames node identifiers from the format `VRES_Knoten_XX`
            to `Node XX`.
            - `normalize_gen_type(gen_type)`: Normalizes generator type strings by converting them
            to lowercase and replacing spaces and hyphens with underscores.
        Raises:
            - Any exceptions raised by `pandas.read_excel` if the file or sheet is not found.
            - AttributeError if the configuration or data processing fails.
        Note:
            Ensure that `self.powerplant_data_path` and `self.powerplant_sheet_name` are correctly
            set before calling this method. The `self.config` dictionary must also contain a
            "generators" key with the expected generator types.
        """
   
        # Load power plant Excel sheet
        powerplants_raw = pd.read_excel(self.powerplant_data_path, sheet_name=self.powerplant_sheet_name)

        # Get generator config
        generators_cfg = self.config.get("generators", {})

        # Helper: renames from VRES_Knoten_XX → Node XX
        def rename_nodes(node_list):
            return ["Node " + str(item).split("_")[-1] for item in node_list]
        
        def normalize_gen_type(gen_type):
            return gen_type.lower().replace(" ", "_").replace("-", "_")

        # Process each generator category
        for gen_type in generators_cfg:
            column = gen_type  # Excel column
            attribute_name = normalize_gen_type(gen_type)  # e.g., "wind" → "wind"

            raw_list = powerplants_raw[column].dropna().to_list()
            renamed_list = rename_nodes(raw_list)

            setattr(self, attribute_name, renamed_list)

    def create_graph(self):
        """
        Creates a network graph using the provided configuration, nodes, and edges.
        This method constructs a graph using the NetworkX library, applies styles and 
        configurations for nodes and edges, and computes positions for generator icons 
        based on the graph layout.
        Attributes:
            - self.config: A dictionary containing configuration options for the graph, 
              including styles, highlights, position overrides, and generator settings.
            - self.edges: A list of edges, where each edge is a dictionary containing 
              "source" and "target" node information.
            - self.nodes: A list of nodes, where each node is a dictionary containing 
              node attributes such as "name", "x", and "y".
            - self.mode: A string indicating the graph layout mode ("default" or "radial").
        Highlights:
            - Nodes and edges can be highlighted based on the configuration.
            - Node positions can be overridden using the configuration.
            - Generator icons are positioned relative to their associated nodes, with 
              support for both rectangular and radial layouts.
        Returns:
            None: The method updates the following instance attributes:
                - self.G: The constructed NetworkX graph.
                - self.positions: A dictionary mapping node IDs to their positions.
                - self.image_positions: A nested dictionary mapping generator types 
                  to node IDs and their respective image positions.
                - self.node_connections: A dictionary mapping each node to its connected nodes.
        Notes:
            - Edge and node styles are customizable through the configuration.
            - Radial layout computes angles for nodes to determine generator icon placement.
            - Debugging information is printed for nodes with specific image offsets.
        """

        G = nx.Graph()
        positions = {}
        image_positions = defaultdict(dict)

        # Pull highlight and override config
        highlight_nodes = self.config.get("highlight_nodes", [])
        highlight_edges = self.config.get("highlight_edges", [])
        position_overrides = self.config.get("node_position_overrides") or {}
        generators_config = self.config.get("generators", {})

        def normalize_gen_type(gen_type):
            return gen_type.lower().replace(" ", "_").replace("-", "_")
        
        generator_mapping = {
            gen_type: getattr(self, normalize_gen_type(gen_type))
            for gen_type in generators_config
        }

        # Extract edge styles
        edge_styles = self.config.get("edge_styles", {})
        default_edge_style = edge_styles.get("default", {"color": "black", "width": 1})
        highlight_edge_style = edge_styles.get("highlight", {"color": "#F70147", "width": 1.3})

        # Extract node styles
        node_styles = self.config.get("node_styles", {})
        default_node_style = node_styles.get("default", {})
        highlight_node_style = node_styles.get("highlight", {})

        # Process edges
        node_connections = defaultdict(list)
        for edge in self.edges:
            source = edge["source"]["name"]
            target = edge["target"]["name"]

            if source and target:
                if [source, target] in highlight_edges or [target, source] in highlight_edges:
                    color = highlight_edge_style["color"]
                    width = highlight_edge_style["width"]
                else:
                    color = default_edge_style["color"]
                    width = default_edge_style["width"]

                G.add_edge(source, target, color=color, width=width)
                node_connections[source].append(target)
                node_connections[target].append(source)

        # Compute angles
        self.angles = self.compute_dead_end_angles(node_connections)
        
        # Process nodes
        # Apply base node positions and generator icon placements
        for node in self.nodes:
            node_id = node["name"]
            if not node_id:
                continue

            # Base position from node data
            x = node["x"]
            y = -node["y"]

            # Apply node-specific position override (affects graph layout only)
            if node_id in position_overrides:
                override_x, override_y = position_overrides[node_id]
                if override_x is not None:
                    x = override_x
                if override_y is not None:
                    y = override_y

            # Store graph node
            # Determine node style
            if node_id in highlight_nodes:
                color = highlight_node_style.get("color", "#F70147")
                size = highlight_node_style.get("node_size", 9)
            else:
                color = default_node_style.get("color", "black")
                size = default_node_style.get("node_size", 9)          
            G.add_node(node_id, pos=(x, y), color=color, size=size)
            positions[node_id] = (x, y)

            # Handle generator icon positions
            for gen_type, gen_nodes in generator_mapping.items():
                if node_id not in gen_nodes:
                    continue
                
                if self.mode == "default": # rectangular styled network
                    # Base image offset from generator type config
                    dx, dy = generators_config[gen_type].get("offset", [0, 0]) 
                elif self.mode == "radial": # radial styled network
                    radius = self.config.get("graph_style", {}).get("radius_radial", 40)
                    angle = self.angles[node_id] if node_id in self.angles.keys() else 0
                    if angle < 90 and angle > -90:
                        dx, dy = -radius, 0
                    elif angle > 90 or angle < -90:
                        dx, dy = radius, 0
                    else:
                        r_dist = radius  # Distance from the node
                        dx = -r_dist * math.cos(math.radians(angle))
                        dy = r_dist * math.sin(math.radians(angle))

                # Apply image-specific offset for this node
                node_specific_offset = self.config.get("image_offsets", {}).get(gen_type, {}).get(node_id)
                if node_specific_offset:
                    print(f"Node {node_id} has specific offset for {gen_type}: {node_specific_offset}")
                    dx, dy = node_specific_offset

                # Store final image position based on current x, y
                image_positions[gen_type][node_id] = (x + dx, y + dy)

        self.G = G
        self.positions = positions
        self.image_positions = image_positions
        self.node_connections = node_connections

    def compute_dead_end_angles(self, node_connections: dict) -> dict:
        """
        Computes the angles of dead-end nodes relative to their connected nodes.
        A dead-end node is defined as a node with only one connection. This method
        calculates the angle (in degrees) between the dead-end node and its connected
        node, measured counterclockwise from the positive x-axis.
        Args:
            node_connections (dict): A dictionary where keys are node names and values
                are lists of connected node names.
        Returns:
            dict: A dictionary where keys are the names of dead-end nodes and values
                are the angles (in degrees) to their connected nodes.
        Notes:
            - The method assumes that `self.nodes` is a list of dictionaries, where
            each dictionary represents a node with the keys "name", "x", and "y"
            for the node's name and coordinates, respectively.
            - If either the dead-end node or its connected node is not found in
            `self.nodes`, that node is skipped.
        """
  
        angles = {}
        ending_nodes = {node: conns[0] for node, conns in node_connections.items() if len(conns) == 1}

        for end_node, connected_node in ending_nodes.items():
            # Find coordinates of both nodes
            end_coords = next((n for n in self.nodes if n["name"] == end_node), None)
            conn_coords = next((n for n in self.nodes if n["name"] == connected_node), None)

            if not end_coords or not conn_coords:
                continue

            x1, y1 = end_coords["x"], end_coords["y"]
            x2, y2 = conn_coords["x"], conn_coords["y"]

            # Compute angle
            angle_rad = math.atan2(y2 - y1, x2 - x1)
            angle_deg = round(math.degrees(angle_rad), 2)
            angles[end_node] = angle_deg

        return angles
    
    def render_network_plot(self, save_path=None, show=True):
        """
        Renders a network plot using the provided configuration and data.
        Args:
            save_path (str, optional): The file path where the plot will be saved. 
                                       If None, the plot will not be saved. Defaults to None.
            show (bool, optional): Whether to display the plot after rendering. 
                                   If True, the plot will be shown. Defaults to True.
        Returns:
            None
        """

        renderer = NetworkPlotRenderer(self.config)
        renderer.plot(
            G=self.G,
            positions=self.positions,
            image_positions=self.image_positions,
            node_connections=self.node_connections,
            angles=self.angles,
            save_path=save_path,
            show=show
        )


json_data_path = os.path.abspath("C:\\Users\\Kelvin Walenta\\JSONGraphPlotter\\networks\\network_both_MV.json")
network_level = "MV"
powerplant_data_path = os.path.abspath("C:\\Users\\Kelvin Walenta\\JSONGraphPlotter\\networks\\Kraftwerke_MS.xlsx")
sheet_name = "gemischt"


net = NetworkPlot(json_data_path, network_level, powerplant_data_path, sheet_name)
net.load_json_data()
net.load_powerplant_data()
net.create_graph()
net.render_network_plot(show=True)  # or save_path="my_plot.png"
