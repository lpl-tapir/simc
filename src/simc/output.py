import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import skimage.transform
from PIL import Image
import rasterio

import simc.curve


def build(confDict, oDict, fcalc, nav, xform, dem, win, i, oi):
    # bincount requires assumptions - all positive integers, nothing greater than tracelen. Need to make sure these are met
    out = confDict["outputs"]
    spt = confDict["simParams"]["tracesamples"]

    cmt = """
    # Apply ellipsoid correction
    angle = np.abs(
        np.arctan(nav["z"][i] / np.sqrt(nav["x"][i] ** 2 + nav["y"][i] ** 2))
    )

    # Mars ellipsoid parameters
    a = 3396190
    b = 3376200

    # Speed of light
    c = 299792458

    marsR = (a * b) / np.sqrt(
        (a**2) * (np.sin(angle) ** 2) + (b**2) * (np.cos(angle) ** 2)
    )

    corr = 2 * (3396000 - marsR) / 3e8"""

    cti = fcalc[:, 8].astype(np.int32)
    lr = fcalc[:, 2]
    pwr = fcalc[:, 0]
    twtt = fcalc[:, 1]
    twttAdj = twtt - nav["datum"][i]
    cbin = (twttAdj / confDict["simParams"]["dt"]).astype(np.int32)

    # Get rid of data that is after end of trace
    pwr[cbin >= confDict["simParams"]["tracesamples"]] = 0

    # Modulo enforces sharad FPB matching behavior. Should probably do this in a better way
    cbin = np.mod(cbin, confDict["simParams"]["tracesamples"])

    # Add echo power map ref if necessary
    if "emap_ref" not in oDict.keys():
        scale = 2
        oDict["emap_ref"] = np.zeros(
            (win.height // scale + 1, win.width // scale + 1)
        )  # georeferenced echo power map
        oDict["emap_ref_count"] = np.zeros(
            (win.height // scale + 1, win.width // scale + 1)
        )  # georeferenced echo power map
        oDict["emap_ref_xform"] = dem.window_transform(win) * dem.window_transform(
            win
        ).scale(
            scale
        )  # Edit resolution

    for j in oi:
        if out["combined"] or out["combinedadj"] or out["binary"]:
            oDict["combined"][:, j] = np.bincount(
                cbin, weights=pwr, minlength=confDict["simParams"]["tracesamples"]
            )

        if out["left"]:
            oDict["left"][:, j] = np.bincount(
                cbin[lr == 0],
                weights=pwr[lr == 0],
                minlength=confDict["simParams"]["tracesamples"],
            )

        if out["right"]:
            oDict["right"][:, j] = np.bincount(
                cbin[lr == 1],
                weights=pwr[lr == 1],
                minlength=confDict["simParams"]["tracesamples"],
            )

        if out["fret"] or out["showfret"]:
            ffacet = fcalc[twttAdj == twttAdj.min(), :]
            oDict["fret"][j, 0:3] = ffacet[0, 5:8]

        if out["echomap"] or out["echomapadj"]:
            oDict["emap"][:, j] = np.bincount(
                cti, weights=pwr * (twtt**4), minlength=oDict["emap"].shape[0]
            )

            # Mask out no-power bins
            cbin_mask = cbin[:].astype(np.float32)
            cbin_mask[pwr == 0] = np.nan

            frFacets = cti[cbin_mask == np.nanmin(cbin_mask)]
            oDict["frmap"][frFacets, j] = 1

            # Map facets back to dem grid
            gt = ~oDict["emap_ref_xform"]
            gtx, gty, gtz = xform.transform(
                fcalc[:, 5], fcalc[:, 6], fcalc[:, 7], direction="FORWARD"
            )
            ix, iy = gt * (gtx, gty)
            ix = ix.astype(np.int32)
            iy = iy.astype(np.int32)

            oDict["emap_ref"][iy, ix] += fcalc[:, 0]
            oDict["emap_ref_count"][iy, ix] += 1

            # if not i % 1000 and i != 0:
            #    plt.imshow(oDict["emap_ref"] / oDict["emap_ref_count"], aspect="auto")
            #    plt.show()

    # valid = np.ones(ix.shape).astype(bool)
    # demz = np.zeros(ix.shape).astype(np.float32)

    return 0


def save(confDict, oDict, nav, dem, win, demData):
    out = confDict["outputs"]
    frColor = [255, 0, 255]
    nColor = [50, 200, 200]

    if out["shownadir"] or out["nadir"] or out["echomap"] or out["echomapadj"]:
        # Find nadir lat/lon/elev and bin
        x = nav["x"].to_numpy()
        y = nav["y"].to_numpy()
        z = nav["z"].to_numpy()

        xyz2dem = pyproj.Transformer.from_crs(confDict["navigation"]["xyzsys"], dem.crs)
        gx, gy, gz = xyz2dem.transform(x, y, z)

        gt = ~dem.window_transform(win)
        ix, iy = gt * (gx, gy)
        ix = ix.astype(np.int32)
        iy = iy.astype(np.int32)

        nvalid = np.ones(ix.shape).astype(bool)
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

        dem2xyz = pyproj.Transformer.from_crs(dem.crs, confDict["navigation"]["xyzsys"])
        nx, ny, nz = dem2xyz.transform(gx, gy, demz)

        dem2lle = pyproj.Transformer.from_crs(dem.crs, confDict["navigation"]["llesys"])
        nlat, nlon, nelev = dem2lle.transform(gx, gy, demz)

        nr = np.sqrt((nx - x) ** 2 + (ny - y) ** 2 + (nz - z) ** 2)

        nbin = (
            ((2 * nr / confDict["simParams"]["speedlight"]) - nav["datum"].to_numpy())
            / confDict["simParams"]["dt"]
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
                fmt="%.6f,%.6f,%.3f,%d",
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
            / confDict["simParams"]["dt"]
        ).astype(np.int32)

        xyz2lle = pyproj.Transformer.from_crs(
            confDict["navigation"]["xyzsys"], confDict["navigation"]["llesys"]
        )
        flat, flon, felev = xyz2lle.transform(fret[:, 0], fret[:, 1], fret[:, 2])

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
                fmt="%.6f,%.6f,%.3f,%d",
                comments="",
            )

    if out["combined"]:
        cgram = oDict["combined"] * (255.0 / oDict["combined"].max())
        cstack = np.dstack((cgram, cgram, cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(confDict["paths"]["outpath"] + "combined.png")

    if out["combinedadj"]:
        # cgram = (oDict["combined"] * (255.0 / oDict["combined"].max())).astype(np.uint8)
        cgram = oDict["combined"]

        # Scale image - clip by 2% on low and high end then log scale
        cliplo = np.percentile(cgram[cgram > 0], 1)
        # cliphi = np.percentile(cgram[cgram > 0], 99.9)
        # cgram[cgram < cliplo] = cliplo
        # cgram[cgram > cliphi] = cliphi
        cgram = np.log10(cgram + cliplo)
        cgram -= np.min(cgram)
        cgram /= np.max(cgram)
        cgram *= 255
        cgram = cgram.astype(np.uint8)

        # scaling = np.array(simc.curve.curve)
        # cgram = scaling[cgram] * 255
        cstack = np.dstack((cgram, cgram, cgram)).astype("uint8")

        # Add in first return and nadir locations if requested
        if out["showfret"]:
            frvalid = nvalid[:]
            frvalid[np.abs(fbin) >= confDict["simParams"]["tracesamples"]] = 0
            for i in range(len(fbin)):
                b = fbin[i]
                if not np.isnan(b) and abs(b) < confDict["simParams"]["tracesamples"]:
                    cstack[b, [i]] = frColor

        if out["shownadir"]:
            for i in range(len(nbin)):
                if nvalid[i] and abs(b) < confDict["simParams"]["tracesamples"]:
                    cstack[nbin[i], [i]] = nColor

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
        # egram = oDict["emap"] * (255.0 / oDict["emap"].max())
        # egram_color = np.copy(egram)

        # estack = np.dstack((egram, egram, egram)).astype(np.uint8)
        # eimg = Image.fromarray(estack)
        # eimg = eimg.convert("RGB")
        # eimg.save(confDict["paths"]["outpath"] + "echomap.png")

        # Scale echo power map
        egram = oDict["emap_ref"]
        egram[oDict["emap_ref_count"] > 0] /= oDict["emap_ref_count"][
            oDict["emap_ref_count"] > 0
        ]

        # Scale image - clip by 2% on low and high end then log scale
        cliplo = np.percentile(egram[egram > 0], 1)
        egram = np.log10(egram + cliplo / (np.max(egram + cliplo)))
        egram[oDict["emap_ref_count"] == 0] = np.nan

        with rasterio.open(
            confDict["paths"]["outpath"] + "echomap.tif",
            "w",
            driver="GTiff",
            height=oDict["emap_ref"].shape[0],
            width=oDict["emap_ref"].shape[1],
            count=1,
            dtype=np.float32,
            crs=dem.crs,
            transform=oDict["emap_ref_xform"],
        ) as dst:
            dst.write_band(
                1,
                egram,
            )

    if out["echomapadj"]:
        # Resize
        emap = oDict["emap"]
        emap_angles = oDict["emap_angles"]
        postSpace = np.sqrt(
            np.diff(nav["x"]) ** 2 + np.diff(nav["y"]) ** 2 + np.diff(nav["z"]) ** 2
        ).mean()
        ySquish = confDict["facetParams"]["ctstep"] / postSpace
        yDim = np.floor(emap.shape[0] * ySquish).astype(np.int32) + 1

        idx = np.arange(0, emap.shape[0])
        nidx = np.floor(idx * ySquish).astype(np.int32)
        egram = np.zeros((yDim, emap.shape[1]))
        ecount = np.zeros((yDim, emap.shape[1]))

        frmap = oDict["frmap"]
        frgram = np.zeros((yDim, frmap.shape[1]))

        egram = skimage.transform.resize(emap, (yDim, emap.shape[1]))

        # Shrink emap and frmap
        for i in range(egram.shape[1]):
            frgram[:, i] = np.bincount(nidx, weights=frmap[:, i], minlength=yDim)

        nz = egram != 0
        hclip = 1.5
        egram[nz] = egram[nz] - (egram[nz].mean() - hclip * egram[nz].std())
        egram = egram * (255.0 / (egram[nz].mean() + hclip * egram[nz].std()))
        egram = np.minimum(egram, 255)
        egram = np.maximum(0, egram)

        estack = np.dstack((egram, egram, egram)).astype(np.uint8)

        for i in range(egram.shape[1]):
            fri = frgram[:, i] > 0
            estack[fri, i] = frColor
            estack[estack.shape[0] // 2, i] = nColor

        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(confDict["paths"]["outpath"] + "echomapAdj.png")
