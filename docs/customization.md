# Customization

## Adding New Plots

You can add new visualization types without modifying the core UI logic.

1. Open `plot_definitions.py`.
2. Add an entry to the `PLOT_REGISTRY` dictionary:

```python
("my_x_axis", "my_y_axis"): {
    "data_source": "vGenP",  # Attribute in LEGOData
    "plot_type": PlotType.LINE,  # Visualization type
    "x_col": "k",  # Column for X
    "y_col": "values",  # Column for Y
    "title_global": "My New Plot",
}
```

3. Update `config.yml` to include your new axis options in the dropdown menus.

## Styling the Map

Map colors and clustering behavior are defined in `config.yml` under `map_options`:

```yaml
map_options:
  line_weight: 2
  technology_colors:
    Wind: "#2ecc71"
    Solar: "#f1c40f"
    Gas: "#e74c3c"
```

## Styling the Graph

Global graph settings (fonts, margins, colors) are controlled via `graph_options` in `config.yml`. These are passed
directly to the Plotly layout engine.