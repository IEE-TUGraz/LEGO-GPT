# System Architecture

LEGO-GPT follows a composition-based design pattern. The application is orchestrated by a central class that delegates
tasks to specialized modules.

## High-Level Structure

```text
LEGO_GPT (Main Class)
├── Data Layer
│   ├── DataProvider (Access Interface)
│   └── DataLoader (Ingestion Strategy)
├── UI Layer
│   ├── LayoutBuilder (HTML Structure)
│   └── UIHandler (Visualization Logic)
└── Logic Layer
    ├── CallbackManager (Interactivity)
    └── PlotDefinitions (Graph Registry)
```

## Core Components

### Orchestrator (`LEGO_GPT.py`)

The entry point. It loads the configuration, initializes the data provider, builds the layout, and starts the Flask/Dash
server.

### Data Loader (`data_loader.py`)

Implements the Strategy pattern to load data from different sources (SQLite, Excel). It normalizes raw data into a
standard `LEGOData` dataclass.

### Layout Builder (`layout_builder.py`)

Constructs the Dash component tree. It separates the visual styling (CSS, HTML structure) from the application logic.

### Callback Manager (`callback_manager.py`)

Registers all Dash callbacks. It handles the "reactivity" of the app—ensuring that when a user moves the time slider,
the map and plots update instantly.

### Plot Definitions (`plot_definitions.py`)

A registry of available plots. It maps `(x_axis, y_axis)` tuples to specific plotting functions using Plotly Express.