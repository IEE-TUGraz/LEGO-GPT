"""
Kaleido Export Worker (internal)

Renders a Plotly figure to a static image file in a standalone process.

Invoking Kaleido from within the running Dash server process was observed
to be dramatically slower and prone to timing out (tens of seconds, vs. a
consistent ~2s in a fresh process) on some Windows setups - likely an
asyncio/subprocess interaction with the dev server's own event loop. Running
the export in its own short-lived process sidesteps that entirely, at the
cost of a small, predictable interpreter-startup overhead.

Usage: python _kaleido_worker.py <figure_json_path> <output_path> <format> <kwargs_json>
"""

import json
import sys

import plotly.graph_objects as go


def main() -> None:
    figure_path, output_path, fmt, kwargs_json = sys.argv[1:5]

    with open(figure_path, "r", encoding="utf-8") as f:
        figure_dict = json.load(f)

    kwargs = json.loads(kwargs_json)
    fig = go.Figure(figure_dict)
    fig.write_image(output_path, format=fmt, **kwargs)


if __name__ == "__main__":
    main()
