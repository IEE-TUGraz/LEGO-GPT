"""
Static Map Export Module for LEGO-GPT

Renders the network map (line loads + nodal generation pies) as a vector
figure (SVG/PDF/PNG) directly from the same filtered data used by the
interactive Leaflet map. This bypasses the DOM/raster-tile stack entirely,
so the line and pie-marker geometry is drawn as true vector paths rather
than captured as a screenshot.

Input is the plain-data dict produced by
`NetworkMapGenerator.get_export_data()` in ui_handler.py - this module has
no dependency on Dash or Leaflet.
"""

import io
import math
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Headless backend - rendering only ever targets an in-memory buffer.
import contextily as ctx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Patch

# =============================================================================
# Pie Marker Construction
# =============================================================================

def _pie_wedge_markers(values: list[float]) -> list[np.ndarray]:
    """
    Build unit-circle wedge marker paths, one per value, in slice order.

    Each returned array is a set of (x, y) vertices (radius 1, centered at
    the origin) suitable for use as a matplotlib scatter `marker`.
    """
    total = sum(values)
    if total <= 0:
        theta = np.linspace(0, 2 * np.pi, 100)
        return [np.column_stack([np.cos(theta), np.sin(theta)])]

    markers = []
    start = 0.0
    for value in values:
        frac = value / total
        end = start + frac
        n_points = max(2, int(60 * frac) + 2)
        theta = np.linspace(2 * np.pi * start, 2 * np.pi * end, n_points)
        x = np.concatenate([[0], np.cos(theta), [0]])
        y = np.concatenate([[0], np.sin(theta), [0]])
        markers.append(np.column_stack([x, y]))
        start = end

    return markers


# =============================================================================
# Figure Rendering
# =============================================================================

def render_network_figure(
        export_data: dict[str, Any],
        fmt: str = "svg",
        figsize: tuple[float, float] = (12, 9),
) -> bytes:
    """
    Render the network (line loads + nodal generation pies) as a vector figure.

    Args:
        export_data: Output of NetworkMapGenerator.get_export_data().
        fmt: Output format - "svg", "pdf", or "png".
        figsize: Figure size in inches.

    Returns:
        Raw bytes of the rendered figure.
    """
    fig, ax = plt.subplots(figsize=figsize, dpi=150)

    _draw_lines(ax, export_data)
    legend_handles = _draw_nodes(ax, export_data)

    ax.margins(0.08)
    _add_basemap(ax)
    ax.set_aspect("equal", adjustable="box")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    title = _build_title(export_data)
    if title:
        ax.set_title(title)

    if legend_handles:
        ax.legend(
            handles=legend_handles,
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            fontsize=8,
            title="Generation",
            frameon=False,
        )

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def _add_basemap(ax) -> None:
    """
    Add the CARTO Positron basemap as a background raster layer.

    Tiles are fetched over the network and embedded as a single raster image
    beneath the vector line/pie layers - the same "light_all" CARTO style
    used by the live Leaflet map. Network/tile-server failures are non-fatal:
    the export still succeeds, just without the background image.
    """
    try:
        ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.CartoDB.Positron)
    except Exception as exc:
        print(f"  [Map Export] Could not fetch basemap tiles ({exc}); exporting without basemap.")


def _draw_lines(ax, export_data: dict[str, Any]) -> None:
    """Draw line-load polylines with a small arrow marking flow direction."""
    line_weight = export_data.get("line_weight", 2)

    for line in export_data.get("lines", []):
        (lat1, lon1), (lat2, lon2) = line["positions"]
        color = line["color"]

        ax.plot(
            [lon1, lon2], [lat1, lat2],
            color=color, linewidth=line_weight, zorder=1, solid_capstyle="round",
        )

        mid_lon, mid_lat = (lon1 + lon2) / 2, (lat1 + lat2) / 2
        dx, dy = (lon2 - lon1) * 0.06, (lat2 - lat1) * 0.06
        if dx == 0 and dy == 0:
            continue

        arrow = FancyArrowPatch(
            (mid_lon - dx, mid_lat - dy), (mid_lon + dx, mid_lat + dy),
            arrowstyle="-|>", mutation_scale=12,
            color=color, linewidth=0, zorder=2,
        )
        ax.add_patch(arrow)


def _draw_nodes(ax, export_data: dict[str, Any]) -> list[Patch]:
    """Draw nodal pie markers; returns legend handles for the technologies seen."""
    radius_cfg = export_data.get("pie_radius", {"min": 8, "max": 16, "scale_factor": 1.0})
    seen_labels: dict[str, str] = {}

    for node in export_data.get("nodes", []):
        values = node["values"]
        colors = node["colors"]
        labels = node["labels"]
        total = sum(values)

        radius_px = min(
            radius_cfg["min"] + math.sqrt(total) * radius_cfg["scale_factor"],
            radius_cfg["max"],
        )
        size = (radius_px * 3) ** 2

        for wedge, color in zip(_pie_wedge_markers(values), colors):
            ax.scatter(
                [node["lon"]], [node["lat"]],
                marker=wedge, s=size,
                facecolor=color, edgecolor="white", linewidth=0.4, zorder=3,
            )

        for label, color in zip(labels, colors):
            seen_labels.setdefault(label, color)

    return [Patch(facecolor=color, label=label) for label, color in seen_labels.items()]


def _build_title(export_data: dict[str, Any]) -> str:
    """Build a title from the selected period/time, skipping placeholder values."""
    period = export_data.get("selected_period")
    time_value = export_data.get("selected_time_value")
    pq_label = "Active Power" if export_data.get("pq_mode") == "vLineP" else "Reactive Power"

    bits = [str(v) for v in (period, time_value) if v not in (None, "All")]
    bits.append(pq_label)
    return " - ".join(bits)
