# User Guide

## Running the Application

To start the LEGO-GPT server, run the main script from your terminal:

```bash
python LEGO_GPT.py [path/to/config.yml]
```

* If no config path is provided, it defaults to `config.yml`.
* The console will display the local server address (usually `http://127.0.0.1:8050`).

## Interface Overview

### 1. Control Panel

Located on the left (or top, depending on screen size), this panel controls what data is displayed.

* **Period:** Selects the representative period (if applicable) or "All".
* **Time Slider:** Navigates through time steps (hours/snapshots).
* **Scope:** Toggles between **Global** (system-wide data) and **Local** (specific node/line data).
* **Axis Selection:** Defines the X and Y axes for the dynamic plot (e.g., X="Time", Y="Dispatch").

### 2. Network Map

The interactive map visualizes the grid topology.

* **Lines:** Colored based on relative loading (Green < 50%, Red > 100%). Arrows indicate flow direction.
* **Nodes:** Display pie charts of generation mix (Solar, Wind, Thermal, etc.).
* **Interactivity:** Click on a **Line** or **Node** to select it. This updates the "Local" scope for plots.

### 3. Dynamic Plot

The graph panel updates automatically based on your selections.

* **Example 1:** Select `X: Time`, `Y: Dispatch`, `Scope: Global` to see the total system generation stack.
* **Example 2:** Click a node on the map, then select `Scope: Local` to see the generation for just that node.