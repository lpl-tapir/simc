import sys, h5py
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import rasterio as rio
import numpy as np
import pyproj

# These functions must return a pandas dataframe with the 
# following cols -
# ["x", "y", "z", "datum"]
# Where XYZ are planetocentric radar platform location
# and datum should be all zeros if no time shift is required, otherwise the
# time shift in seconds

def GetNav_FPBgeom(navfile, navsys, xyzsys):
  c = 299792458
  geomCols = ["trace", "time", "lat", "lon", "marsRad", "elev", "radiVel", "tangVel", "SZA", "phaseD"]
  df = pd.read_csv(navfile, names=geomCols)

  # Planetocentric lat/lon/radius to X/Y/Z - no need for navsys in this one
  df["x"] = (df["elev"]*1000)*np.cos(np.radians(df["lat"]))*np.cos(np.radians(df["lon"]))
  df["y"] = (df["elev"]*1000)*np.cos(np.radians(df["lat"]))*np.sin(np.radians(df["lon"]))
  df["z"] = (df["elev"]*1000)*np.sin(np.radians(df["lat"]))

  # Set up geodataframe 
  points = df.apply(lambda row: Point(row.x, row.y, row.z), axis=1)
  gdf = gpd.GeoDataFrame(df, geometry=points)
  gdf.crs = xyzsys

  # Find datum time with areoid
  aer = rio.open('../test/dem/mega_16.tif', 'r')
  gdfAer = gdf.to_crs(aer.crs)
  iy,ix = aer.index(gdfAer.geometry.x, gdfAer.geometry.y)
  ix = np.array(ix)
  iy = np.array(iy)

  # Temp fix mola meters/pix issue
  ix[ix > aer.width-1] = aer.width-1

  zval = aer.read(1)[iy,ix]
  gdf["datum"] = ((1000*gdf["elev"]-3396000-zval)*2/c) - (1800 * 37.5e-9)
  #print(gdf["datum"])

  return gdf[["x", "y", "z", "datum"]]

def GetNav_QDAetm(navfile, navsys, xyzsys):
  c = 299792458
  etmCols = ["trace", "epoch", "alt", "sza", "lat", "lon",
              "molaNadir", "vrad", "vtan", "dist", "tshift",
              "radius", "utc0","utc1"] 

  df = pd.read_csv(navfile, names=etmCols, sep="\s+")

  df["x"], df["y"], df["z"] = pyproj.transform(navsys, xyzsys, df["lon"].to_numpy(),
                                df["lat"].to_numpy(), (1000*df["alt"]).to_numpy())
  df["datum"] = df["tshift"]*1e-6

  return df[["x", "y", "z", "datum"]]

def GetNav_simpleTest(navfile, navsys, xyzsys):
  navCols = ["x", "y", "z"]
  df = pd.read_csv(navfile, names=navCols)

  # No redatum
  df["datum"] = np.zeros(gdf.shape[0])

  return df[["x", "y", "z", "datum"]]