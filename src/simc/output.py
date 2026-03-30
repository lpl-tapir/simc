import sys

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import rasterio
import skimage.transform
from PIL import Image

from simc import curve


def build(
    confDict, oDict, fcalc, dem, win, xform, nav, i, oi
):
    # bincount requires assumptions - all positive integers, nothing greater than tracelen. Need to make sure these are met
    out = confDict["outputs"]
    spt = confDict["simParams"]["tracesamples"]

    cti = fcalc[:, 8].astype(np.int32)
    lr = fcalc[:, 2]
    pwr = fcalc[:, 0]
    twtt = fcalc[:, 1]
    theta = fcalc[:, 9]
    twttAdj = twtt - nav["datum"][i]
    cbin = (twttAdj / confDict["simParams"]["dt"]).astype(
        np.int32
    )
    cbin_float = (
        twttAdj / confDict["simParams"]["dt"]
    ).astype(np.float32)

    cbin = np.mod(
        cbin, confDict["simParams"]["tracesamples"]
    )

    # Add georef echo power map holder if necessary
    # This cannot go in prep because it needs dem window information
    # Add echo power map ref if necessary
    if "emap_ref" not in oDict.keys():
        scale = 2
        # Needed to add an adaptive scale range due to the difference in raster size
        if (win.height // 8 >= 300) and (
            win.width // 8 >= 300
        ):
            scale = 8

        oDict["emap_ref"] = np.zeros(
            (
                win.height // scale + 1,
                win.width // scale + 1,
            )
        )  # georeferenced echo power map
        oDict["emap_ref_count"] = np.zeros(
            (
                win.height // scale + 1,
                win.width // scale + 1,
            )
        )  # georeferenced echo power map
        oDict["emap_ref_xform"] = dem.window_transform(
            win
        ) * dem.window_transform(win).scale(
            scale
        )  # Edit resolution

    for j in oi:
        if (
            out["combined"]
            or out["combinedadj"]
            or out["binary"]
        ):
            oDict["combined"][:, j] = np.bincount(
                cbin,
                weights=pwr,
                minlength=confDict["simParams"][
                    "tracesamples"
                ],
            )

        if out["combinedcolored"] or out["echomapcolored"]:
            swathAngle = float(
                confDict["simParams"]["swathangle"]
            )
            oDict["combined_center"][:, j] = np.bincount(
                cbin,
                weights=pwr * (theta <= (swathAngle / 2)),
                minlength=confDict["simParams"][
                    "tracesamples"
                ],
            )
            oDict["combined_sides"][:, j] = np.bincount(
                cbin,
                weights=pwr * (theta > (swathAngle / 2)),
                minlength=confDict["simParams"][
                    "tracesamples"
                ],
            )

        if out["left"]:
            oDict["left"][:, j] = np.bincount(
                cbin[lr == 0],
                weights=pwr[lr == 0],
                minlength=confDict["simParams"][
                    "tracesamples"
                ],
            )

        if out["right"]:
            oDict["right"][:, j] = np.bincount(
                cbin[lr == 1],
                weights=pwr[lr == 1],
                minlength=confDict["simParams"][
                    "tracesamples"
                ],
            )

        if out["fret"] or out["showfret"]:
            ffacet = fcalc[twttAdj == twttAdj.min(), :]
            oDict["fret"][j, 0:3] = ffacet[0, 5:8]

        if (
            out["echomap"]
            or out["echomapadj"]
            or out["echomapcolored"]
            or out["echomapgeoref"]
        ):
            oDict["emap"][:, j] = np.bincount(
                cti,
                weights=pwr * (twtt**4),
                minlength=oDict["emap"].shape[0],
            )
            oDict["emap_angles"][:, j] = np.bincount(
                cti,
                weights=theta,
                minlength=oDict["emap"].shape[0],
            )
            # frFacets = cti[cbin_float == cbin_float.min()] #comparison of floats
            frFacets = cti[
                cbin == cbin.min()
            ]  # comparison of integers
            # ffacet = fcalc[pwr > (pwr.max() - ((pwr.max() - pwr.min()) / 2)) , :]
            oDict["frmap"][frFacets, j] = 1
            # for k in range(-9, 10):
            #    oDict["frmap"][frFacets+k, j] = 1

            # Map facets back to dem grid for georeferenced echo power map
            gt = ~oDict["emap_ref_xform"]
            gtx, gty, gtz = xform.transform(
                fcalc[:, 5],
                fcalc[:, 6],
                fcalc[:, 7],
                direction="FORWARD",
            )
            ix, iy = gt * (gtx, gty)
            ix = ix.astype(np.int32)
            iy = iy.astype(np.int32)

            oDict["emap_ref"][iy, ix] += fcalc[:, 0]
            oDict["emap_ref_count"][iy, ix] += 1

        if out["exportfacetsarray"]:
            mlon, mlat, melev = pyproj.transform(
                confDict["navigation"]["xyzsys"],
                confDict["navigation"]["llesys"],
                fcalc[:, 5],
                fcalc[:, 6],
                fcalc[:, 7],
            )
            fcalc[:, 5] = mlon
            fcalc[:, 6] = mlat
            fcalc[:, 7] = melev

            filename = confDict["paths"][
                "outpath"
            ] + "fcalc_{}.csv".format(i)
            print(
                "saving {}...................".format(
                    filename
                )
            )
            fcalc[:, 0] = 10 * np.log10(
                fcalc[:, 0] / np.max(fcalc[:, 0])
            )  # exporting facets in dB
            np.savetxt(
                confDict["paths"]["outpath"]
                + "fcalc_{}.csv".format(i),
                fcalc[:, [0, 1, 9, 10, 5, 6, 7]],
                delimiter=",",
                header="power,twtt,theta,phi,mx,my,mz",
                fmt="%.6e,%.6e,%.6f,%6f,%.6f,%.6f,%.6f",
                comments="",
            )
    return 0


