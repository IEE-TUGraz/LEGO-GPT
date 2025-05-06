from dash_extensions.javascript import assign
import pandas as pd
import numpy as np

class MarkerJS:
    """
    MarkerJS is a class designed to generate custom Leaflet markers and clusters with pie chart visualizations. 
    It provides methods to create individual markers and cluster markers, leveraging SVG pie charts to represent data.
    Attributes:
        scale_factor (float): A scaling factor calculated based on the mean of the square root of the 'values' column 
            in the provided DataFrame.
        min_radius (float): The minimum radius for the pie chart markers, derived from the provided map options.
    Methods:
        pie_svg():
            Returns a JavaScript function as a string that generates an SVG pie chart based on input options.
        pointToLayer():
            Generates a JavaScript function as a string that creates a Leaflet marker with a pie chart icon 
            for individual data points. The marker includes a tooltip displaying the data values and labels.
        clusterToLayer():
            Generates a JavaScript function as a string that creates a Leaflet marker with a pie chart icon 
            for clusters of data points. The marker includes a tooltip summarizing the cluster's data values and labels.
    """

    def __init__(self, map_options: dict, vGenP: pd.DataFrame):
        """
        Initializes the MarkerJS class with map options and a DataFrame.
        Args:
            map_options (dict): A dictionary containing configuration options for the map.
            vGenP (pd.DataFrame): A pandas DataFrame containing data from generating units.
        Attributes:
            scale_factor (float): A scaling factor calculated as the inverse of the square 
                root of the mean of the 'values' column in the provided DataFrame.
            min_radius (Any): The minimum radius for pie charts, extracted from the 
                map_options dictionary.
        """

        self.scale_factor = 1 / (np.sqrt(vGenP['values']).mean() )
        self.min_radius = map_options["pie_chart_min_radius"]

    @staticmethod
    def pie_svg():
        """
        Generates an SVG representation of a pie chart using JavaScript.

        The `pie_svg` method returns a JavaScript function as a string. This function, `pieSVG`, 
        creates an SVG pie chart based on the provided options. It calculates the necessary 
        coordinates and angles for each slice of the pie chart and generates the corresponding 
        SVG path elements.
        Returns:
            str: A JavaScript function as a string that generates an SVG pie chart.
        JavaScript Function Details:
            - `getCoords(cx, cy, radius, angle)`: Calculates the x and y coordinates for a 
            point on a circle given its center, radius, and angle.
            - `describeSlice(cx, cy, r, startAngle, endAngle, isFullCircle)`: Generates the 
            SVG path description for a pie slice or a full circle.
            - `pieSVG(opt)`: Main function that generates the SVG pie chart. Accepts an options 
            object (`opt`) with the following properties:
                - `width` (int): Width of the SVG canvas (default: 60).
                - `height` (int): Height of the SVG canvas (default: 60).
                - `radius` (int): Radius of the pie chart (default: 20).
                - `fontSize` (int): Font size for labels (default: 14).
                - `values` (list): List of numerical values representing the pie slices 
                (default: [10, 10, 10]).
                - `colors` (list): List of colors for the pie slices (default: ['green', 'orange', 'red']).
        Behavior:
            - If the sum of `values` is 0, a placeholder full circle is drawn.
            - Otherwise, the function calculates the angles for each slice based on the 
            proportions of the `values` array and generates the corresponding SVG paths.
        Example Usage:
            The returned JavaScript function can be embedded in an HTML file or executed in a 
            JavaScript environment to generate a pie chart SVG.
            """
        
        return """
        function pieSVG(opt) {
            function getCoords(cx, cy, radius, angle) {
                const rad = (angle - 90) * Math.PI / 180;
                return {
                    x: cx + radius * Math.cos(rad),
                    y: cy + radius * Math.sin(rad)
                };
            }

            function describeSlice(cx, cy, r, startAngle, endAngle, isFullCircle = false) {
                if (isFullCircle) {
                    const midAngle = startAngle + 180;
                    const start = getCoords(cx, cy, r, startAngle);
                    const mid = getCoords(cx, cy, r, midAngle);
                    const end = getCoords(cx, cy, r, endAngle);
                    return [
                        "M", start.x, start.y,
                        "A", r, r, 0, 1, 1, mid.x, mid.y,
                        "A", r, r, 0, 1, 1, end.x, end.y,
                        "Z"
                    ].join(" ");
                } else {
                    const start = getCoords(cx, cy, r, startAngle);
                    const end = getCoords(cx, cy, r, endAngle);
                    const largeArc = (endAngle - startAngle) > 180 ? 1 : 0;
                    return [
                        "M", cx, cy,
                        "L", start.x, start.y,
                        "A", r, r, 0, largeArc, 1, end.x, end.y,
                        "Z"
                    ].join(" ");
                }
            }

            opt = Object.assign({
                width: 60,
                height: 60,
                radius: 20,
                fontSize: 14,
                values: [10, 10, 10],
                colors: ['green', 'orange', 'red']
            }, opt);
            const sum = opt.values.reduce((a, b) => a + b, 0);
            let startAngle = 0;
            let paths = '';

            if (sum === 0) {
                // Draw a placeholder circle (e.g., gray full circle)
                const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, 0, 360, true);
                paths += `<path fill="${opt.colors[0]}" d="${d}"></path>`;
            } else {
                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const isFullCircle = sliceAngle === 360;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle, isFullCircle);
                    paths += `<path fill="${opt.colors[i % opt.colors.length]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }
            }


            return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
        }
        """

    def pointToLayer(self):
        """
        Creates a Leaflet marker with a custom pie chart icon and binds a tooltip to it.
        This method generates a JavaScript function that defines how GeoJSON points 
        are converted into Leaflet markers. Each marker is represented by a pie chart 
        icon, which is dynamically created based on the feature's properties.
        Returns:
            str: A JavaScript function as a string that defines the point-to-layer 
            behavior for Leaflet.
        The generated JavaScript function performs the following:
        - Extracts `values`, `colors`, and `labels` from the feature's properties.
        - Calculates the total of the `values` array and determines the radius of 
          the pie chart based on the total and scaling factors.
        - Creates a custom Leaflet `divIcon` using the `pieSVG` function to render 
          the pie chart.
        - Configures the icon's size and anchor point based on the calculated radius.
        - Creates a Leaflet marker at the given latitude and longitude (`latlng`) 
          with the custom icon.
        - Binds a tooltip to the marker, displaying the feature's name and a 
          breakdown of the values with corresponding colors and labels.
        Note:
            - The `pieSVG` function is expected to generate the SVG representation 
              of the pie chart.
            - The `self.min_radius` and `self.scale_factor` attributes are used to 
              calculate the pie chart's radius.
        """


        return assign(f"""function(feature, latlng) {{
        {self.pie_svg()}

        const values = feature.properties.values;
        const colors = feature.properties.colors;
        const labels = feature.properties.labels;
        const total = values.reduce((a, b) => a + b, 0);
        const radius = {self.min_radius} + Math.sqrt(total) * {self.scale_factor:.6f};
        const scale = radius * 2.5;

        const icon = L.divIcon({{
            html: pieSVG({{
                values: values,
                colors: colors,
                width: scale,
                height: scale,
                radius: radius,
                fontSize: 10
            }}),
            className: "custom-marker",
            iconSize: L.point(scale, scale),
            iconAnchor: [scale / 2, scale / 2]
        }});

        const marker = L.marker(latlng, {{ icon: icon }});
        marker.bindTooltip(
            `<b>${{feature.properties.name}}</b><br/>` +
            values.map((val, i) => {{
                const color = colors[i];
                const label = labels[i];
                return `<span style="color:${{color}}">&#9679;</span> ${{label}}: ${{val}}`;
            }}).join("<br/>"),
            {{
                direction: 'top',
                offset: [0, -scale / 2],
                opacity: 0.9
            }}
        );
        return marker;
    }}""")
    
    def clusterToLayer(self):
        """
        Generates a JavaScript function to create a custom Leaflet marker cluster layer.
        This method constructs a JavaScript function that defines how to render a cluster
        of markers on a Leaflet map. It uses pie chart SVGs to visually represent the 
        aggregated data within each cluster. The function is returned as a string and 
        can be used in a JavaScript context.
        Returns:
            str: A JavaScript function as a string that defines the behavior and appearance
                 of marker clusters on a Leaflet map.
        The generated JavaScript function performs the following:
        - Aggregates data from the cluster's leaves (individual markers).
        - Calculates the total values and proportions for each category in the cluster.
        - Dynamically generates a pie chart SVG to represent the data distribution.
        - Creates a custom Leaflet marker with the pie chart as its icon.
        - Binds a tooltip to the marker displaying detailed information about the cluster.
        """


        return assign(f"""function(feature, latlng, index, context) {{
        {self.pie_svg()}

            const leaves = index.getLeaves(feature.properties.cluster_id, Infinity);
            const colorIndex = {{}};
            const labelMap = {{}};
            const colorSums = [];

            for (let i = 0; i < leaves.length; i++) {{
                const values = leaves[i].properties.values;
                const colors = leaves[i].properties.colors;
                const labels = leaves[i].properties.labels;

                for (let j = 0; j < values.length; j++) {{
                    const color = colors[j];
                    const label = labels[j];
                    if (colorIndex[color] === undefined) {{
                        colorIndex[color] = colorSums.length;
                        colorSums.push(0);
                        labelMap[color] = label;
                    }}
                    colorSums[colorIndex[color]] += values[j];
                }}
            }}

            const orderedColors = Object.keys(colorIndex).sort((a, b) => colorIndex[a] - colorIndex[b]);
            const orderedValues = orderedColors.map(color => colorSums[colorIndex[color]]);
            const orderedLabels = orderedColors.map(color => labelMap[color]);
            const total = orderedValues.reduce((a, b) => a + b, 0);
            const radius = {self.min_radius} + Math.sqrt(total) * {self.scale_factor:.6f};
            const scale = radius * 2.5;

            const icon = L.divIcon({{
                html: pieSVG({{
                    values: orderedValues,
                    colors: orderedColors,
                    width: scale,
                    height: scale,
                    radius: radius,
                    fontSize: 12
                }}),
                className: "marker-cluster",
                iconSize: L.point(scale, scale),
                iconAnchor: [scale / 2, scale / 2]
            }});

            const marker = L.marker(latlng, {{ icon: icon }});
            marker.bindTooltip(
                `Cluster of ${{leaves.length}} Sites<br/>` +
                orderedValues.map((val, i) => {{
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${{color}}">&#9679;</span> ${{label}}: ${{val.toFixed(1)}}`;
                }}).join("<br/>"),
                {{
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }}
            );

            return marker;
        }}""")
           