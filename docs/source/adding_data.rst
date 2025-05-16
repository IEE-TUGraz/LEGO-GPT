Adding Data - Contribution Guide
================================

This tutorial explains how to contribute new data to the project using code and visuals.
Each step is accompanied by a screenshot for clarity. You can replace image filenames
and adjust the text as needed for your specific additions.

Step 1: Open the config.yml File
--------------------------------

Navigate to the file where plot and data selection is handled. This is typically located in::

    src/config.yml

If your nre plot needs addiitonal data, add the name of the new table (as in the Pyomo model) to the
tables section of the config file. Then, specify the x- and y-axis data for the plot in the dropdown-options
section. This will allow users to select the new data when generating plots. An example showing the addition of a new table
and a new selection for the y axis is shown below:

.. image:: images/adapt_config.png
   :alt: Adapting the config file to add new variables and dropdown-options
   :width: 600

Step 2: Modify new table in the data loader module
-------------------------------------------------------

In the `get_data()` function, adapt your table if necessary. In this case, the table vStIntraRes is enhanced by adding the information about 
at which node, the storage unit is attached.

.. image:: images/adapt_dataframe.png
   :alt: Adapt dataframe (optional)
   :width: 600

Step 3: Define the New Plot
---------------------------

In the `plot_definitions.py` file, define the new plot in the generate_plot(..) function using the new data. This is where you specify how the data will be visualized. 
First, add to the block that filters the data to be plotted. Then, add the new plot definition to the list of plots.

.. image:: images/adapt_plot_definition.png
   :alt: Adding a new plot definition
   :width: 600

In the filter_dataframe(..) function, you specify how your data is filtered based on the selected x- and y-axis data.
This is where you can add any additional filtering logic needed for your new table.

.. image:: images/adapt_filtering.png
   :alt: Adding a new plot definition
   :width: 600

Step 4: Test the Integration
----------------------------

Run a minimal example to see if the plot is generated correctly. 

.. image:: images/final_plot.png
   :alt: Testing the integration of new data
   :width: 600

Next Steps
----------

Once the table is added, documented, and tested, feel free to open a pull request.
Please make sure:

- The table name follows naming conventions.
- All fields are documented.
- No hard-coded paths or values are included.
