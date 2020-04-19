import numpy as np
import sys
import pyproj
import sim


def prep(confDict, dem, nav, navl):
    # Create data structures to hold output products
    oDict = {}
    out = confDict["outputs"]

    samps = confDict["simParams"]["tracesamples"]
    traces = navl
    if out["combined"] or out["combinedadj"]:
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
        oDict["frmap"] = np.zeros((numCTfacets + 1, traces)).astype(
            np.bool
        )  # first return

    if out["fret"] or out["showfret"]:
        oDict["fret"] = np.zeros((traces, 4)).astype(np.float64)

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

    return nav, oDict


def calcBounds(
    confDict, dem, nav, xyzsys, atDist, ctDist,
):
    corners = np.zeros((len(nav) * 9, 3))

    for i in range(len(nav)):
        gx, gy, gz = sim.genGrid(nav, 1, 1, atDist, ctDist, i)

        corners[i * 9 : (i * 9) + 9, :] = np.stack((gx, gy, gz), axis=1)

    demX, demY, demZ = pyproj.transform(
        xyzsys, dem.crs, corners[:, 0], corners[:, 1], corners[:, 2]
    )
    gt = ~dem.transform
    ix, iy = gt * (demX, demY)
    bounds = [int(min(ix)), int(max(ix)), int(min(iy)), int(max(iy))]

    with open(confDict["paths"]["logpath"], "a") as fd:
        if bounds[0] < 0:
            fd.write("Warning: min X off of DEM -> {}\n".format(bounds[0]))
            bounds[0] = 0

        if bounds[1] > dem.width - 1:
            fd.write("Warning: max X off of DEM -> {}\n".format(bounds[1]))
            bounds[1] = dem.width - 1

        if bounds[2] < 0:
            fd.write("Warning: min y off of DEM -> {}".format(bounds[2]))
            bounds[2] = 0

        if bounds[3] > dem.height - 1:
            fd.write("Warning: max y off of DEM -> {}".format(bounds[3]))
            bounds[3] = dem.height - 1

    return bounds
