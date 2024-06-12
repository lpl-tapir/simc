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
    theta = fcalc[:,9]
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
            oDict["emap_angles"][:, j] = np.bincount(
                cti, weights=theta, minlength=oDict["emap"].shape[0]
            )
            frFacets = cti[cbin_copy == cbin_copy.min()] #comparison of floats
            #ffacet = fcalc[pwr > (pwr.max() - ((pwr.max() - pwr.min()) / 2)) , :]
            #frFacets = cti[cbin == cbin.min()] #comparison of integers
            oDict["frmap"][frFacets, j] = 1

        if out["exportfacetsarray"]:
            mlon, mlat, melev = pyproj.transform(
                confDict["navigation"]["xyzsys"],
                confDict["navigation"]["llesys"],
                fcalc[:,5],
                fcalc[:,6],
                fcalc[:,7],
        
            )
            fcalc[:,5] =  mlon
            fcalc[:,6] =  mlat
            fcalc[:,7] =  melev

            filename = confDict["paths"]["outpath"] + "fcalc_{}.csv".format(i)
            print("saving {}...................".format(filename))
            np.savetxt(
                confDict["paths"]["outpath"] + "fcalc_{}.csv".format(i),
                #fcalc[np.where(fcalc[:,0] != sys.float_info.min)[0],[0,1,9,10,5,6,7]], # TODO: export only values part of the antenna model
                fcalc[:,[0,1,9,10,5,6,7]],
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

    if out["shownadir"] or out["nadir"] or out["echomap"] or out["echomapadj"]:
        # Find nadir lat/lon/elev and bin
        x = nav["x"].to_numpy()
        y = nav["y"].to_numpy()
        z = nav["z"].to_numpy()

        gx, gy, gz = pyproj.transform(
            confDict["navigation"]["xyzsys"], demCrs, x, y, z
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
            demCrs, confDict["navigation"]["xyzsys"], gx, gy, demz
        )

        ## CHECK THIS LINE              <------------------------------------------------------
        nlon, nlat, nelev = pyproj.transform(
            demCrs, confDict["navigation"]["llesys"], gx, gy, demz
            #confDict["navigation"]["xyzsys"], demCrs, nx, ny, demz # from pds
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
            #commenting out this lines that were working for CTX
            #demCrs,
            #"+proj=longlat +R=3396190 +no_defs", #from pds
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

    if out["exportfacetsarrayh5"]:
        slon, slat, selev = pyproj.transform(
            confDict["navigation"]["xyzsys"],
            confDict["navigation"]["llesys"],
            x,
            y,
            z,
            )
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

        #The following lines are needed to align the clutter sim with the drone GPR first return
        #TODO: move this parameter to a config file
        '''
        for i in range(cgram.shape[1]):
            print(i)
            cgram[:, i] = np.roll(cgram[:,i], 35)
        '''
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
        egram_color = np.copy(egram)

        estack = np.dstack((egram, egram, egram)).astype(np.uint8)
        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(confDict["paths"]["outpath"] + "echomap.png")

    if out["echomapadj"]:
        # Resize
        emap = oDict["emap"]
        emap_angles = oDict["emap_angles"]
        postSpace = np.sqrt(
            np.diff(nav["x"]) ** 2 + np.diff(nav["y"]) ** 2 + np.diff(nav["z"]) ** 2
        ).mean()
        ySquish = confDict["facetParams"]["ctstep"] / postSpace
        yDim = np.floor(emap.shape[0] * ySquish).astype(np.int32) + 1
        print(yDim)
        idx = np.arange(0, emap.shape[0])
        nidx = np.floor(idx * ySquish).astype(np.int32)
        egram = np.zeros((yDim, emap.shape[1]))
        ecount = np.zeros((yDim, emap.shape[1]))

        frmap = oDict["frmap"]
        frgram = np.zeros((yDim, frmap.shape[1]))

        egram = skimage.transform.resize(emap, (yDim, emap.shape[1]))
        egram_angles = skimage.transform.resize(emap_angles, (yDim, emap_angles.shape[1]))
        # Shrink emap and frmap
        for i in range(egram.shape[1]):
            frgram[:, i] = np.bincount(nidx, weights=frmap[:, i], minlength=yDim)

        #The following to lines are needed to handle the values outside the dipole pattern of the drone GPR
        egram[egram == 0] = np.nan
        nz = egram != 0
        hclip = 1.5
        #egram[nz] = egram[nz] - (egram[nz].mean() - hclip * egram[nz].std())
        #egram = egram * (255.0 / (egram[nz].mean() + hclip * egram[nz].std()))
        #The following to lines are needed to handle the values outside the dipole pattern of the drone GPR
        egram[nz] = egram[nz] - (np.nanmean(egram[nz]) - hclip * np.nanstd(egram[nz]))
        egram = egram * (255.0 / (np.nanmean(egram[nz]) + hclip * np.nanstd(egram[nz])))
        egram = np.minimum(egram, 255)
        egram = np.maximum(0, egram)

        estack = np.dstack((egram, egram, egram)).astype(np.uint8)
        
        '''
        egram_color1 = np.copy(egram)
        egram_color2 = np.copy(egram)
        egram_color3 = np.copy(egram)
        print(egram.shape)
        print(egram_angles.shape)
        x = (egram_angles / 3) % 2 < 1 
        print(x.shape)
        print(egram_angles)
        angle = 5
        shift = 2.5
        egram_color1[(((egram_angles / 12) + shift)  / angle) % 2 < 1] = egram[(((egram_angles / 12) + shift)  / angle) % 2 < 1] * 0.7
        #egram_color2[(((egram_angles / 12) + shift)  / angle) % 2 >= 1] = egram[(((egram_angles / 12) + shift)  / angle) % 2 >= 1] * 0.7
        egram_color3 = egram  * 0.7#[(((egram_angles / 12) + shift)  / angle) % 2 >= 1] = egram[(((egram_angles / 12) + shift)  / angle) % 2 >= 1] * 0.6
        estack = np.dstack((egram_color3, egram_color1, egram_color2)).astype(np.uint8)
        estack = np.dstack((egram, egram, egram)).astype(np.uint8)
        '''
        
        for i in range(egram.shape[1]):
            fri = frgram[:, i] > 0
            estack[fri, i] = frColor
            estack[estack.shape[0] // 2, i] = nColor


        eimg = Image.fromarray(estack)
        eimg = eimg.convert("RGB")
        eimg.save(confDict["paths"]["outpath"] + "echomapAdj.png")
