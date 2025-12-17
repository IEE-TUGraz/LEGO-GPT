# Installation & Setup

## Prerequisites

* **Anaconda** or **Miniconda** installed on your system.
* **Git** (optional, for cloning the repository).

## 1. Environment Setup

LEGO-GPT relies on specific Python libraries (Dash, Pandas, Plotly, etc.). We recommend creating a dedicated Conda
environment.

1. Navigate to the project root directory:
   ```bash
   cd path/to/LEGO-GPT
   ```

2. Create the environment using the provided `environment.yml` file:
   ```bash
   conda env create -f environment.yml
   ```

3. Activate the environment:
   ```bash
   conda activate LEGO_GPT_env
   ```

## 2. Configuration

Before running the tool, ensure your configuration is correct.

1. Copy the template configuration:
   ```bash
   cp config_template.yml config.yml
   ```

2. Edit `config.yml` to point to your data source:
   ```yaml
   input_type: sqlite  # or 'excel'
   input_dir: "data/model.sqlite"
   ```