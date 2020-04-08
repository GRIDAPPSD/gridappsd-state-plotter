# gridappsd-state-plotter

## Purpose

The state plotter application plots state estimator service and simulation output including plots of the difference between simulation and state estimate voltage magnitudes and angles.  The user can specify the nodes and phases to plot along with other settings on the command line or through a configuration file.


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

1. Python version 3.6 or newer is required and should be the one found, based on your $PATH value, starting the Python interpreter with the command:

```` bash
python
````

2. The gridappsd-python module must be installed in python.  To check if this module is already installed:

```` bash
python
>>> import gridappsd
````

&nbsp;&nbsp;&nbsp;&nbsp;If the import returns an error message, see <https://github.com/GRIDAPPSD/gridappsd-python> for installation instructions.

3. The tkinter module must be installed in python, which is typically the case with most full Linux distributions.  To check if this module is already installed:

```` bash
python
>>> import tkinter
````

If the import returns an error message, the following command should install the tkinter module into python along with the required Tk GUI libraries:

```` bash
sudo apt-get install python-tk
````

3. The matplotlib module must be installed in python.  Use the following command to install the newest available version:

```` bash
sudo python -m pip install -U matplotlib
````

4. Verify the matplotlib module is version 3.1.0 or newer:

```` bash
python
>>> import matplotlib
>>> matplotlib.__version__
````

5. Verify that the host or Docker container you are using is setup to support X Windows applications as needed for displaying matplotlib plots:

```` bash
python
>>> import matplotlib.pyplot as plt
>>> plt.plot([1,2,3,4])
>>> plt.show()
````

If errors are output without a plot window, there are various solutions to
allow X Windows applications to display. If you are running in a Docker container with the docker compose command, the following docker-compose.yml directives are needed before running docker compose so the container shares the X11 port with the host:

```` bash
volumes:
    - /tmp/.X11-unix:/tmp/.X11-unix
environment:
    - DISPLAY=${DISPLAY}
````

If you are running in a Docker container with the docker run command, the following blog provides guidance in the section titled "Running UI apps with Docker": <http://fabiorehm.com/blog/2014/09/11/running-gui-apps-with-docker/>

If you are running from a host that's different than the one running your Linux windows manager via ssh, you can use ssh X11 port forwarding with the "-X" command line option when starting your ssh connection.



## Installing state plotter

1. Clone the repository <https://github.com/GRIDAPPSD/gridappsd-state-ploter> under the same parent directory as the gridappsd-python module, assumed to be ~/git:

```` bash
~/git
├── gridappsd-python
└── gridappsd-state-plotter
````


## Running state plotter

1. Invoke ./state-plotter.py from the state-plotter subdirectory with no arguments to get a usage message that describes various command line options.

2. Edit the run-plot.sh script in the state-plotter subdirectory, uncomment the appropriate SIMREQ variable for the model being run based on the comment at the end of each SIMREQ line denoting the corresponding model, and save changes. Different command line options are shown in commented out invocations of state plotter below.

3. Configure and start the simulation from the GRIDAPPSD platform web browser visualization, click on the "Simulation ID" value in the upper left corner of the simulation diagram to copy the value to the clipboard.

3. With the state estimator being invoked either by the platform or separately from the command line, run the script "./run-plot.sh" from the command line with the Simulation ID value pasted from the clipboard as the command line argument to the script.

4. The state plotter will process running simulation measurements and state estimator messages and update plots with new data along with sending diagnostic log output to the terminal.

