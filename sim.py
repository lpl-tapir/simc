import numpy as np
import pyproj
import rasterio as rio
import sys
import scipy


def sim(confDict, dem, nav, xform, demData, win, i):
    atStep = confDict["facetParams"]["atstep"]
    ctStep = confDict["facetParams"]["ctstep"]
    atDist = confDict["facetParams"]["atdist"]
    ctDist = confDict["facetParams"]["ctdist"]
    atNum = atDist // atStep
    ctNum = ctDist // ctStep

    # Geotransform DEM x,y to pixel coordinates
    gt = ~dem.window_transform(win)

    # Generate grid in xyz space
    gx, gy, gz = genGrid(nav, ctNum, atNum, atStep, ctStep, i)

    # Transform to dem CRS and sample DEM
    gtx, gty, gtz = xform.transform(gx, gy, gz, direction="FORWARD")

    # Sample DEM
    ix, iy = gt * (gtx, gty)
    ix = ix.astype(np.int32)
    iy = iy.astype(np.int32)

    valid = np.ones(ix.shape).astype(np.bool)
    demz = np.zeros(ix.shape).astype(np.float32)

    # If dembump turned on, fix off dem values
    if confDict["simParams"]["dembump"]:
        ix[ix < 0] = 0
        ix[ix > (demData.shape[1] - 1)] = demData.shape[1] - 1
        iy[iy < 0] = 0
        iy[iy > (demData.shape[0] - 1)] = demData.shape[0] - 1
    else:
        valid[ix < 0] = 0
        valid[ix > (demData.shape[1] - 1)] = 0
        valid[iy < 0] = 0
        valid[iy > (demData.shape[0] - 1)] = 0

    demz[valid] = demData[iy[valid], ix[valid]]

    # Mark nodata vals as invalid
    valid[demz == dem.nodata] = 0

    # If there are no valid facets
    if(np.sum(valid) == 0):
        return np.array([])

    # Transform back to xyz for facet calcs
    sx, sy, sz = xform.transform(gtx, gty, demz, direction="INVERSE")

    shape = (2 * int(atNum) + 1, 2 * int(ctNum) + 1)
    sx = np.reshape(sx, shape)
    sy = np.reshape(sy, shape)
    sz = np.reshape(sz, shape)
    valid = np.reshape(valid, shape)

    surface = np.stack((sx, sy, sz), axis=0)
    facets = genFacets(surface, valid)
    fcalc = calcFacets(
        facets,
        nav["x"][i],
        nav["y"][i],
        nav["z"][i],
        confDict["simParams"]["speedlight"],
    )

    return fcalc


def genGrid(nav, ctNum, atNum, atStep, ctStep, i):
    # Generate XYZ grid
    ua = nav["uv"][i] * atStep  # along track vector (forward)
    uc = nav["ul"][i] * ctStep  # cross track vector (right)

    # Use meshgrid to come up with vectors to grid points
    ati = np.arange(atNum, -atNum - 1, -1)
    cti = np.arange(-ctNum, ctNum + 1)
    mgrd = np.meshgrid(cti, ati)

    dATx = mgrd[1] * ua[0]
    dATy = mgrd[1] * ua[1]
    dATz = mgrd[1] * ua[2]

    dCTx = mgrd[0] * uc[0]
    dCTy = mgrd[0] * uc[1]
    dCTz = mgrd[0] * uc[2]

    dx = dATx + dCTx
    dy = dATy + dCTy
    dz = dATz + dCTz

    # Add vectors to nav points to get grid
    px = nav["x"][i]
    py = nav["y"][i]
    pz = nav["z"][i]

    gx = dx + px
    gy = dy + py
    gz = dz + pz

    return gx.flatten(), gy.flatten(), gz.flatten()


