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

    #print("REEEE CHANGE demcrs to dem.crs REEEEEE")
    #demcrs = "+proj=longlat +a=3396190 +no_defs"
    xform = pyproj.transformer.Transformer.from_crs(
        confDict["navigation"]["xyzsys"], dem.crs
    )

    nav, oDict, inv = prep.prep(confDict, dem, nav)

    bounds = prep.calcBounds(
        confDict,
        dem,
        nav,
        confDict["navigation"]["xyzsys"],
        confDict["facetParams"]["atdist"],
        confDict["facetParams"]["ctdist"],
    )

    rowSub = (bounds[2], bounds[3] + 1)
    colSub = (bounds[0], bounds[1] + 1)

    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write(
            "Subsetting DEM to\n\tRow: %d-%d\n\tCol: %d-%d\n"
            % (rowSub[0], rowSub[1], colSub[0], colSub[1])
        )

    win = rio.windows.Window.from_slices(rowSub, colSub)

    demData = dem.read(1, window=win)

    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write("Simulating %d traces\n" % len(nav))

    for i in range(nav.shape[0]):
        fcalc = sim.sim(confDict, dem, nav, xform, demData, win, i)
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
