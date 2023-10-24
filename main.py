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
    print("dem {}".format(dem.crs))

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

   
    demCrs = dem.crs
    try:
        xform = pyproj.transformer.Transformer.from_crs(
            confDict["navigation"]["xyzsys"], dem.crs
        )
    except:
        print("reading dem crs failed, setting crs to xform manually")
        demCrs = "+proj=longlat +R=3396190 +no_defs"
        xform = pyproj.transformer.Transformer.from_crs(
            confDict["navigation"]["xyzsys"], demCrs
        )

    print("xform {}".format(xform))

    nav, oDict, inv = prep.prep(confDict, dem, nav)

    bounds = prep.calcBounds(
        confDict,
        dem,
        nav,
        confDict["navigation"]["xyzsys"],
        confDict["facetParams"]["atdist"],
        confDict["facetParams"]["ctdist"],
    )

    print("bounds {}".format(bounds))
    rowSub = (bounds[2], bounds[3] + 1)
    colSub = (bounds[0], bounds[1] + 1)

    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write(
            "Subsetting DEM to\n\tRow: %d-%d\n\tCol: %d-%d\n"
            % (rowSub[0], rowSub[1], colSub[0], colSub[1])
        )

    win = rio.windows.Window.from_slices(rowSub, colSub)
    print("win {}".format(win))
    demData = dem.read(1, window=win)
    print("dem shape {}".format(dem.read(1).shape))
    print("demData shape {}".format(demData.shape))
    #demData = dem.read(1)

    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write("Simulating %d traces\n" % len(nav))
    
    for i in range(nav.shape[0]):
        fcalc = sim.sim(confDict, dem, nav,  xform, demData, win, i)
        #fcalc = sim.sim(confDict, dem, nav, normal, xform, demData, win, i)
        if fcalc.shape[0] == 0:
            continue

        # Putting things back in order
        oi = np.where(inv == i)[0]
        output.build(confDict, oDict, fcalc, nav, i, oi)

    nav = nav.iloc[inv, :].reset_index()
    output.save(confDict, oDict, nav, dem, demData, demCrs, win)
    dem.close()

    stopTime = time.time()
    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write("Wall clock runtime: %.2fs" % (stopTime - startTime))


# execute only if run as a script.
if __name__ == "__main__":
    main()
