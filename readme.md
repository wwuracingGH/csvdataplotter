# CSV Plotter #
This is a tool that plots csv files from our datalogger.

## Installation ##
### Python ###
Download [this](https://www.python.org/downloads/).

Open a command prompt. On windows, go to the search bar and type 'cmd', and command prompt should pop up first.

Type `python --version` to check that it's installed and added to your PATH. If it isn't, try rebooting your computer.

Type `pip install matplotlib`. This installs the only library used by csv plotter. If pip is not found, you can also try `python -m pip install matplotlib`.

### CSV Plotter ###

You can either clone the repository or just download the file `plot.py`.

## Running ##

You must open a command prompt to the directory you downloaded the file in. On Windows 11 this can be accomplished by right clicking anywhere in the folder you installed plot.py in while viewing it in file explorer. The main command looks like this:

```cmd
python plot.py [dir] a [channel1] [channel2] ... [channeln]
```

\[dir\] could be either the path to a log file or the path to a directory containing log files

channel1 through channeln are names of the channels as they exist in the logfile. To list all channels in a file, type

```cmd
python plot.py [file] c
```

Where \[file\] is the path of a valid log file.

For example, if I wanted to plot the x and y accelerations of all logfiles in the directory H:/logs/, I could type

```cmd
python plot.py H:/logs/ a AccelX AccelY
```

