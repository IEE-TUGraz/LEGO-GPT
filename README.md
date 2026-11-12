# LEGO-GPT: Graph Plotting Tool (V2G-QUESTS-PSOM version)

LEGO-GPT is a modular, interactive visualization tool. This version is dedicated to the results of the
[V2G-QUESTS-PSOM](https://github.com/IEE-TUGraz/V2G-QUESTS-PSOM) power system optimization model: it reads the SQLite
result database (`output/result.sqlite`) and provides a web-based interface built with Dash to visualize network maps,
power flows, dispatch schedules, EV charging and other time-series data.

## 1. Project Structure

The tool follows a composition-based architecture where the main orchestrator (`LEGO_GPT.py`) delegates responsibilities
to specialized modules. This separation of concerns makes the tool easier to maintain and extend.

```text
LEGO-GPT/
├── LEGO_GPT.py           # Main application entry point (Orchestrator)
├── config.yml            # Central configuration file
├── data_loader.py        # Data ingestion (V2G-QUESTS-PSOM SQLite) using Strategy pattern
├── data_provider.py      # Interface for accessing processed data
├── layout_builder.py     # UI component construction (Dash Layout)
├── callback_manager.py   # Event handling and reactivity (Dash Callbacks)
├── plot_definitions.py   # Plot generation logic and registry
├── ui_handler.py         # Specific visualization logic (Maps/Plots)
├── MarkerJS.py           # Generates JavaScript for map markers
└── helper_functions.py   # Utility functions
```

### Core Components

* **LEGO_GPT (Orchestrator):** Initializes the app, loads configuration, and wires together the data, UI, and callback
  components.
* **Data Layer:**
    * `data_loader.py`: Reads the V2G-QUESTS-PSOM SQLite result database and standardizes the data into a
      `LEGOData` container.
    * `data_provider.py`: Acts as a clean interface for the UI to request specific data subsets.
* **Visualization Layer:**
    * `layout_builder.py`: Constructs the HTML structure of the app using reusable component methods (e.g.,
      `_build_map_controls`, `_build_graph_panel`).
    * `plot_definitions.py`: Contains the logic for generating Plotly figures. It uses a registry system to map axis
      selections (e.g., X="Time", Y="Dispatch") to specific plot configurations.
* **Interaction Layer:**
    * `callback_manager.py`: Registers all Dash callbacks. It manages the logic for what happens when a user clicks a
      node, changes a slider, or selects a dropdown.

## 2. Workflow

The application lifecycle follows these steps:

1. **Initialization:**
    * The `LEGO_GPT` class is instantiated with a configuration path (default: `config.yml`).
    * `_load_configuration()` reads settings for input directories, map styles, and plot options.

2. **Data Loading:**
    * `_load_data()` invokes the V2G-QUESTS-PSOM loader via `data_loader.py`.
    * Data is loaded into standard Pandas DataFrames (e.g., `vGenP` for generation, `vLineP` for power flow) and stored
      in the `LEGOData` dataclass.

3. **UI Construction:**
    * `_setup_ui()` calls `LayoutBuilder.build()`.
    * The builder creates the header, control panel (dropdowns, sliders), and the main visualization areas (Leaflet map
      and Plotly graph).

4. **Callback Registration:**
    * `_register_callbacks()` initializes the `CallbackManager`.
    * It links UI inputs (like `time-slider` value) to output updates (like `network-map` children).

5. **Execution:**
    * The server starts via `app.run()`. As users interact with the UI, the `CallbackManager` routes events to specific
      handlers to update the visualizations dynamically.

## 3. How to Extend

LEGO-GPT is designed to be extensible. Common extension scenarios include:

### Adding New Plots

You do not need to modify the UI logic to add a standard plot.

1. Open `plot_definitions.py`.
2. Locate the `PLOT_REGISTRY` dictionary.
3. Add a new entry with a tuple key `(x_axis_name, y_axis_name)`.
    * **data_source**: The attribute name in `LEGOData` (e.g., `"vGenP"`).
    * **plot_type**: Choose from `PlotType` (AREA, LINE, BAR, etc.).
    * **x_col / y_col**: Column names to map to the axes.
    * **color_col**: Column to use for grouping/coloring.
4. Ensure your `config.yml` includes the new X or Y options in `dropdown_options_x` or `dropdown_options_y` so they
   appear in the UI.

### Adding New Data Sources

To support a new input format (e.g., CSV or JSON):

1. Open `data_loader.py`.
2. Create a new class that inherits from `DataLoaderStrategy`.
3. Implement the `load(self, input_dir, tables)` method to return a `LEGOData` object.
4. Update `get_data` to instantiate your new loader (and extend the allowed `input_type` values in `config.py`).

### Customizing the UI

The UI is built using composable methods in `layout_builder.py`.

* **To add a control:** Add a `_build_new_control()` method in `LayoutBuilder` and insert it into the
  `_build_control_panel()` list.
* **To change styling:** Modify the `Colors` or `BaseStyles` classes in `layout_builder.py` to affect the global theme.

## 4. Usage

**Command Line:**

```bash
python LEGO_GPT.py [path/to/config.yml]
```

**Python:**

```python
from LEGO_GPT import LEGO_GPT

# Initialize with custom config
app = LEGO_GPT(config_path="my_config.yml")

# Run the server
app.run(debug=True, port=8050)
```