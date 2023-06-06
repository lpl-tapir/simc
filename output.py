import numpy as np
import sys
from PIL import Image
import pyproj
import matplotlib.pyplot as plt
import skimage.transform
import curve
import h5py


def build(confDict, oDict, fcalc, nav, i, oi):
    # bincount requires assumptions - all positive integers, nothing greater than tracelen. Need to make sure these are met
    out = confDict["outputs"]
    spt = confDict["simParams"]["tracesamples"]

    cti = fcalc[:, 8].astype(np.int32)
    lr = fcalc[:, 2]
    pwr = fcalc[:, 0]
    twtt = fcalc[:, 1]
    twttAdj = twtt - nav["datum"][i]
    cbin = (twttAdj / confDict["simParams"]["dt"]).astype(np.int32)
    cbin_copy = (twttAdj / confDict["simParams"]["dt"]).astype(np.int32)
  
    cbin = np.mod(cbin, confDict["simParams"]["tracesamples"])

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
                cti, weights=pwr * (twtt ** 4), minlength=oDict["emap"].shape[0]
            )
            frFacets = cti[cbin_copy == cbin_copy.min()]
            #ffacet = fcalc[pwr > (pwr.max() - ((pwr.max() - pwr.min()) / 2)) , :]
            #ifrFacets = cti[cbin == cbin.min()]
            oDict["frmap"][frFacets, j] = 1

        oDict["pwr"][j,:] = fcalc[:,0]
        oDict["twtt"][j,:] = fcalc[:,1]
        oDict["theta"][j, :] = fcalc[:,9]
        oDict["phi"][j,:] = fcalc[:,10]
    
        mlon, mlat, melev = pyproj.transform(
            confDict["navigation"]["xyzsys"],
            confDict["navigation"]["llesys"],
            fcalc[:,5],
            fcalc[:,6],
            fcalc[:,7],
        
        )
        print(mlat)
        print(mlon)
        print(melev)
        oDict["mx"][j,:] = mlat
        oDict["my"][j, :] = mlon
        oDict["mz"][j,:] = melev
        ''' 
        filename = confDict["paths"]["outpath"] + "fcalc_{}.csv".format(i)
        print("saving {}...................".format(filename))
        
        np.savetxt(
            confDict["paths"]["outpath"] + "fcalc_{}.csv".format(i),
            fcalc[:,[0,1,9,10]],
            #fcalc[:,[0,1,2,8,9,10]],
            delimiter=",",
            header="power,twtt,theta,phi",
            fmt="%.6e,%.6e,%.6f,%.6f",
            comments="",
        )
        '''
    
    return 0


def save(confDict, oDict, nav, dem, demData, win):

    out = confDict["outputs"]
    frColor = [255, 0, 255]
    nColor = [50, 200, 200]

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
        nlon, nlat, nelev = pyproj.transform(
            dem.crs, confDict["navigation"]["llesys"], gx, gy, demz
        )

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

        flon, flat, felev = pyproj.transform(
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
                fmt="%.6f,%.6f,%.3f,%d",
                comments="",
            )
    slon, slat, selev = pyproj.transform(
        confDict["navigation"]["xyzsys"],
        confDict["navigation"]["llesys"],
        x,            
        y,
        z,
    )
    print(slat[0])
    print(slon[0])
    print(selev[0])
    print(oDict["pwr"][0])
    print(oDict["twtt"][0])
    print(oDict["theta"][0])
    print(oDict["phi"][0])
    print(oDict["mx"][0])
    print(oDict["my"][0])
    print(oDict["mz"][0])
    with h5py.File( confDict["paths"]["outpath"] + "out.h5", 'w' ) as hf:
        hf.create_dataset("spacecraft_lat", data=slat, dtype=np.float32, compression="gzip")
        hf.create_dataset("spacecraft_lon", data=slon, dtype=np.float32, compression="gzip")
        hf.create_dataset("spacecraft_elev", data=selev, dtype=np.float32, compression="gzip")
        hf.create_dataset("facets_pwr", data=oDict["pwr"], dtype=np.float64, compression="gzip")
        hf.create_dataset("facets_twtt", data=oDict["twtt"], dtype=np.float64, compression="gzip")
        hf.create_dataset("facets_theta", data=oDict["theta"], dtype=np.float32, compression="gzip")
        hf.create_dataset("facets_phi", data=oDict["phi"], dtype=np.float32, compression="gzip")
        hf.create_dataset("facets_center_lat", data=oDict["mx"], dtype=np.float32, compression="gzip")
        hf.create_dataset("facets_center_lon", data=oDict["my"], dtype=np.float32, compression="gzip")
        hf.create_dataset("facets_center_elev", data=oDict["mz"], dtype=np.float32, compression="gzip")

    if out["combined"] or out["binary"]:
        cgram = oDict["combined"] * (255.0 / oDict["combined"].max())
        cstack = np.dstack((cgram, cgram, cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert("RGB")
        cimg.save(confDict["paths"]["outpath"] + "combined.png")

    if out["combinedadj"]:
        cgram = (oDict["combined"] * (255.0 / oDict["combined"].max())).astype(np.uint8)
        # Auto adjustment
        scaling = np.array(curve.curve)
        cgram = scaling[cgram] * 255
        cstack = np.dstack((cgram, cgram, cgram)).astype("uint8")

        # Add in first return and nadir locations if requested
        if out["showfret"]:
            frvalid = nvalid[:]
            frvalid[np.abs(fbin) >= confDict["simParams"]["tracesamples"]] = 0
            for i in range(len(fbin)):
                b = fbin[i]
                if not np.isnan(b) and abs(b) < confDict["simParams"]["tracesamples"] :
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
        egram = oDict["emap"] * (255.0 / oDict["emap"].max())
        estack = np.dstack((egram, egram, egram)).astype(np.uint8)
        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(confDict["paths"]["outpath"] + "echomap.png")

    if out["echomapadj"]:
        # Resize
        emap = oDict["emap"]
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
