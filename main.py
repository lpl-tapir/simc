import sys
import ingest, prep, sim, output
import rasterio as rio
import numpy as np
import pandas as pd
import pprint
import pyproj
import time
import matplotlib.pyplot as plt


def main():
    startTime = time.time()
    version = 1.1
    argDict = ingest.parseCmd()
    confDict = ingest.readConfig(argDict)
    dem = rio.open(confDict["paths"]["dempath"], mode="r")
    #print("dem {}".format(dem.crs))

    nav = ingest.readNav(
        confDict["paths"]["navpath"],
        confDict["navigation"]["navsys"],
        confDict["navigation"]["xyzsys"],
        confDict["navigation"]["navfunc"],
    )

    with open(confDict["paths"]["logpath"], "w") as fd:
        fd.write(
            "University of Arizona Clutter Simulator Log File\nVersion %.1f\n" % version
        )
        pprint.pprint(confDict, stream=fd)

    xform = pyproj.transformer.Transformer.from_crs(
        confDict["navigation"]["xyzsys"], dem.crs
    )
    #print("xform {}".format(xform))

    nav, oDict, inv = prep.prep(confDict, dem, nav)

    bounds = prep.calcBounds(
        confDict,
        dem,
        nav,
        confDict["navigation"]["xyzsys"],
        confDict["facetParams"]["atdist"],
        confDict["facetParams"]["ctdist"],
    )

    #print("bounds {}".format(bounds))
    rowSub = (bounds[2], bounds[3] + 1)
    colSub = (bounds[0], bounds[1] + 1)

    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write(
            "Subsetting DEM to\n\tRow: %d-%d\n\tCol: %d-%d\n"
            % (rowSub[0], rowSub[1], colSub[0], colSub[1])
        )

    win = rio.windows.Window.from_slices(rowSub, colSub)
    #print("win {}".format(win))
    demData = dem.read(1, window=win)
    #demData = dem.read(1)

    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write("Simulating %d traces\n" % len(nav))
    '''
    x = nav["x"].to_numpy()
    y = nav["y"].to_numpy()
    z = nav["z"].to_numpy()
    gx, gy, gz = pyproj.transform(
        confDict["navigation"]["xyzsys"], dem.crs, x, y, z
    )

    gt = ~dem.window_transform(win)
    ix, iy = gt * (gx, gy)
    ix = ix.astype(np.int32)
    iy = iy.astype(np.int32)

    nvalid = np.ones(ix.shape).astype(np.bool)
    demz = np.zeros(ix.shape).astype(np.float32)

    # If dembump turned on, fix off dem values
    if confDict["simParams"]["dembump"]:
        ix[ix < 0] = 0
        ix[ix > (demData.shape[1] - 1)] = demData.shape[1] - 1
        iy[iy < 0] = 0
        iy[iy > (demData.shape[0] - 1)] = demData.shape[0] - 1
    else:
        nvalid[ix < 0] = 0
        nvalid[ix > (demData.shape[1] - 1)] = 0
        nvalid[iy < 0] = 0
        nvalid[iy > (demData.shape[0] - 1)] = 0

    demz[nvalid] = demData[iy[nvalid], ix[nvalid]]
    nvalid[demz == dem.nodata] = 0

    nx, ny, nz = pyproj.transform(
        dem.crs, confDict["navigation"]["xyzsys"], gx, gy, demz
    )
    lon, lat, elev = pyproj.transform(
        "+proj=geocent +a=1737400 +b=1737400 +no_defs",
        "+proj=longlat +a=1737400 +b=1737400 +no_defs",
        nx, 
        ny,
        nz,            
    )
    nlon, nlat, nelev = pyproj.transform(
        dem.crs, confDict["navigation"]["llesys"], gx, gy, demz
    )
    normal = [nx, ny, nz]
    '''
    for i in range(nav.shape[0]):
        fcalc = sim.sim(confDict, dem, nav,  xform, demData, win, i)
        #fcalc = sim.sim(confDict, dem, nav, normal, xform, demData, win, i)
        if fcalc.shape[0] == 0:
            continue

        # Putting things back in order
        oi = np.where(inv == i)[0]
        output.build(confDict, oDict, fcalc, nav, i, oi)

    nav = nav.iloc[inv, :].reset_index()
    output.save(confDict, oDict, nav, dem, demData, win)
    dem.close()

    stopTime = time.time()
    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write("Wall clock runtime: %.2fs" % (stopTime - startTime))


# execute only if run as a script.
if __name__ == "__main__":
    main()
