# gridappsd-state-plotter

## Purpose

The state plotter application plots state estimator service and simulation output including plots of the difference between voltage magnitudes and angles.  The user can specify the nodes and phases to plot on the command line or through a configuration file.


## State plotter application layout

The following is the structure of the state plotter:

```` bash
.
├── README.md
├── LICENSE
├── state-plotter-config.csv
└── state-plotter
    ├── icons
    └── state-plotter.py
````


## Prerequisites

1. Python version 3.6 or newer is required.

2. The gridappsd-python module must be installed in python.  See <https://github.com/GRIDAPPSD/gridappsd-python> for installation instructions.

3. The matplotlib module must be installed in python.  Use the following command to install the newest available version:

```` bash
sudo python3 -m pip install -U matplotlib
````

4. Verify the matplotlib is version 3.1.0 or newer and that the TkAgg backend is available:

```` bash
python3
>>> import matplotlib
>>> matplotlib.__version__
>>> matplotlib.rcsetup.interactive_bk
````


## Installing state plotter

1. Clone the repository <https://github.com/GRIDAPPSD/gridappsd-state-ploter> under the same parent directory as the gridappsd-python module, assumed to be ~/git:

```` bash
~/git
├── gridappsd-python
└── gridappsd-state-plotter
````


## Running state plotter

1. Invoke ./state-plotter.py from the state-plotter subdirectory with no arguments to get a usage message that describes various command line options.

2. Edit the run-plot.sh script in the state-plotter subdirectory, uncomment the appropriate SIMREQ variable for the model being run based on the comment at the end of each SIMREQ line denoting the corresponding model, and save changes. Different command line options are shown in commented out invocations of state plotter.

3. Configure and start the simulation from the GRIDAPPSD platform web browser visualization, click on the "Simulation ID" value in the upper left corner of the simulation diagram to copy the value to the clipboard.

3. Assuming the state estimator was invoked either by the platform or separately from the command line, invoke the script "./run-plot.sh" from the command line with the Simulation ID value pasted from the clipboard as the command line argument to the script.

4. The state plotter will process running simulation measurements and state estimator messages and plot output along with diagnostic log output to the terminal.

