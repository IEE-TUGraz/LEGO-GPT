# LEGO-GPT Documentation

Welcome to the official documentation for **LEGO-GPT**!

LEGO-GPT is an interactive Graph Plotting Tool. This version is dedicated to analyzing the optimization results of
the V2G-QUESTS-PSOM model. It allows users to visualize network power flows, generation dispatch, EV charging and
nodal data through a reactive web interface.

## Table of Contents

* [Installation & Setup](installation.md)
* [User Guide](usage.md)
* [System Architecture](architecture.md)
* [Data Integration](data_integration.md)
* [Customization](customization.md)

## Key Features

* **Interactive Network Map:** Visualizes lines, nodes, and power flows on a Leaflet map.
* **Dynamic Plotting:** Generates time-series and aggregated plots for any variable in the dataset.
* **Modular Design:** Easily extensible for new plots, data sources, or UI components.
* **V2G-QUESTS-PSOM Input:** Reads the SQLite result database of V2G-QUESTS-PSOM, including EV charging and discharging.