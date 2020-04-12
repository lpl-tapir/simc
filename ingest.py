import argparse, configparser, os, sys
import numpy as np
import parseNav

def parseCmd():
    # Build argparser and parse command line args
    parser = argparse.ArgumentParser(description="Run a clutter simulation.")
    parser.add_argument("confPath", help="Path to configuration file (.ini)")
    parser.add_argument("-n", dest="navPath", help="Path to navigation file - overrides any path in config file")
    parser.add_argument("-d", dest="demPath", help="Path to DEM file - overrides any path in config file")
    args = parser.parse_args()

    # Store in dict, expand any relative paths
    argDict = {}
    argDict["confPath"] = os.path.abspath(args.confPath)

    if(args.navPath is not None):
        argDict["navPath"] = os.path.abspath(args.navPath)
    else:
        argDict["navPath"] = None

    if(args.demPath is not None):
        argDict["demPath"] = os.path.abspath(args.demPath)
    else:
        argDict["demPath"] = None

    return argDict

def readConfig(argDict):
    """
    Reads in config file and command line args into dict. Checks legality of various parameters in it.

    Returns:
        Dict: Config parameters.
    """
    # Check that config file path is valid
    if(not os.path.exists(argDict["confPath"])):
        print("Invalid path to config file - file does not exist.")
        sys.exit(1)

    config = configparser.ConfigParser()
    try:
        config.read(argDict["confPath"])
    except Exception as err:
        print("Unable to parse config file.")
        print(err)
        sys.exit(1)

    confDict = {section: dict(config.items(section)) for section in config.sections()} # Dict of config file.

    # Substitute in command line args if necessary
    if argDict["navPath"] is not None:
        confDict["paths"]["navpath"] = argDict["navPath"] # Command line arg overrides config file

    if argDict["demPath"] is not None:
        confDict["paths"]["dempath"] = argDict["demPath"]

    # Check that nav and dem paths are valid
    if(not os.path.exists(confDict["paths"]["navpath"])):
        print("Invalid path to navigation file - file does not exist.")
        sys.exit(1)

    if(not os.path.exists(confDict["paths"]["dempath"])):
        print("Invalid path to DEM file - file does not exist.")
        sys.exit(1)

    # Make output prefix
    if(confDict["paths"]["outpath"][-1] != '/'):
        confDict["paths"]["outpath"] += '/'

    navfile = confDict["paths"]["navpath"].split("/")[-1]
    navname = navfile.split(".")[0]
    confDict["paths"]["outpath"] = confDict["paths"]["outpath"] + navname + "_"

    # Set log file path
    confDict["paths"]["logpath"] = confDict["paths"]["outpath"] + "simLog.txt"

    # Assign correct data types for non-string config items
    confDict["simParams"]["speedlight"] = float(confDict["simParams"]["speedlight"])
    confDict["simParams"]["dt"] = float(confDict["simParams"]["dt"])
    confDict["simParams"]["tracesamples"] = int(confDict["simParams"]["tracesamples"])

    confDict["facetParams"]["atdist"] = float(confDict["facetParams"]["atdist"])
    confDict["facetParams"]["ctdist"] = float(confDict["facetParams"]["ctdist"])
    confDict["facetParams"]["atstep"] = float(confDict["facetParams"]["atstep"])
    confDict["facetParams"]["ctstep"] = float(confDict["facetParams"]["ctstep"])

    trueVal = ["true", "True", "t", "T"]
    falseVal = ["false", "False", "f", "F"]

    for key in confDict["outputs"].keys():
        if(confDict["outputs"][key] in trueVal):
            confDict["outputs"][key] = True
        elif(confDict["outputs"][key] in falseVal):
            confDict["outputs"][key] = False
        else:
            print("Invalid value for outputs:" + key)
            print('Must be "True" or "False"')
            sys.exit(1)

    # Check that facet extent and dimensions are legal
    if(confDict["facetParams"]["atdist"] < confDict["facetParams"]["atstep"]):
        print("Invalid config file param.")
        print("atdist must be greater than atstep")
        sys.exit(1)

    if(confDict["facetParams"]["ctdist"] < confDict["facetParams"]["ctstep"]):
        print("Invalid config file param.")
        print("ctdist must be greater than ctstep")
        sys.exit(1)


    if(confDict["facetParams"]["atdist"] % confDict["facetParams"]["atstep"]):
        print("Invalid config file param")
        print("atdist must be integer multiple of atstep")
        sys.exit(1)

    if(confDict["facetParams"]["ctdist"] % confDict["facetParams"]["ctstep"]):
        print("Invalid config file param")
        print("ctdist must be integer multiple of ctstep")
        sys.exit(1)

    # Determine internal xyz and spherical coordinate systems (IAU 2000)
    xyzD = {"mars": "+proj=geocent +a=3396190 +b=3376200 +no_defs",
            "moon": "+proj=geocent +a=1737400 +b=1737400 +no_defs",
            "earth": "+proj=geocent +a=6378140 +b=6356750 +no_defs"}
    
    lleD = {"mars": "+proj=longlat +a=3396190 +b=3376200 +no_defs",
            "moon": "+proj=longlat +a=1737400 +b=1737400 +no_defs",
            "earth": "+proj=longlat +a=6378140 +b=6356750 +no_defs"}

    body = confDict["simParams"]["body"]

    if(body in xyzD.keys()):
        confDict["navigation"]["xyzsys"] = xyzD[body]
        confDict["navigation"]["llesys"] = lleD[body]
    else:
        print("Invalid body \"" + body + "\" in conf file, valid options are: " + str(list(xyzD.keys())))
        sys.exit(1)
    
    return confDict

def readNav(navPath, navSys, xyzSys, navFunc):
    # Call the user specified navigation file parser
    nav = eval("parseNav." + navFunc)(navPath, navSys, xyzSys)
    return nav