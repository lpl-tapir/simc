# Python 3.7

# Program to select and save a window of a DEM based on a nav file.

import h5py
import os
from multiprocessing import Pool

def main():
  datadir = "/zippy/MARS/targ/supl/UAF/2019/hdf5/"
  dem = "/zippy/MARS/targ/supl/grid-AKDEM/Alaska_albers_V2.tif"
  outdem = "/zippy/MARS/code/modl/simc/test/temp/dem/ak2019/"
  files = os.listdir(datadir)
  cmdlist = []
  for file in files:
    if(not file.endswith(".h5")):
      continue
    f = h5py.File(datadir + file, 'r')
    nav = f["nav0"][:]
    lat = [];
    lon = [];
    for i in range(len(nav)):
      lat.append(nav[i][0])
      lon.append(nav[i][1])

    maxlat = max(lat)
    minlat = min(lat)
    maxlon = max(lon)
    minlon = min(lon)

    cmd = "gdal_translate -projwin_srs EPSG:4326 -projwin " + str(minlon-1) + " " + str(maxlat+1) + " " + str(maxlon+1) + " " + str(minlat-1)
    cmd = cmd + " " + dem + " " + outdem + file.replace(".h5",".tif") 
    cmdlist.append(cmd)

  p = Pool(20)
  p.map(os.system, cmdlist)

main()
