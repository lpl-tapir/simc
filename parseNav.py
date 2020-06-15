import sys
import pandas as pd
import rasterio as rio
import numpy as np
import pyproj, h5py
import matplotlib.pyplot as plt

# These functions must return a pandas dataframe with the
# following cols -
# ["x", "y", "z", "datum"]
# Where XYZ are planetocentric radar platform location
# and datum should be all zeros if no time shift is required, otherwise the
# time shift in seconds

areoidPath = "/home/mchristo/proj/simc/test/dem/mega_128ppd.tif"


def GetNav_akHDF(navfile, navsys, xyzsys):
    h5 = h5py.File(navfile, 'r')
    if("nav0" in h5["ext"].keys()):
        nav = h5["ext"]["nav0"][:]
        df = pd.DataFrame(nav)

    elif("loc0" in h5["raw"].keys()):
        nav = h5["raw"]["loc0"][:]
        df = pd.DataFrame(nav)
        # Interpolate non-unique values
        hsh = nav["lat"] + nav["lon"]*1e4
        idx = np.arange(0, len(hsh), 1)
        uniq, uidx = np.unique(hsh, return_index=True)
        uidx = np.sort(uidx)
        uidx[-1] = len(hsh)-1 # Handle end of array
        df["lat"] = np.interp(idx, uidx, df["lat"][uidx])
        df["lon"] = np.interp(idx, uidx, df["lon"][uidx])
        df["altM"] = np.interp(idx, uidx, df["altM"][uidx])
  
    else:
        print("No valid navigation data found in file %s" % navfile)
        sys.exit()

    df["x"], df["y"], df["z"] = pyproj.transform(
        navsys,
        xyzsys,
        df["lon"].to_numpy(),
        df["lat"].to_numpy(),
        df["altM"].to_numpy(),
    )

    df["datum"] = 0*df["x"]

    return df[["x", "y", "z", "datum"]]

def GetNav_FPBgeom(navfile, navsys, xyzsys):
    c = 299792458
    geomCols = [
        "trace",
        "time",
        "lat",
        "lon",
        "marsRad",
        "elev",
        "radiVel",
        "tangVel",
        "SZA",
        "phaseD",
    ]
    df = pd.read_csv(navfile, names=geomCols)

    # Planetocentric lat/lon/radius to X/Y/Z - no need for navsys in this one
    df["x"] = (
        (df["elev"] * 1000)
        * np.cos(np.radians(df["lat"]))
        * np.cos(np.radians(df["lon"]))
    )
    df["y"] = (
        (df["elev"] * 1000)
        * np.cos(np.radians(df["lat"]))
        * np.sin(np.radians(df["lon"]))
    )
    df["z"] = (df["elev"] * 1000) * np.sin(np.radians(df["lat"]))

    # Find datum time with areoid
    try:
        aer = rio.open(areoidPath, "r")
    except:
        print("Unable to open areoid file, is it at : " + areoidPath + " ?")
        sys.exit(1)

    aerX, aerY, aerZ = pyproj.transform(
        xyzsys, aer.crs, df["x"].to_numpy(), df["y"].to_numpy(), df["z"].to_numpy()
    )

    iy, ix = aer.index(aerX, aerY)
    ix = np.array(ix)
    iy = np.array(iy)

    # Temp fix mola meters/pix issue
    ix[ix > aer.width - 1] = aer.width - 1
    ix[ix < 0] = 0

    zval = aer.read(1)[iy, ix]

    df["datum"] = ((1000.0 * df["elev"] - 3396000.0 - zval) * 2.0 / c) - (
        1800.0 * 37.5e-9
    )

    return df[["x", "y", "z", "datum"]]

def GetNav_QDAetm(navfile, navsys, xyzsys):
    c = 299792458
    etmCols = [
        "trace",
        "epoch",
        "alt",
        "sza",
        "lat",
        "lon",
        "molaNadir",
        "vrad",
        "vtan",
        "dist",
        "tshift",
        "radius",
        "utc0",
        "utc1",
    ]

    df = pd.read_csv(navfile, names=etmCols, sep="\s+")

    df["x"], df["y"], df["z"] = pyproj.transform(
        navsys,
        xyzsys,
        df["lon"].to_numpy(),
        df["lat"].to_numpy(),
        (1000 * df["alt"]).to_numpy(),
    )
    #df["datum"] = df["tshift"] * 1e-6

    df["datum"] = (2*df["alt"]/c)-(1800*37.5e-9)

    #plt.plot(np.gradient(df["tshift"]))
    #plt.plot((df["tshift"]/37.5e-9),'.')
    #plt.show()
    #sys.exit()

    rad = np.sqrt(df["x"]**2 + df["y"]**2 + df["z"]**2)

    #plt.plot(rad)
    #plt.show()
    #sys.exit()

    return df[["x", "y", "z", "datum"]]

def GetNav_LRS(navfile, navsys, xyzsys):
    c = 299792458

    df = pd.read_csv(navfile, sep=",")

    df["x"], df["y"], df["z"] = pyproj.transform(
        navsys,
        xyzsys,
        df["SUB_SPACECRAFT_LONGITUDE"].to_numpy(),
        df["SUB_SPACECRAFT_LATITUDE"].to_numpy(),
        np.ones(len(df))*190000,
    )

    plt.plot(df["SUB_SPACECRAFT_LONGITUDE"],'.')
    plt.show()
    #df["datum"] = df["tshift"] * 1e-6

    #plt.plot(df["SPACECRAFT_ALTITUDE"])
    #plt.plot(df["DISTANCE_TO_RANGE0"])
    #plt.show()

    df["datum"] = (2*1000*df["DISTANCE_TO_RANGE0"]/c) - (500*160e-9)

    #rad = np.sqrt(df["x"]**2 + df["y"]**2 + df["z"]**2)

    #plt.plot(rad)
    #plt.show()

    return df[["x", "y", "z", "datum"]]

def GetNav_simpleTest(navfile, navsys, xyzsys):
    navCols = ["x", "y", "z"]
    df = pd.read_csv(navfile, names=navCols)

    # No redatum
    df["datum"] = np.zeros(gdf.shape[0])

    return df[["x", "y", "z", "datum"]]
