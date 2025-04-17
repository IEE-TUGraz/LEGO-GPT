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
                    text: '',
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

                return `<svg width="${opt.width}" height="${opt.height}">
                ${paths}
            </svg>`;
            }


            const cat1 = feature.properties.cat1;
            const cat2 = feature.properties.cat2;
            const cat3 = feature.properties.cat3;
            const total = cat1 + cat2 + cat3;

            const radius = 6 + Math.sqrt(total) * 3.207135;
            const scale = radius * 2.5;

            const icon = L.divIcon({
                html: pieSVG({
                    values: [cat1, cat2, cat3],
                    colors: ['green', 'orange', 'red'],
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
                `<b>${feature.properties.name}</b><br/>
             Cat1: ${cat1}<br/>
             Cat2: ${cat2}<br/>
             Cat3: ${cat3}`, {
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
                    text: '',
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

                return `<svg width="${opt.width}" height="${opt.height}">
                ${paths}
            </svg>`;
            }


            const leaves = index.getLeaves(feature.properties.cluster_id, Infinity);
            let total1 = 0,
                total2 = 0,
                total3 = 0;
            for (let i = 0; i < leaves.length; ++i) {
                total1 += leaves[i].properties.cat1;
                total2 += leaves[i].properties.cat2;
                total3 += leaves[i].properties.cat3;
            }

            const total = total1 + total2 + total3;
            const radius = 6 + Math.sqrt(total) * 3.207135;
            const scale = radius * 2.5;

            const icon = L.divIcon({
                html: pieSVG({
                    values: [total1, total2, total3],
                    colors: ['green', 'orange', 'red'],
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
                `Cluster of ${leaves.length} Sites<br/>
             Total Cat1: ${total1}<br/>
             Total Cat2: ${total2}<br/>
             Total Cat3: ${total3}`, {
                    direction: 'top',
                    offset: [0, -scale / 2],
                    opacity: 0.9
                }
            );

            return marker;
        }
    }
});