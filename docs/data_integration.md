# Data Integration

LEGO-GPT is designed to work with standard LEGO model outputs.

## Supported Formats

1. **SQLite (`.sqlite`)**: Recommended for large datasets.
2. **Excel (`.xlsx`)**: Suitable for smaller models or prototypes.

## Required Data Structure

The application expects specific tables to be present in the input. If you are extending the data loader, ensure your
data maps to these attributes in the `LEGOData` class:

### Sets (Indices)

* `i`: Nodes (buses). Must include `lat` and `lon` columns if `coords` table is missing.
* `k`: Time steps.
* `rp`: Representative periods (optional).
* `g`: Generators.
* `la`: Lines (arcs).

### Variables (Time Series)

* `vGenP`: Generator active power dispatch. Columns: `[rp, k, g, values]`.
* `vLineP`: Active power flow. Columns: `[rp, k, i, j, values]`.
* `pDemandP` (Optional): Nodal demand.
* `vStIntraRes` (Optional): Storage state of charge.

### Parameters

* `pPmax`: Line thermal limits (used for map coloring).
* `gi`: Generator-to-Node mapping. Columns: `[g, i]`.

## Adding a New Data Source

To support a new format (e.g., CSV or Parquet):

1. Open `data_loader.py`.
2. Create a class inheriting from `DataLoaderStrategy`.
3. Implement the `load()` method to return a populated `LEGOData` object.
4. Update the `get_data()` function to select your new loader.