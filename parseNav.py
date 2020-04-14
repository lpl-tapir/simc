import sys, h5py
import pandas as pd
import rasterio as rio
import numpy as np
import pyproj
import matplotlib.pyplot as plt

# These functions must return a pandas dataframe with the
# following cols -
# ["x", "y", "z", "datum"]
# Where XYZ are planetocentric radar platform location
# and datum should be all zeros if no time shift is required, otherwise the
# time shift in seconds


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
    aer = rio.open("../test/dem/mega_128ppd.tif", "r")
    aerX, aerY, aerZ = pyproj.transform(
        xyzsys, aer.crs, df["x"].to_numpy(), df["y"].to_numpy(), df["z"].to_numpy()
    )

    iy, ix = aer.index(aerX, aerY)
    ix = np.array(ix)
    iy = np.array(iy)

    # Temp fix mola meters/pix issue
    ix[ix > aer.width - 1] = aer.width - 1

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
    df["datum"] = df["tshift"] * 1e-6

    return df[["x", "y", "z", "datum"]]


def GetNav_simpleTest(navfile, navsys, xyzsys):
    navCols = ["x", "y", "z"]
    df = pd.read_csv(navfile, names=navCols)

    # No redatum
    df["datum"] = np.zeros(gdf.shape[0])

    return df[["x", "y", "z", "datum"]]
