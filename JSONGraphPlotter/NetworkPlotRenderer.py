import os
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from shapely.geometry import box
from shapely.ops import unary_union
import networkx as nx

class NetworkPlotRenderer:
    def __init__(self, config):
        """
        Initializes the NetworkPlotRenderer instance with the given configuration.

        Args:
            config (dict): A dictionary containing configuration settings for the renderer.
        """
        self.config = config

    def plot(self, G, positions, image_positions, node_connections, angles, save_path=None, show=True):
        """
        Plots a network graph with customized styles, node labels, generator icons, and legends.
        Args:
            G (networkx.Graph): The graph to be plotted.
            positions (dict): A dictionary mapping node IDs to their (x, y) positions.
            image_positions (dict): A dictionary mapping node IDs to positions for generator icons.
            node_connections (dict): A dictionary of node connections (not used in this function).
            angles (dict): A dictionary mapping node IDs to angles for label and icon orientation.
            save_path (str, optional): File path to save the plot as an image. Defaults to None.
            show (bool, optional): Whether to display the plot interactively. Defaults to True.
        Config Attributes:
            - graph_style (dict): Configuration for graph appearance, including:
                - "scale_factor" (float): Scaling factor for the graph dimensions. Defaults to 1.0.
                - "dpi" (int): Resolution of the plot in dots per inch. Defaults to 150.
            - node_styles (dict): Configuration for node-specific styles (not used directly in this function).
        Behavior:
            - Calculates the width and height of the plot based on node positions and scale factor.
            - Extracts edge colors, edge widths, and node colors from the graph attributes.
            - Draws the graph using NetworkX with the specified styles.
            - Adds node labels, generator icons, an outline, and a legend to the plot.
            - Saves the plot to the specified file path if `save_path` is provided.
            - Displays the plot interactively if `show` is True; otherwise, closes the plot.
        Raises:
            KeyError: If required attributes (e.g., "color", "width") are missing in the graph edges or nodes.
        """

        graph_style = self.config.get("graph_style", {})
        node_styles = self.config.get("node_styles", {})
        scale_factor = graph_style.get("scale_factor", 1.0)
        dpi = graph_style.get("dpi", 150)

        xs, ys = zip(*positions.values())
        width = (max(xs) - min(xs)) * scale_factor
        height = (max(ys) - min(ys)) * scale_factor

        edge_colors = [G[u][v]["color"] for u, v in G.edges()]
        edge_widths = [G[u][v]["width"] for u, v in G.edges()]
        node_colors = [G.nodes[n]["color"] for n in G.nodes()]

        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        ax.set_aspect('equal')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        nx.draw(G, pos=positions, ax=ax, with_labels=False,
                node_color=node_colors, edge_color=edge_colors,
                node_size=9, width=edge_widths)

        self._add_node_labels(ax, positions, angles)
        self._add_generator_icons(ax, image_positions, angles)
        self._add_outline(ax, positions)
        self._add_legend(fig, ax)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
        if show:
            plt.show()
        else:
            plt.close()

    def _add_node_labels(self, ax, positions, angles):
        """
        Adds labels to nodes on the plot.

        This method places text labels near each node on the plot, with their
        positions and orientations determined by the provided `positions` and
        `angles` dictionaries. The labels are styled with a specific font and
        formatting.

        Args:
            ax (matplotlib.axes.Axes): The matplotlib Axes object where the labels
                will be added.
            positions (dict): A dictionary mapping node IDs to their (x, y)
                coordinates on the plot.
            angles (dict): A dictionary mapping node IDs to their respective angles
                (in degrees or radians) used to determine label placement.

        Returns:
            None
        """
        for node_id, (x, y) in positions.items():
            angle = angles.get(node_id)
            offset_x, offset_y, ha, va = self._label_offset(angle)
            ax.text(x + offset_x, y + offset_y, f"{node_id:<8}",
                    fontsize=4, fontweight="bold", ha=ha, va=va,
                    color="black", fontfamily="Consolas",
                    bbox=dict(facecolor="white", linewidth=0, alpha=0.0))

    def _label_offset(self, angle):
        """
        Calculate the label offset and alignment based on the given angle.
        (SHOULD BE MOVED TO CONFIG)

        This method determines the x and y offset values, as well as the horizontal 
        and vertical alignment for a label, based on the provided angle.

        Args:
            angle (float or None): The angle in degrees. If None, a default offset 
                and alignment are returned.

        Returns:
            tuple: A tuple containing:
                - x_offset (int): The horizontal offset for the label.
                - y_offset (int): The vertical offset for the label.
                - horizontal_align (str): The horizontal alignment ("left", "right", or "center").
                - vertical_align (str): The vertical alignment ("top" or "center").
        """
        if angle is None:
            return -5, -18, "center", "top"
        if angle < -90:
            return -5, -18, "left", "top"
        elif -90 < angle < 0:
            return 5, -18, "right", "top"
        elif 0 < angle < 90:
            return 5, -18, "right", "top"
        elif 90 < angle < 180:
            return -5, -18, "left", "top"
        elif angle == 90:
            return -5, -18, "center", "top"
        else:
            return -5, -18, "center", "top"

    def _add_generator_icons(self, ax, image_positions, angles):
        """
        Adds generator icons to the plot based on the specified positions and configurations.
        Args:
            ax (matplotlib.axes.Axes): The matplotlib Axes object where the icons will be added.
            image_positions (dict): A dictionary where keys are generator types (str) and values are 
                dictionaries mapping node IDs (str) to their (x, y) positions (tuple) on the plot.
            angles (dict): A dictionary mapping node IDs (str) to their respective angles (float). 
                (Currently unused in the function.)
        Config Requirements:
            The function expects a "generators" configuration in `self.config` with the following structure:
            {
                "generator_type": {
                    "image": "filename.png",  # Path to the generator icon image.
                    "zoom": float,           # Optional zoom level for the icon (default is 0.05).
                },
                ...
            }
        Behavior:
            - For each generator type, the function attempts to load the corresponding icon image.
            - If the image file is missing, a warning is printed, and the generator type is skipped.
            - The icons are added to the plot at the specified positions with the configured zoom level.
        Warnings:
            Prints a warning message if the icon image for a generator type is not found.
        Dependencies:
            - Requires `os`, `matplotlib.image` (as `mpimg`), and `matplotlib.offsetbox.AnnotationBbox` 
              and `matplotlib.offsetbox.OffsetImage` for image handling and annotation.
        """

        generators_cfg = self.config.get("generators", {})
        for gen_type, image_nodes in image_positions.items():
            # img_path = f"icons/{gen_type.lower().replace(' ', '_')}.png"
            img_path = os.path.join("icons", f"{generators_cfg[gen_type]['image']}")
            if not os.path.exists(img_path):
                print(f"[Warning] Missing icon for {gen_type}")
                continue
            img = mpimg.imread(img_path)
            zoom = generators_cfg[gen_type].get("zoom", 0.05)

            for node_id, (x, y) in image_nodes.items():
                ab = AnnotationBbox(OffsetImage(img, zoom=zoom),
                                    (x, y), frameon=False, pad=0.4)
                ax.add_artist(ab)

    def _add_outline(self, ax, positions):
        """
        Adds an outline to the plot based on the configuration provided.
        This method modifies the plot by adding an outline around specified nodes
        and connecting them with lines or rectangles as defined in the configuration.
        Args:
            ax (matplotlib.axes.Axes): The matplotlib Axes object where the outline will be drawn.
            positions (dict): A dictionary mapping node identifiers to their (x, y) positions.
        Configuration:
            The method relies on an "outline" configuration dictionary, which may contain:
            - "added_nodes" (dict): A dictionary of additional nodes to be added, where each key is
              the new node's identifier, and the value is a dictionary with:
                - "base" (str): The identifier of the base node.
                - "dx" (float): The x-offset from the base node.
                - "dy" (float): The y-offset from the base node.
            - "lines" (list of tuples): A list of tuples, where each tuple contains two node
              identifiers (n1, n2) that define a line segment to be drawn.
        Behavior:
            - Adds additional nodes based on the "added_nodes" configuration.
            - Draws rectangles around the lines connecting specified nodes in the "lines" configuration.
            - Merges overlapping rectangles into a single polygon and plots it as a dashed outline.
        Note:
            This method assumes the presence of the `shapely.geometry.box` and
            `shapely.ops.unary_union` functions for geometric operations.
        Returns:
            None
        """
        outline_cfg = self.config.get("outline", {})
        if not outline_cfg:
            return

        nodes = positions.copy()
        xs, ys = zip(*nodes.values())


        for new_node, info in outline_cfg.get("added_nodes", {}).items():
            base = info["base"]
            dx, dy = info["dx"], info["dy"]
            if base in nodes:
                x, y = nodes[base]
                nodes[new_node] = (x + dx, y + dy)

        rectangles = []
        for n1, n2 in outline_cfg.get("lines", []):
            if n1 in nodes and n2 in nodes:
                x1, y1 = nodes[n1]
                x2, y2 = nodes[n2]
                if x1 == x2:
                    rect = box(x1 - 82, min(y1, y2) - 82, x1 + 82, max(y1, y2) + 82)
                elif y1 == y2:
                    rect = box(min(x1, x2) - 82, y1 - 82, max(x1, x2) + 82, y1 + 82)
                else:
                    continue
                rectangles.append(rect)

        merged = unary_union(rectangles)
        if merged.geom_type == "Polygon":
            bx, by = merged.exterior.xy
            ax.plot(bx, by, 'k--', linewidth=1)

    def _add_legend(self, fig, ax):
        """
        Adds a custom legend to the given matplotlib figure and axis.
        This method reads legend configuration from the `self.config` object and 
        dynamically places legend elements (icons and labels) on the figure. Each 
        legend element consists of an image and a corresponding text label.
        Args:
            fig (matplotlib.figure.Figure): The matplotlib figure to which the legend 
                will be added.
            ax (matplotlib.axes.Axes): The matplotlib axis associated with the figure.
        Legend Configuration (self.config["legend"]):
            - position (dict): Specifies the absolute position of the legend.
                - x_abs (float): The x-coordinate in inches for the starting position.
                - y_abs (float): The y-coordinate in inches for the starting position.
            - spacing (dict): Specifies the spacing between legend elements.
                - x (float): Horizontal spacing between elements in inches.
            - elements (list): A list of legend elements, where each element is a dict 
              containing:
                - label (str): The text label for the legend element.
                - file (str): The filename of the icon image (located in the "icons" directory).
                - zoom (float, optional): The zoom factor for the icon image. Defaults to 0.05.
        Notes:
            - The method uses the `AnnotationBbox` and `OffsetImage` classes to place 
              images on the figure.
            - Text labels are added next to the images using `fig.text`.
            - If an icon file does not exist, the corresponding legend element is skipped.
        """
        legend_cfg = self.config.get("legend", {})
        if not legend_cfg:
            return

        x_abs = legend_cfg["position"]["x_abs"]
        y_abs = legend_cfg["position"]["y_abs"]
        spacing_x = legend_cfg["spacing"]["x"]
        fig_width, fig_height = fig.get_size_inches()
        dpi = fig.dpi

        for item in legend_cfg["elements"]:
            label = item["label"]
            file = item["file"]
            zoom = item.get("zoom", 0.05)
            path = os.path.join("icons", file)

            if not os.path.exists(path):
                continue

            img = mpimg.imread(path)
            x_rel = x_abs / fig_width
            y_rel = y_abs / fig_height
            ab = AnnotationBbox(OffsetImage(img, zoom=zoom),
                                (x_rel, y_rel), frameon=False,
                                xycoords='figure fraction')
            fig.add_artist(ab)

            text = fig.text(x_rel + 0.01, y_rel, label, ha="left", va="center",
                            fontsize=5, fontweight="bold")
            renderer = fig.canvas.get_renderer()
            bbox = text.get_window_extent(renderer=renderer)
            text_width = bbox.width / dpi
            x_abs += text_width + spacing_x
