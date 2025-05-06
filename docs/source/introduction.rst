Introduction
============

Welcome to the **LEGO GPT** documentation!

LEGO GPT is a flexible and extensible Python module for:

- Loading and processing data  
- Defining custom plots  
- Managing UI interactions  
- Creating custom markers for graph visualization  

Data Integration and Format
---------------------------

You can integrate any data source into the tool, as long as it adheres to a consistent internal format.

- If a required data table does **not** exist, you can add it in the ``get_data()`` function in ``data_loader.py``.
- Be sure to document the structure of the new table in ``data_description.rst``.
- Indexing sets must be **uniform across all tables**.  
  For example, the time index should always be named ``"k"``.

Custom Plotting
---------------

To define new plots, modify or extend the ``plot_definitions.py`` file.

.. note::

   Whenever changes are made to data structures or plotting logic, remember to update this documentation accordingly.

Building the Documentation
--------------------------

The documentation is generated using **Sphinx**. Source files are located in the ``docs/source/`` directory.

To build the documentation from the terminal (e.g., Anaconda Prompt), follow these steps:

.. code-block:: bash

   # Navigate to the project root directory
   cd path/to/LEGO-GPT

   # Activate your conda environment
   conda activate LEGO_GPT_env

   # Build the HTML documentation
   sphinx-build -b html docs/source docs/build

The generated HTML files will be located in the ``docs/build/`` directory.

You can view the documentation by opening the following file in a web browser:

.. code-block:: bash

   docs/build/index.html
