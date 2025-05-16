Adding Data - Contribution Guide
================================

This tutorial explains how to contribute new data to the project using code and visuals.
Each step is accompanied by a screenshot for clarity. 

Step 1: Open the `config.yml` File
----------------------------------

Navigate to the `config.yml` file, where plot and data selection are configured.

If your new plot requires additional data, add the name of the new table (as defined in the Pyomo model) to the
`tables` section. Then, specify the x- and y-axis data for the plot in the `dropdown-options` section.
This enables users to select the new data when generating plots.

The example below shows how to add a new table and a corresponding y-axis option:

.. image:: images/adapt_config.png
   :alt: Adapting the config file to add new variables and dropdown options
   :width: 600

Step 2: Modify the New Table in the Data Loader Module
-------------------------------------------------------

In the `get_data()` function of the data loader module, adapt your table if necessary.  
In the example below, the table `vStIntraRes` is enhanced by adding information about  
which node each storage unit is attached to.

.. image:: images/adapt_dataframe.png
   :alt: Adapting a DataFrame (optional)
   :width: 600

Step 3: Define the New Plot
---------------------------

In the `plot_definitions.py` file, define your new plot in the `generate_plot(..)` function using the newly added data.
Start by extending the block that filters the data to be plotted. Then, add your plot to the list of plot definitions.

.. image:: images/adapt_plot_definition.png
   :alt: Adding a new plot definition
   :width: 600

In the `filter_dataframe(..)` function, define how your data is filtered based on the selected x- and y-axis values.
Here you can include any additional logic required for filtering your new table.

.. image:: images/adapt_filtering.png
   :alt: Filtering the new table
   :width: 600

Step 4: Test the Integration
----------------------------

Run a minimal example or use the user interface to verify that the plot is generated correctly with the new data.

.. image:: images/final_plot.png
   :alt: Final test of the new plot
   :width: 600

Next Steps
----------

Once the new table is added, documented, and tested, feel free to open a pull request.

Please ensure the following before submitting:

- The table name follows existing naming conventions.
- All fields are clearly documented.
- No hard-coded paths or values are introduced.
- The new data is compatible with the plot selection logic.
