.. _safety:

############
hveto safety
############

Hveto safety analysis uses the hveto analysis algorithms to analyze hardware injections looking for unsafe channels. An unsafe channel is one that witnesses an event in the strain channel as opposed to a safe channel where strain may witness an event in that channel. In other words we do not want to look for glitches in a channel man may see a gravitational wave event.

The safety analysis differs from a normal hveto analysis and that it is not "hierarchical" in the sense that vetoes from one channel remove that primary channel event from consideration in the other channels.

Processing
==========

The safety process is implemented as a pipeline with multiple steps. It is designed to eventually be able to be run completely automatically triggered by an LValert. We are not quite there yet but close. The steps in running are:

* **detchar-hwinj-query** Query GraceDB for the time and parameters of each injection. This creates a CSV file.
* **SafetyTrigPrep** Uses the parameters of each injection and the PSD used calculate the expected SNR and outputs and HDF5 file to be used as a primary input to the safety calculations.
* **omicron_trig** Takes a time interval and the directory then converts the `ligolw` XML files to CSV files.
* **csv2hdf.py** Converts a directory of CSV files to an HDF5 file
* **get_segs.py** Creates an XML and a text file defining the time to process.
* **hveto_safety** Run the safety analysis

