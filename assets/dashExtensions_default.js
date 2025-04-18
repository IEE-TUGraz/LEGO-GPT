window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.027749;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function1: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.027749;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function2: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.027079;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function3: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.027079;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function4: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.024150;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function5: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.024150;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function6: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.023217;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function7: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.023217;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function8: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.025728;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function9: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.025728;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function10: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.033189;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function11: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.033189;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function12: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.027451;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function13: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.027451;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function14: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.033955;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function15: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.033955;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function16: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.031080;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function17: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.031080;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function18: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.028197;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function19: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.028197;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function20: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.026047;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function21: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.026047;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function22: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.022367;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function23: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.022367;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function24: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.034534;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function25: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.034534;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function26: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.023569;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function27: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.023569;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function28: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.028518;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function29: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.028518;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function30: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.026869;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function31: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.026869;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function32: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.026658;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function33: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.026658;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        },
        function34: function(feature, latlng) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
                }

                return `<svg width="${opt.width}" height="${opt.height}">${paths}</svg>`;
            }


            const values = feature.properties.values;
            const colors = feature.properties.colors;
            const labels = feature.properties.labels;
            const total = values.reduce((a, b) => a + b, 0);
            const radius = 8 + Math.sqrt(total) * 0.030139;
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
            marker.bindTooltip(
                `<b>${feature.properties.name}</b><br/>` +
                values.map((val, i) => {
                    const color = colors[i];
                    const label = labels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );
            return marker;
        },
        function35: function(feature, latlng, index, context) {

            function pieSVG(opt) {
                function getCoords(cx, cy, radius, angle) {
                    const rad = (angle - 90) * Math.PI / 180;
                    return {
                        x: cx + radius * Math.cos(rad),
                        y: cy + radius * Math.sin(rad)
                    };
                }

                function describeSlice(cx, cy, r, startAngle, endAngle) {
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

                for (let i = 0; i < opt.values.length; i++) {
                    const sliceAngle = (opt.values[i] / sum) * 360;
                    const endAngle = startAngle + sliceAngle;
                    const d = describeSlice(opt.width / 2, opt.height / 2, opt.radius, startAngle, endAngle);
                    paths += `<path fill="${opt.colors[i]}" d="${d}"></path>`;
                    startAngle = endAngle;
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
            const radius = 8 + Math.sqrt(total) * 0.030139;
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
            marker.bindTooltip(
                `Cluster of ${leaves.length} Sites<br/>` +
                orderedValues.map((val, i) => {
                    const color = orderedColors[i];
                    const label = orderedLabels[i];
                    return `<span style="color:${color}">&#9679;</span> ${label}: ${val}`;
                }).join("<br/>"), {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        }
    }
});