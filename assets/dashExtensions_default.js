window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, layer) {
            layer.bindPopup(feature.properties.popup);
        },
        function1: function(feature, latlng) {

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


            // --- 1. Get all properties from the feature ---
            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const nodeName = feature.properties.name;
            const voltage = feature.properties.voltage;
            const voltageMin = feature.properties.voltage_min;
            const voltageMax = feature.properties.voltage_max;
            const showVoltage = feature.properties.show_voltage !== false;
            const total = values.reduce((a, b) => a + b, 0);
            const raw_radius = 6 + Math.sqrt(total) * 25.443103;
            const radius = Math.min(raw_radius, 16);
            const scale = radius * 2.5;

            const icon = L.divIcon({
                html: pieSVG({
                    values: values,
                    colors: colors,
                    width: scale,
                    height: scale,
                    radius: radius,
                    fontSize: 10
                }),
                className: "custom-marker",
                iconSize: L.point(scale, scale),
                iconAnchor: [scale / 2, scale / 2]
            });

            const marker = L.marker(latlng, {
                icon: icon
            });

            // This is always visible and does not require hover.
            const tooltipHtml = showVoltage ?
                `<div style="font-weight: bold; font-size: 11px; color: black; text-align: center;">${nodeName}<br/>${voltage}</div>` :
                `<div style="font-weight: bold; font-size: 11px; color: black; text-align: center;">${nodeName}</div>`;
            marker.bindTooltip(
                tooltipHtml, {
                    permanent: true,
                    direction: 'bottom',
                    offset: [0, scale / 2 + 5], // Position below the icon
                    opacity: 0.9,
                    className: 'node-label-tooltip' // For custom CSS
                }
            );

            // This appears *only* on hover (or click).
            var popupContent = `<b>${nodeName}</b> (${voltage})<br/>` +
                `Min Voltage: ${voltageMin}<br/>` +
                `Max Voltage: ${voltageMax}<br/>` +
                `<hr style="margin: 3px 0;"/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>");

            marker.bindPopup(popupContent, {
                offset: [0, -scale / 2] // Position above the icon
            });

            marker.on('mouseover', function(e) {
                this.openPopup();
            });

            marker.on('mouseout', function(e) {
                this.closePopup();
            });

            return marker;
        },
        function2: function(feature, latlng, index, context) {

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


            const leaves = index.getLeaves(feature.properties.cluster_id, Infinity);
            const colorIndex = {};
            const labelMap = {};
            const colorSums = [];

            for (let i = 0; i < leaves.length; i++) {
                const values = leaves[i].properties.values;
                const colors = leaves[i].properties.colors;
                const labels = leaves[i].properties.labels;

                for (let j = 0; j < values.length; j++) {
                    const color = colors[j];
                    const label = labels[j];
                    if (colorIndex[color] === undefined) {
                        colorIndex[color] = colorSums.length;
                        colorSums.push(0);
                        labelMap[color] = label;
                    }
                    colorSums[colorIndex[color]] += values[j];
                }
            }

            const orderedColors = Object.keys(colorIndex).sort((a, b) => colorIndex[a] - colorIndex[b]);
            const orderedValues = orderedColors.map(color => colorSums[colorIndex[color]]);
            const orderedLabels = orderedColors.map(color => labelMap[color]);
            const total = orderedValues.reduce((a, b) => a + b, 0);
            const raw_radius = 6 + Math.sqrt(total) * 25.443103;
            const radius = Math.min(raw_radius, 16);
            const scale = radius * 2.5;

            const icon = L.divIcon({
                html: pieSVG({
                    values: orderedValues,
                    colors: orderedColors,
                    width: scale,
                    height: scale,
                    radius: radius,
                    fontSize: 12
                }),
                className: "marker-cluster",
                iconSize: L.point(scale, scale),
                iconAnchor: [scale / 2, scale / 2]
            });

            const marker = L.marker(latlng, {
                icon: icon
            });

            // Compact hover tooltip with limited information
            const tooltipContent = `<div style="font-size: 10px; padding: 2px 4px;"><b>Cluster (${leaves.length})</b></div>`;

            marker.bindTooltip(
                tooltipContent, {
                    permanent: false,
                    direction: 'top',
                    offset: [0, -scale / 2 - 5],
                    opacity: 0.75,
                    className: 'compact-cluster-tooltip'
                }
            );

            return marker;
        }
    }
});