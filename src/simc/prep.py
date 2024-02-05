import sys

import numpy as np
import pyproj
import sim


def findDupe(nav):
    # Find neighboring duplicate nav points. Return nav without them and an index array to reconstruct
    # Does not sort
    navl = len(nav)
    olen = 0
    inv = np.zeros(navl)
    uniq = np.ones(navl).astype(bool)

    for i in range(navl - 1):
        row = nav.iloc[i]
        nrow = nav.iloc[i + 1]

        inv[i] = olen

        dx = nrow.x - row.x
        dy = nrow.y - row.y
        dz = nrow.z - row.z
        d = dx + dy + dz

        if d:
            olen += 1
        else:
            uniq[i] = 0

    inv[i + 1] = olen

    return nav.iloc[uniq, :].reset_index(), inv


def prep(confDict, dem, nav):
    # Create data structures to hold output products
    oDict = {}
    out = confDict["outputs"]

    samps = confDict["simParams"]["tracesamples"]
    traces = len(nav)
    if out["combined"] or out["combinedadj"] or out["binary"]:
        oDict["combined"] = np.zeros((samps, traces)).astype(np.float64)

    if out["left"]:
        oDict["left"] = np.zeros((samps, traces)).astype(np.float64)

    if out["right"]:
        oDict["right"] = np.zeros((samps, traces)).astype(np.float64)

    if out["echomap"] or out["echomapadj"]:
        numCTfacets = int(
            2 * confDict["facetParams"]["ctdist"] / confDict["facetParams"]["ctstep"]
        )
        oDict["emap"] = np.zeros((numCTfacets + 1, traces)).astype(
            np.float64
        )  # echo power
        oDict["emap_angles"] = np.zeros((numCTfacets + 1, traces)).astype(
            np.float64
        )  # theta integrated along-track
        oDict["frmap"] = np.zeros((numCTfacets + 1, traces)).astype(
            bool
        )  # first return

    if out["fret"] or out["showfret"]:
        oDict["fret"] = np.zeros((traces, 4)).astype(np.float64)

    numFacets = int(
        2
        * (2 * confDict["facetParams"]["ctdist"] / confDict["facetParams"]["ctstep"])
        * (2 * confDict["facetParams"]["atdist"] / confDict["facetParams"]["atstep"])
    )

    # print("numFacets {}".format(numFacets))
    oDict["pwr"] = np.zeros((traces, numFacets)).astype(np.float64)
    oDict["twtt"] = np.zeros((traces, numFacets)).astype(np.float64)
    oDict["theta"] = np.zeros((traces, numFacets)).astype(np.float32)
    oDict["phi"] = np.zeros((traces, numFacets)).astype(np.float32)
    oDict["mx"] = np.zeros((traces, numFacets)).astype(np.float32)
    oDict["my"] = np.zeros((traces, numFacets)).astype(np.float32)
    oDict["mz"] = np.zeros((traces, numFacets)).astype(np.float32)
    # Remove duplicate entries, calculate inverse
    nav, inv = findDupe(nav)

    # Velocity vector components
    vx = np.gradient(nav["x"])
    vy = np.gradient(nav["y"])
    vz = np.gradient(nav["z"])
    vMag = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
    v = np.stack((vx / vMag, vy / vMag, vz / vMag), axis=1)
    nav["uv"] = list(v)

    # Vector to center of planet
    cx = -nav["x"]
    cy = -nav["y"]
    cz = -nav["z"]
    cMag = np.sqrt(cx ** 2 + cy ** 2 + cz ** 2)
    c = np.stack((cx / cMag, cy / cMag, cz / cMag), axis=1)

    # Right pointing cross track vector
    l = np.cross(c, v)
    lMag = np.sqrt(l[:, 0] ** 2 + l[:, 1] ** 2 + l[:, 2] ** 2)
    nav["ul"] = list(l / np.stack((lMag, lMag, lMag), axis=1))
    # print(nav["ul"])

    return nav, oDict, inv


def calcBounds(confDict, dem, demCrs, nav, xyzsys, atDist, ctDist):
    corners = np.zeros((len(nav) * 9, 3))

    for i in range(len(nav)):
        gx, gy, gz = sim.genGrid(nav, 1, 1, atDist, ctDist, i)

        corners[i * 9 : (i * 9) + 9, :] = np.stack((gx, gy, gz), axis=1)

    xform = pyproj.Transformer.from_crs(xyzsys, demCrs)
    demX, demY, demZ = xform.transform(corners[:, 0], corners[:, 1], corners[:, 2])
    gt = ~dem.transform
    # print("gt {}".format(gt))
    ix, iy = gt * (demX, demY)
    bounds = [int(min(ix)), int(max(ix)), int(min(iy)), int(max(iy))]

    # print(bounds)
    with open(confDict["paths"]["logpath"], "a") as fd:
        if bounds[0] < 0:
            fd.write("Warning: min X off of DEM -> {}\n".format(bounds[0]))
            bounds[0] = 0

        if bounds[1] > dem.width - 1:
            fd.write("Warning: max X off of DEM -> {}\n".format(bounds[1]))
            bounds[1] = dem.width - 1

        if bounds[2] < 0:
            fd.write("Warning: min y off of DEM -> {}\n".format(bounds[2]))
            bounds[2] = 0

        if bounds[3] > dem.height - 1:
            fd.write("Warning: max y off of DEM -> {}\n".format(bounds[3]))
            bounds[3] = dem.height - 1

    return bounds