def save(confDict, oDict, nav, dem, demData, demCrs, win):

    out = confDict["outputs"]
    frColor = [255, 0, 255]
    nColor = [50, 200, 200]

    if (
        out["shownadir"]
        or out["nadir"]
        or out["echomap"]
        or out["echomapadj"]
    ):
        # Find nadir lat/lon/elev and bin
        x = nav["x"].to_numpy()
        y = nav["y"].to_numpy()
        z = nav["z"].to_numpy()

        gx, gy, gz = pyproj.transform(
            confDict["navigation"]["xyzsys"],
            demCrs,
            x,
            y,
            z,
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
            ix[ix > (demData.shape[1] - 1)] = (
                demData.shape[1] - 1
            )
            iy[iy < 0] = 0
            iy[iy > (demData.shape[0] - 1)] = (
                demData.shape[0] - 1
            )
        else:
            nvalid[ix < 0] = 0
            nvalid[ix > (demData.shape[1] - 1)] = 0
            nvalid[iy < 0] = 0
            nvalid[iy > (demData.shape[0] - 1)] = 0

        demz[nvalid] = demData[iy[nvalid], ix[nvalid]]
        nvalid[demz == dem.nodata] = 0

        nx, ny, nz = pyproj.transform(
            demCrs,
            confDict["navigation"]["xyzsys"],
            gx,
            gy,
            demz,
        )

        ## CHECK THIS LINE              <------------------------------------------------------
        nlon, nlat, nelev = pyproj.transform(
            demCrs,
            confDict["navigation"]["llesys"],
            gx,
            gy,
            demz,
            # confDict["navigation"]["xyzsys"], "+proj=longlat +a=3396190 +b=3376200 +no_defs", nx, ny, nz # from pds
            # confDict["navigation"]["xyzsys"], "+proj=longlat +R=3396190 +no_defs", nx, ny, nz # from pds
        )

        nr = np.sqrt(
            (nx - x) ** 2 + (ny - y) ** 2 + (nz - z) ** 2
        )

        nbin = (
            (
                (
                    2
                    * nr
                    / confDict["simParams"]["speedlight"]
                )
                - nav["datum"].to_numpy()
            )
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
            (x - fret[:, 0]) ** 2
            + (y - fret[:, 1]) ** 2
            + (z - fret[:, 2]) ** 2
        )
        fbin = (
            (
                (
                    2
                    * fr
                    / confDict["simParams"]["speedlight"]
                )
                - nav["datum"].to_numpy()
            )
            / confDict["simParams"]["dt"]
        ).astype(np.int32)

        flon, flat, felev = pyproj.transform(
            # commenting out the following 2 lines that were working for CTX instead of the confDict
            # demCrs,
            # "+proj=longlat +R=3396190 +no_defs", #from pds
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
                confDict["paths"]["outpath"]
                + "firstReturn.csv",
                fretInfo,
                delimiter=",",
                header="lat,lon,elev_IAU2000,sample",
                fmt="%.6f,%.6f,%.3f,%d",
                comments="",
            )

    if out["exportfacetsarrayh5"]:
        slon, slat, selev = pyproj.transform(
            confDict["navigation"]["xyzsys"],
            confDict["navigation"]["llesys"],
            x,
            y,
            z,
        )
        with h5py.File(
            confDict["paths"]["outpath"] + "out.h5", "w"
        ) as hf:
            hf.create_dataset(
                "spacecraft_lat",
                data=slat,
                dtype=np.float32,
                compression="gzip",
            )
            hf.create_dataset(
                "spacecraft_lon",
                data=slon,
                dtype=np.float32,
                compression="gzip",
            )
            hf.create_dataset(
                "spacecraft_elev",
                data=selev,
                dtype=np.float32,
                compression="gzip",
            )
            hf.create_dataset(
                "facets_pwr",
                data=oDict["pwr"],
                dtype=np.float64,
                compression="gzip",
            )
            hf.create_dataset(
                "facets_twtt",
                data=oDict["twtt"],
                dtype=np.float64,
                compression="gzip",
            )
            hf.create_dataset(
                "facets_theta",
                data=oDict["theta"],
                dtype=np.float32,
                compression="gzip",
            )
            hf.create_dataset(
                "facets_phi",
                data=oDict["phi"],
                dtype=np.float32,
                compression="gzip",
            )
            hf.create_dataset(
                "facets_center_lat",
                data=oDict["mx"],
                dtype=np.float32,
                compression="gzip",
            )
            hf.create_dataset(
                "facets_center_lon",
                data=oDict["my"],
                dtype=np.float32,
                compression="gzip",
            )
            hf.create_dataset(
                "facets_center_elev",
                data=oDict["mz"],
                dtype=np.float32,
                compression="gzip",
            )

    if out["combined"] or out["binary"]:
        cgram = oDict["combined"] * (
            255.0 / oDict["combined"].max()
        )
        cstack = np.dstack((cgram, cgram, cgram)).astype(
            np.uint8
        )
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(
            confDict["paths"]["outpath"] + "combined.png"
        )

    if out["combinedadj"]:
        cgram = (
            oDict["combined"]
            * (255.0 / oDict["combined"].max())
        ).astype(np.uint8)
        """
        #The following lines are needed to align the clutter sim with the drone GPR first return
        #TODO: move this parameter to a config file
        for i in range(cgram.shape[1]):
            print(i)
            cgram[:, i] = np.roll(cgram[:,i], 35)
        """
        # Auto adjustment
        scaling = np.array(curve.curve)
        cgram = scaling[cgram] * 255
        cstack = np.dstack((cgram, cgram, cgram)).astype(
            "uint8"
        )

        # Add in first return and nadir locations if requested
        if out["showfret"]:
            frvalid = nvalid[:]
            frvalid[
                np.abs(fbin)
                >= confDict["simParams"]["tracesamples"]
            ] = 0
            for i in range(len(fbin)):
                b = fbin[i]
                if (
                    not np.isnan(b)
                    and abs(b)
                    < confDict["simParams"]["tracesamples"]
                ):
                    cstack[b, [i]] = frColor

        if out["shownadir"]:
            for i in range(len(nbin)):
                if (
                    nvalid[i]
                    and abs(b)
                    < confDict["simParams"]["tracesamples"]
                ):
                    cstack[nbin[i], [i]] = nColor

        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(
            confDict["paths"]["outpath"] + "combinedAdj.png"
        )

        if out["combinedcolored"]:
            cgram_center = cgram * np.bitwise_and(
                oDict["combined"] != 0,
                oDict["combined_sides"]
                == oDict["combined"],
            )
            cgram_center[cgram != cgram_center] = (
                cgram[cgram != cgram_center] * 0.4
            )
            cstack = np.dstack(
                (cgram_center, cgram, cgram_center)
            ).astype("uint8")

            cimg = Image.fromarray(cstack)
            cimg = cimg.convert("RGB")
            cimg.save(
                confDict["paths"]["outpath"]
                + "combinedColored.png"
            )

    if out["left"]:
        cgram = oDict["left"] * (
            255.0 / oDict["left"].max()
        )
        cstack = np.dstack((cgram, cgram, cgram)).astype(
            np.uint8
        )
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(confDict["paths"]["outpath"] + "left.png")

    if out["right"]:
        cgram = oDict["right"] * (
            255.0 / oDict["right"].max()
        )
        cstack = np.dstack((cgram, cgram, cgram)).astype(
            np.uint8
        )
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(
            confDict["paths"]["outpath"] + "right.png"
        )

    if out["binary"]:
        oDict["combined"].astype("float32").tofile(
            confDict["paths"]["outpath"] + "combined.img"
        )

    if out["echomap"]:
        egram = oDict["emap"] * (
            255.0 / oDict["emap"].max()
        )
        estack = np.dstack((egram, egram, egram)).astype(
            np.uint8
        )
        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(
            confDict["paths"]["outpath"] + "echomap.png"
        )

    if out["echomapgeoref"]:
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
            num = oDict["emap_ref"].astype(np.float32)
            den = oDict["emap_ref_count"].astype(np.float32)

            # Replace zeros with NaN to avoid division errors
            safe_den = np.where(den == 0, np.nan, den)
            ratio = num / safe_den

            # Take log10
            log_result = np.log10(ratio)

            # Replace nan/inf with something safe (0)
            log_result = np.nan_to_num(
                log_result, nan=0.0, posinf=0.0, neginf=0.0
            ).astype(np.float32)

            dst.write_band(1, log_result)

    if out["echomapadj"]:
        # Resize
        emap = oDict["emap"]
        emap_angles = oDict["emap_angles"]
        postSpace = np.sqrt(
            np.diff(nav["x"]) ** 2
            + np.diff(nav["y"]) ** 2
            + np.diff(nav["z"]) ** 2
        ).mean()
        ySquish = (
            confDict["facetParams"]["ctstep"] / postSpace
        )
        yDim = (
            np.floor(emap.shape[0] * ySquish).astype(
                np.int32
            )
            + 1
        )
        idx = np.arange(0, emap.shape[0])
        nidx = np.floor(idx * ySquish).astype(np.int32)
        egram = np.zeros((yDim, emap.shape[1]))
        ecount = np.zeros((yDim, emap.shape[1]))

        frmap = oDict["frmap"]
        frgram = np.zeros((yDim, frmap.shape[1]))

        egram = skimage.transform.resize(
            emap, (yDim, emap.shape[1])
        )
        egram_angles = skimage.transform.resize(
            emap_angles, (yDim, emap_angles.shape[1])
        )
        # Shrink emap and frmap
        for i in range(egram.shape[1]):
            frgram[:, i] = np.bincount(
                nidx, weights=frmap[:, i], minlength=yDim
            )

        nz = egram != 0
        hclip = 1.5
        egram[nz] = egram[nz] - (
            egram[nz].mean() - hclip * egram[nz].std()
        )
        egram = egram * (
            255.0
            / (egram[nz].mean() + hclip * egram[nz].std())
        )
        egram = np.minimum(egram, 255)
        egram = np.maximum(0, egram)

        estack = np.dstack((egram, egram, egram)).astype(
            np.uint8
        )
        for i in range(egram.shape[1]):
            fri = frgram[:, i] > 0
            estack[fri, i] = frColor
            estack[estack.shape[0] // 2, i] = nColor

        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(
            confDict["paths"]["outpath"] + "echomapAdj.png"
        )

        if out["echomapcolored"]:
            swathAngle = float(
                confDict["simParams"]["swathangle"]
            )
            shift = swathAngle / 2
            nColor = [0, 255, 0]
            facets_per_bin = (
                confDict["facetParams"]["atdist"]
                / confDict["facetParams"]["atstep"]
                * 4
            )
            egram_color1 = np.copy(egram)
            egram_color1[
                (
                    (
                        (egram_angles / facets_per_bin)
                        + shift
                    )
                    / swathAngle
                )
                % 2
                >= 1
            ] = (
                egram[
                    (
                        (
                            (egram_angles / facets_per_bin)
                            + shift
                        )
                        / swathAngle
                    )
                    % 2
                    >= 1
                ]
                * 0.7
            )
            egram_color2 = np.copy(egram)
            egram_color2[
                egram_angles < (shift * facets_per_bin)
            ] = (
                egram[
                    egram_angles < (shift * facets_per_bin)
                ]
                * 0.5
            )
            egram_color3 = egram * 0.7
            egram_color3[
                egram_angles < (shift * facets_per_bin)
            ] = (
                egram[
                    egram_angles < (shift * facets_per_bin)
                ]
                * 0.5
            )
            estack = np.dstack(
                (egram_color3, egram_color1, egram_color2)
            ).astype(np.uint8)

            for i in range(egram.shape[1]):
                fri = frgram[:, i] > 0
                estack[fri, i] = frColor
                for k in range(-1, 2):
                    estack[estack.shape[0] // 2 + k, i] = (
                        nColor
                    )

            eimg = Image.fromarray(estack)
            eimg = eimg.convert("RGB")
            eimg.save(
                confDict["paths"]["outpath"]
                + "echomapColored.png"
            )
