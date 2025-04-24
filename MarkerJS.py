from dash_extensions.javascript import assign
import pandas as pd
import numpy as np

class MarkerJS:

    def __init__(self, map_options: dict, vGenP: pd.DataFrame):
        self.scale_factor = 1 / (np.sqrt(vGenP['values']).mean() )
        self.min_radius = map_options["pie_chart_min_radius"]

    @staticmethod
    def pie_svg():
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
           