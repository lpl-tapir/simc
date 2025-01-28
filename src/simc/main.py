import pprint
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import rasterio as rio
import tqdm

import simc.ingest
import simc.output
import simc.prep
import simc.sim


def main():
    startTime = time.time()
    version = 1.1
    argDict = simc.ingest.parseCmd()
    confDict = simc.ingest.readConfig(argDict)
    dem = rio.open(confDict["paths"]["dempath"], mode="r")

    nav = simc.ingest.readNav(
        confDict["paths"]["navpath"],
        confDict["navigation"]["navsys"],
        confDict["navigation"]["xyzsys"],
        confDict["navigation"]["navfunc"],
    )

    xform = pyproj.Transformer.from_crs(
        confDict["navigation"]["xyzsys"], confDict["navigation"]["llesys"]
    )

    with open(confDict["paths"]["logpath"], "w") as fd:
        fd.write(
            "University of Arizona Clutter Simulator Log File\nVersion %.1f\n" % version
        )
        pprint.pprint(confDict, stream=fd)

    # Parse dem CRS
    demcrs = pyproj.CRS.from_user_input(dem.crs)
    xform = pyproj.Transformer.from_crs(confDict["navigation"]["xyzsys"], demcrs)

    nav, oDict, inv = simc.prep.prep(confDict, dem, nav)

    bounds = simc.prep.calcBounds(
        confDict,
        dem,
        dem.crs,
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

    for i in tqdm.tqdm(range(nav.shape[0]), disable=(not argDict["p"])):
        fcalc = simc.sim.sim(confDict, dem, nav, xform, demData, win, i)
        if fcalc.shape[0] == 0:
            continue

        # Putting things back in order
        oi = np.where(inv == i)[0]
        simc.output.build(confDict, oDict, fcalc, nav, xform, dem, win, i, oi)

    nav = nav.iloc[inv, :].reset_index()
    simc.output.save(confDict, oDict, nav, dem, win, demData)
    dem.close()

    stopTime = time.time()
    with open(confDict["paths"]["logpath"], "a") as fd:
        fd.write("Wall clock runtime: %.2fs" % (stopTime - startTime))


if __name__ == "__main__":
    main()
