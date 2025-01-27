# simc - Multi-planet surface clutter simulation
[![DOI](https://zenodo.org/badge/748854775.svg)](https://zenodo.org/doi/10.5281/zenodo.10595006)

## Installation
simc can be installed directly from this GitHub repo with pip. To install the most recent version:
```
pip install git+https://github.com/lpl-tapir/simc.git
```
This will create an executable named `simc` that you can use at the command line in order to run the surface clutter simulator. Running `simc --help` will print the following help text:

```
usage: simc [-h] [-n NAVPATH] [-d DEMPATH] [-o OUTPATH] [-p] confPath

Run a clutter simulation.

positional arguments:
  confPath    Path to configuration file (.ini)

optional arguments:
  -h, --help  show this help message and exit
  -n NAVPATH  Path to navigation file - overrides any path in config file
  -d DEMPATH  Path to DEM file - overrides any path in config file
  -o OUTPATH  Path to output products - overrides any path in config file
  -p          Display progress bar
```

## Developer Installation
If you wish to install simc with the intent to modify the source code we recommend the following installation procedure:
1. Use git to clone this repository  
   `git clone https://github.com/lpl-tapir/simc.git`  
2. Navigate into the cloned repository and use pip to install it in editable mode  
   `pip install -e`
  
This installation procedure will create the same `simc` executable as the normal installation, however the `simc` executable is connected to your version of the simc git repo.
