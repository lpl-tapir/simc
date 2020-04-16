import numpy as np
import sys
from PIL import Image
import pyproj
import matplotlib.pyplot as plt
import skimage.transform


def build(confDict, oDict, fcalc, nav, i):
    # bincount requires assumptions - all positive integers, nothing greater than tracelen. Need to make sure these are met
    out = confDict["outputs"]
    spt = confDict["simParams"]["tracesamples"]

    cti = fcalc[:, 8].astype(np.int32)
    lr = fcalc[:, 2]
    pwr = fcalc[:, 0]
    twtt = fcalc[:, 1]
    twttAdj = twtt - nav["datum"][i]
    cbin = (twttAdj / confDict["simParams"]["dt"]).astype(np.int32)

    cbin = np.mod(cbin, confDict["simParams"]["tracesamples"])

    if out["combined"] or out["combinedadj"]:
        # np.add.at(oDict["combined"][:,i], cbin, pwr)
        oDict["combined"][:, i] = np.bincount(
            cbin, weights=pwr, minlength=confDict["simParams"]["tracesamples"]
        )

    if out["left"]:
        # Left facets are first half
        # np.add.at(oDict["left"][:,i], cbin[lr == 0], pwr[lr == 0])
        oDict["left"][:, i] = np.bincount(
            cbin[lr == 0],
            weights=pwr[lr == 0],
            minlength=confDict["simParams"]["tracesamples"],
        )

    if out["right"]:
        # Right facets are second half
        # np.add.at(oDict["right"][:,i], cbin[lr == 1], pwr[lr == 1])
        oDict["right"][:, i] = np.bincount(
            cbin[lr == 1],
            weights=pwr[lr == 1],
            minlength=confDict["simParams"]["tracesamples"],
        )

    if out["fret"] or out["showfret"]:
        ffacet = fcalc[twttAdj == twttAdj.min(), :]
        oDict["fret"][i, 0:3] = ffacet[0, 5:8]

    if out["echomap"] or out["echomapadj"]:
        oDict["emap"][:, i] = np.bincount(
            cti, weights=pwr * (twtt ** 4), minlength=oDict["emap"].shape[0]
        )
        frFacets = cti[cbin == cbin.min()]
        oDict["frmap"][frFacets, i] = 1

    return 0


