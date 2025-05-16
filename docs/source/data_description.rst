Data Format Overview
====================

This section outlines the internal data format used by the plotting tool. Given the evolving nature of data sources and structures (like the many versions of LEGO), this overview serves as a reference for how data should be structured after loading and processing.

All data sources integrated into the plotting tool should conform to this format. Specifically, this is the format expected as the output of the get_data() function. The resulting data is assigned as an attribute to the class instance and subsequently used to generate the plots.

---

**1. gi – Generation Info Table**

.. csv-table::
   :header: "g", "tec", "i"
   :widths: 20, 15, 10

   "AL00WIND", "Wind", "AL00"
   "AL00PV", "Solar", "AL00"
   "AT00WIND", "Wind", "AT00"
   "AT00PV", "Solar", "AT00"
   "AT00OTHERRES", "OtherRES", "AT00"

---

**2. i – Node Info**

Contains the list of nodes and their corresponding geographic coordinates.
Note: The `i` table is then modified so that the 'values' column is set as index.
This is done to simplify indexing, but it requires the 'values' column to be unique.

.. csv-table::
   :header: "values", "lon", "lat"
   :widths: 10, 10, 10

   "AL00", 20.04, 41.26
   "AT00", 14.84, 47.64
   "BA00", 17.72, 44.27
   "BE00", 4.72, 50.80
   "BG00", 25.10, 42.78

---

**3. k – Time Steps**

.. csv-table::
   :header: "values"
   :widths: 10

   "k0001"
   "k0002"
   "k0003"
   "k0004"
   "k0005"

---

**4. la – Lines Between Nodes**

.. csv-table::
   :header: "i", "j"
   :widths: 10, 10

   "AT00", "CH00"
   "AT00", "CZ00"
   "AT00", "DE00"
   "AT00", "HU00"
   "AT00", "ITN1"

---

**5. rp – Representative Periods**

.. csv-table::
   :header: "values"
   :widths: 10

   "rp01"

---

**6. vGenP – Generator Profiles**

.. csv-table::
   :header: "rp", "k", "g", "values"
   :widths: 10, 10, 20, 10

   "rp01", "k0001", "AL00COALOLD2", 0.0
   "rp01", "k0002", "AL00COALOLD2", 0.0
   "rp01", "k0003", "AL00COALOLD2", 0.0
   "rp01", "k0004", "AL00COALOLD2", 0.0
   "rp01", "k0005", "AL00COALOLD2", 0.0

---

**7. vLineP – Line Flow Values**

.. csv-table::
   :header: "rp", "k", "i", "j", "values", "line", "rel_values", "pPmax"
   :widths: 10, 10, 10, 10, 15, 5, 10, 10

   "rp01", "k0001", "AT00", "CH00", 964.539580, 0, 0.803783, 1200
   "rp01", "k0001", "AT00", "CZ00", -228.815745, 1, 0.254240, 900
   "rp01", "k0001", "AT00", "DE00", 5772.293185, 2, 0.769639, 7500
   "rp01", "k0001", "AT00", "HU00", -800.0, 3, 1.0, 800
   "rp01", "k0001", "AT00", "ITN1", -875.0, 4, 1.0, 875

---

**8. vStIntraRes – Storage SOC Values**

.. csv-table::
   :header: "rp", "k", "i", "storageUnits", "values", "tec"
   :widths: 10, 10, 10, 20, 10, 10

   "rp01", "k0001", "AL00", "AL00HS", 0.500000, "HS"
   "rp01", "k0001", "AT00", "AT00HS", 0.500113, "HS"
   "rp01", "k0001", "AT00", "AT00HPS", 0.496457, "HPS"
   "rp01", "k0001", "AT00", "AT00HPSCL", 0.500000, "HPS"
   "rp01", "k0001", "AT00", "AT00BESS", 0.545226, "BESS"

