# Data Integration

This version of LEGO-GPT visualizes the results of the V2G-QUESTS-PSOM model.

## Supported Format

The SQLite result database written by V2G-QUESTS-PSOM (`output/result.sqlite`). Set `input_dir` in `config.yml` to the
folder containing the database or to the `.sqlite` file itself.

## Table Mapping

The data loader (`V2GDataLoader` in `data_loader.py`) reads the V2G-QUESTS-PSOM tables and maps them to the attributes
of the `LEGOData` class used by the rest of the application:

### Sets (Indices)

* `i`: Nodes, from `Buses`. Coordinates come from the `lat` and `lon` tables.
* `k`: Time steps, from `Time`.
* `rp`: A single dummy period (`rp01`); V2G-QUESTS-PSOM has no representative periods.
* `la`: Lines, from `Branches`.
* `g` / `gi`: Generators and their nodes, from `PV_Buses`, `Wind_Buses` and `Hydro_Buses`.

### Variables (Time Series)

* `vGenP`: Generation, from `vProd_PV`, `vProd_Wind` and `vProd_Hydro`.
* `vLineP` / `vLineQ`: Active and reactive power flow.
* `pDemandP`: Nodal demand, from `pDemand`.
* `vSOCP`: Voltage magnitude, from `vCii` (square root of the squared voltage).
* `vStIntraRes`: Battery state of charge, from `vSOC_Batt`.
* `vChEV` / `vDchEV` / `vSocEV`: EV charging, discharging and state of charge, assigned to nodes via `pAvailable`.

### Parameters

* `pPmax`: Line thermal limits, from `pPmax_line` (used for map coloring).
* `voltage_bounds`: Nodal voltage limits, from `Vmax` and `Vmin`.

## Adding a New Data Source

To support another format:

1. Open `data_loader.py`.
2. Create a class inheriting from `DataLoaderStrategy`.
3. Implement the `load()` method to return a populated `LEGOData` object.
4. Update the `get_data()` function to select your new loader.