def save(confDict, oDict, nav, dem, demData, win):

    out = confDict["outputs"]
    nColor = [255, 0, 255]
    frColor = [50, 200, 200]

    if out["shownadir"] or out["nadir"] or out["echomap"] or out["echomapadj"]:
        # Find nadir lat/lon/elev and bin
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
        nlat, nlon, nelev = pyproj.transform(
            dem.crs, confDict["navigation"]["llesys"], gx, gy, demz
        )

        nr = np.sqrt((nx - x) ** 2 + (ny - y) ** 2 + (nz - z) ** 2)
        nbin = (
            ((2 * nr / confDict["simParams"]["speedlight"]) - nav["datum"].to_numpy())
            / 37.5e-9
        ).astype(np.int32)

        if out["nadir"]:
            nadInfo = np.zeros((nav.shape[0], 4))
            nadInfo[:, 0] = nlat
            nadInfo[:, 1] = nlon
            nadInfo[:, 2] = nelev
            nadInfo[:, 3] = nbin
            np.savetxt(
                confDict["paths"]["outpath"] + "nadir.csv",
                nadInfo,
                delimiter=",",
                header="lat,lon,elev_IAU2000,sample",
                comments="",
            )

    if out["showfret"] or out["fret"]:
        # Find fret lat/lon/elev and bin
        x = nav["x"].to_numpy()
        y = nav["y"].to_numpy()
        z = nav["z"].to_numpy()
        fret = oDict["fret"]

        fr = np.sqrt(
            (x - fret[:, 0]) ** 2 + (y - fret[:, 1]) ** 2 + (z - fret[:, 2]) ** 2
        )
        fbin = (
            ((2 * fr / confDict["simParams"]["speedlight"]) - nav["datum"].to_numpy())
            / 37.5e-9
        ).astype(np.int32)

        flat, flon, felev = pyproj.transform(
            confDict["navigation"]["xyzsys"],
            confDict["navigation"]["llesys"],
            fret[:, 0],
            fret[:, 1],
            fret[:, 2],
        )
        if out["fret"]:
            fretInfo = np.zeros((nav.shape[0], 4))
            fretInfo[:, 0] = flat
            fretInfo[:, 1] = flon
            fretInfo[:, 2] = felev
            fretInfo[:, 3] = fbin
            np.savetxt(
                confDict["paths"]["outpath"] + "firstReturn.csv",
                fretInfo,
                delimiter=",",
                header="lat,lon,elev_IAU2000,sample",
                comments="",
            )

    if out["combined"]:
        cgram = oDict["combined"] * (255.0 / oDict["combined"].max())
        cstack = np.dstack((cgram, cgram, cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(confDict["paths"]["outpath"] + "combined.png")

    if out["combinedadj"]:
        cgram = (oDict["combined"] * (255.0 / oDict["combined"].max())).astype(np.uint8)
        # Auto adjustment
        curve = np.fromfile("curve.txt", sep=" ")
        cgram = curve[cgram] * 255
        cstack = np.dstack((cgram, cgram, cgram)).astype("uint8")

        if out["showfret"]:
            for i in range(len(fbin)):
                b = fbin[i]
                if(not np.isnan(b)):
                    cstack[b, [i]] = nColor

        # Add in first return and nadir locations if requested
        if out["shownadir"]:
            for i in range(len(nbin)):
                if(nvalid[i]):
                    cstack[nbin[i], [i]] = frColor

        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(confDict["paths"]["outpath"] + "combinedAdj.png")

    if out["left"]:
        cgram = oDict["left"] * (255.0 / oDict["left"].max())
        cstack = np.dstack((cgram, cgram, cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(confDict["paths"]["outpath"] + "left.png")

    if out["right"]:
        cgram = oDict["right"] * (255.0 / oDict["right"].max())
        cstack = np.dstack((cgram, cgram, cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(confDict["paths"]["outpath"] + "right.png")

    if out["binary"]:
        oDict["combined"].astype("float32").tofile(
            confDict["paths"]["outpath"] + "combined.img"
        )

    if out["echomap"]:
        egram = oDict["emap"] * (255.0 / oDict["emap"].max())
        estack = np.dstack((egram, egram, egram)).astype(np.uint8)
        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(confDict["paths"]["outpath"] + "echomap.png")

    if out["echomapadj"]:
        emap = oDict["emap"]
        postSpace = np.sqrt(
            np.diff(nav["x"]) ** 2 + np.diff(nav["y"]) ** 2 + np.diff(nav["z"]) ** 2
        ).mean()
        ySquish = confDict["facetParams"]["ctstep"] / postSpace
        nz = emap != 0
        hclip = 1
        emap[nz] = emap[nz] - (emap[nz].mean() - hclip * emap[nz].std())
        emap = emap * (255.0 / (emap[nz].mean() + hclip * emap[nz].std()))
        emap = np.minimum(emap, 255)
        emap = np.maximum(0, emap)
        yDim = int(emap.shape[0] * ySquish)
        egram = skimage.transform.resize(emap, (yDim, len(nav)))
        frgram = oDict["frmap"]
        estack = np.dstack((egram, egram, egram)).astype(np.uint8)

        idx = np.arange(0,frgram.shape[0])
        for i in range(estack.shape[1]):
            fri = idx[frgram[:,i] == 1]
            fri = (fri*ySquish).astype(np.int32)
            estack[fri,i] = frColor
            estack[estack.shape[0]//2, i] = nColor

        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(confDict["paths"]["outpath"] + "echomapAdj.png")
