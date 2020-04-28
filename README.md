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

<ol>
<li>
Python version 3.6 or newer is required and should be the one found, based on your $PATH value, starting the Python interpreter with the command:

```` bash
python
````
</li>

<li>
The gridappsd-python module must be installed in python.  To check if this module is already installed:

```` bash
python
>>> import gridappsd
````

If the import returns an error message, see <https://github.com/GRIDAPPSD/gridappsd-python> for installation instructions.
</li>

<li>
The tkinter module must be installed in python, which is typically the case with most full Linux distributions.  To check if this module is already installed:

```` bash
python
>>> import tkinter
````

If the import returns an error message, the following command should install the tkinter module into python along with the required Tk GUI libraries:

```` bash
sudo apt-get install python-tk
````
</li>

<li>
The matplotlib module must be installed in python.  Use the following command to install the newest available version:

```` bash
sudo python -m pip install -U matplotlib
````
</li>

<li>
Verify the matplotlib module is version 3.1.0 or newer:

```` bash
python
>>> import matplotlib
>>> matplotlib.__version__
````
</li>

<li>
Verify that the host or Docker container you are using is setup to support X Windows applications as needed for displaying matplotlib plots:

```` bash
python
>>> import matplotlib.pyplot as plt
>>> plt.plot([1,2,3,4])
>>> plt.show()
````

If errors are output without a plot window being shown, there are various solutions to allow X Windows applications to display.

If you are running in a Docker container with the docker compose command, the following docker-compose.yml directives are needed before running docker compose so the container shares the X11 port with the host that is running your Linux windows manager:

```` bash
volumes:
    - /tmp/.X11-unix:/tmp/.X11-unix
environment:
    - DISPLAY=${DISPLAY}
````

If you are running in a Docker container with the docker run command, the following blog provides guidance in the section titled "Running GUI apps with Docker": <http://fabiorehm.com/blog/2014/09/11/running-gui-apps-with-docker/>.

If you are running from a host that's different than the one running your Linux windows manager via ssh, you can use ssh X11 port forwarding with the "-X" command line option when starting your ssh connection.
</li>
</ol>



## Installing state plotter

Clone the repository <https://github.com/GRIDAPPSD/gridappsd-state-ploter> under the same parent directory as the gridappsd-python module, assumed to be ~/git:

```` bash
~/git
├── gridappsd-python
└── gridappsd-state-plotter
````


## Running state plotter

1. Invoke ./state-plotter.py from the state-plotter subdirectory with no arguments or -help to get a usage message that describes various command line options. These are also shown in the next section

2. Edit the run-plot.sh script in the state-plotter subdirectory, uncomment the appropriate SIMREQ variable for the model being run based on the comment at the end of each SIMREQ line denoting the corresponding model, and save changes. Different command line options are shown in commented out invocations of state plotter below.

3. Configure and start the simulation from the GRIDAPPSD platform web browser visualization, click on the "Simulation ID" value in the upper left corner of the simulation diagram to copy the value to the clipboard.

4. With the state estimator being invoked either by the platform or separately from the command line, run the script "./run-plot.sh" from the command line with the Simulation ID value pasted from the clipboard as the command line argument to the script.

5. The state plotter will process running simulation measurements and state estimator messages and update plots with new data along with sending diagnostic log output to the terminal.

## Command line options for state plotter

- -mag[nitude]: voltage magnitude plots should be created (default)
- -ang[le]: voltage angle plots should be created
- -over[lay]: overlays simulation measurement and state estimate values in the same bottom plot instead of the default to plot the difference between simulation measurement and state estimate values
- -match: only plot state estimates when there is a matching bus,phase pair in simulation measurements
- -comp[aritivebasis]: plot comparitive basis values. I.e., per-unit voltage magnitudes and relative to nominal voltage angles (default)
- -phys[icalunits]: plot physical units for voltage magnitude and absolute values for voltage angles
- -nocomp[aritivebasis]: equivalent to -phys[icalunits], comparitive basis values are not plotted
- -stat[s][istics]: plots minimum, maximum, mean and standard deviation values over all bus,phase pairs for each timestamp (default if none from -bus, -conf, -all, nor -# are specified). Can be used in combination with -phase to report statistics for specific phases.  The standard deviation is shown as a shaded range below and above the mean value.  Minimum and maximum value ranges are shaded below and above the standard deviation ranges.
- -bus: plots the specified bus name and phase comma-separated pair (no spaces) given as the argument that follows. The bus name alone may be given without a comma and phase and all phases that are present will be plotted, e.g. "-bus 150" will plot phases A, B, and C if present.  Plotting combinations of bus,phase pairs is done by repeating the -bus option, e.g., "-bus 150,A -bus 160,A". Using -bus on the command line results in state-plotter-config.csv bus,phase pairs being disregarded.
- -conf[ig]: read bus name and phase pairs from state-plotter-config.csv file in parent directory. Each line contains a bus name and phase comma-separated pair. The bus name alone may be given without a comma and phase and all phases that are present will be plotted. Lines starting with the character "#" are treated as comments and ignored as are blank lines.
- -all: plots all bus,phase pairs disregarding any pairs specified by state-plotter-config.csv or the -bus option
- -#, where # is an integer value: plots the first # bus,phase pairs that occur in state estimator output, e.g., "-25" plots the first 25 bus,phase pairs. Like -all, any pairs specified by state-plotter-config.csv or the -bus option are disregarded when using this option. If there are fewer pairs than #, all pairs are plotted.
- -phase: plots only the specified phase (A, B, or C) given as the argument that follows. Combinations of phases in the same plot are done by repeating the -phase option, e.g., "-phase A -phase B" to exclude phase C. If there are bus,phase pairs specified in state-plotter-config.csv or with the -bus option, they will be excluded if -phase is used and the phase of the pair differs. E.g., "-bus 160,A -phase C" will not plot the 160,A pair, nor any data in this case, since the -phase option specifies only phase C.
- -legend: Indicates that a legend should be shown for the plot when bus,phase pairs are specified either with the -bus option or in state-plotter-config.csv
- -title: appends argument that follows to the standard title to allow plot windows to be distinguished from each other. The argument can be quoted to allow spaces.
- -help: show usage message

