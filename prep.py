import numpy as np
import sys

def prep(confDict, dem, nav):
    # Create data structures to hold output products
    oDict = {}
    out = confDict["outputs"]

    samps = confDict["simParams"]["tracesamples"]
    traces = nav.shape[0]
    if(out["combined"] or out["combinedadj"]):
        oDict["combined"] = np.zeros((samps, traces)).astype(np.float64)

    if(out["left"]):
        oDict["left"] = np.zeros((samps, traces)).astype(np.float64)

    if(out["right"]):
        oDict["right"] = np.zeros((samps, traces)).astype(np.float64)

    if(out["echomap"] or out["echomapadj"]):
        numCTfacets = int(2*confDict["facetParams"]["ctdist"]/confDict["facetParams"]["ctstep"])
        oDict["emap"] = np.zeros((numCTfacets+1, traces)).astype(np.float64)

    if(out["fret"] or out["showfret"]):
        oDict["fret"] = np.zeros((traces, 4)).astype(np.float64)

    # Velocity vector components
    vx = np.gradient(nav["x"])
    vy = np.gradient(nav["y"])
    vz = np.gradient(nav["z"])
    vMag = np.sqrt(vx**2 + vy**2 + vz**2)
    v = np.stack((vx/vMag, vy/vMag, vz/vMag), axis=1)
    nav["uv"] = list(v)

    # Vector to center of planet
    cx = -nav["x"]
    cy = -nav["y"]
    cz = -nav["z"]
    cMag = np.sqrt(cx**2 + cy**2 + cz**2)
    c = np.stack((cx/cMag, cy/cMag, cz/cMag), axis=1)

    # Right pointing cross track vector
    l = np.cross(c, v)
    lMag = np.sqrt(l[:,0]**2 + l[:,1]**2 + l[:,2]**2)
    nav["ul"] = list(l/np.stack((lMag, lMag, lMag), axis=1))
    #print(nav["ul"])

    return nav, oDict