def calcFacets(f, px, py, pz, c):
    # Calculate return power and twtt for facets

    # Array to hold output data
    # Col 1 is power
    # Col 2 is two way travel time
    # Col 3 is empty
    # Col 4 is whether the facet is to the right or left of the platform
    # Col 5 is a flag for whether to use the facet
    # Cols 6-8 hold x,y,z for the facet center
    # Col 9 holds the facet's cross track index
    fcalc = np.zeros((f.shape[0], 9))

    # Calc midpoints
    mx = (f[:, 0] + f[:, 3] + f[:, 6]) / 3
    my = (f[:, 1] + f[:, 4] + f[:, 7]) / 3
    mz = (f[:, 2] + f[:, 5] + f[:, 8]) / 3

    # Calc distances to platform/twtt
    rx = px - mx
    ry = py - my
    rz = pz - mz

    r = np.sqrt(rx ** 2 + ry ** 2 + rz ** 2)

    ## Calc area and normal vector
    # Calc 2->1 vector
    f[:, 3] = f[:, 0] - f[:, 3]  # x
    f[:, 4] = f[:, 1] - f[:, 4]  # y
    f[:, 5] = f[:, 2] - f[:, 5]  # z
    # Calc 1->3 vector
    f[:, 0] = f[:, 6] - f[:, 0]  # x
    f[:, 1] = f[:, 7] - f[:, 1]  # y
    f[:, 2] = f[:, 8] - f[:, 2]  # z
    # Calc cross product
    f[:, 6:9] = np.cross(f[:, 3:6], f[:, 0:3])
    area = np.sqrt(f[:, 6] ** 2 + f[:, 7] ** 2 + f[:, 8] ** 2) / 2

    ## Calc power
    # Dot product between facet center -> platform and normal to facet
    ct = (rx * f[:, 6]) + (ry * f[:, 7]) + (rz * f[:, 8])
    ct = ct / (r * area * 2)

    fcalc[:, 0] = np.abs(((area * ct) ** 2) / (r ** 4))  # power
    fcalc[:, 1] = 2 * r / c  # twtt
    fcalc[:, 2] = f[:, 10]  # right or left
    fcalc[:, 4] = 1  # use all facets for now
    fcalc[:, 5] = mx  # Facet centers
    fcalc[:, 6] = my
    fcalc[:, 7] = mz
    fcalc[:, 8] = f[:, 11]  # Cross track indices for echo power map

    return fcalc


def genFacets(s, valid):
    # Generate list of facets (f) from surface grid (s)
    # Facets that contain a point that is not valid will
    # not be evaluated later
    h = s.shape[1]
    w = s.shape[2]

    nfacet = (w - 1) * (h - 1) * 2  # number of facets
    qt = int(nfacet / 4)  # quarter
    hf = int(nfacet / 2)  # half
    tq = hf + qt  # three quarters

    # Array to hold facet data
    # Cols 1-9 hold (x1,y1,z1,x2,...,z3) of the facet corners
    # Col 10 holds whether the facet is valid and should be evaluated
    # Col 11 holds whether the facet is left or right side left is 0, right is 1
    # Col 12 holds the cross-track index of the facet. This is for the echo power map
    f = np.zeros((nfacet, 12))
    fkeep = np.ones(nfacet).astype(np.bool)

    # Ordering of points along axis 1 is important for cross product later
    # Ordering of points along axis 0 is important for left/right side

    atSlices = [
        slice(0, h - 1),
        slice(0, h - 1),
        slice(1, h),
        slice(1, h),
        slice(1, h),
        slice(0, h - 1),
        slice(0, h - 1),
        slice(0, h - 1),
        slice(1, h),
        slice(1, h),
        slice(1, h),
        slice(0, h - 1),
    ]

    ctSlices = [
        slice(0, (w - 1) // 2),
        slice(1, (w + 1) // 2),
        slice(0, (w - 1) // 2),
        slice(1, (w + 1) // 2),
        slice(0, (w - 1) // 2),
        slice(1, (w + 1) // 2),
        slice((w - 1) // 2, w - 1),
        slice((w + 1) // 2, w),
        slice((w - 1) // 2, w - 1),
        slice((w + 1) // 2, w),
        slice((w - 1) // 2, w - 1),
        slice((w + 1) // 2, w),
    ]

    lstSlices = [slice(0, qt), slice(qt, hf), slice(hf, tq), slice(tq, nfacet)]

    for i in range(4):
        for j in range(3):
            f[lstSlices[i], 3 * j] = s[
                0, atSlices[i * 3 + j], ctSlices[i * 3 + j]
            ].flatten()  # X
            f[lstSlices[i], 3 * j + 1] = s[
                1, atSlices[i * 3 + j], ctSlices[i * 3 + j]
            ].flatten()  # Y
            f[lstSlices[i], 3 * j + 2] = s[
                2, atSlices[i * 3 + j], ctSlices[i * 3 + j]
            ].flatten()  # Z
            fkeep[lstSlices[i]] &= valid[
                atSlices[i * 3 + j], ctSlices[i * 3 + j]
            ].flatten()

    # Add in lr entry - l=0, r=1
    f[0:hf, 10] = 0
    f[hf:nfacet, 10] = 1

    # Add in cross track indices for echo power map
    hm0 = np.arange(0, h - 1)
    wm0 = np.arange(0, (w - 1) // 2)
    wm0, hm0 = np.meshgrid(wm0, hm0)
    f[0:qt, 11] = wm0.flatten()
    f[qt:hf, 11] = wm0.flatten()

    hm1 = np.arange(0, h - 1)
    wm1 = np.arange((w - 1) // 2, w - 1)
    wm1, hm1 = np.meshgrid(wm1, hm1)
    f[hf:tq, 11] = wm1.flatten()
    f[tq:nfacet, 11] = wm1.flatten()

    return f[fkeep]
