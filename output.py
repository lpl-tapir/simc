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

    cti = fcalc[:,8].astype(np.int32)
    lr = fcalc[:,2]
    pwr = fcalc[:,0]
    twttAdj = fcalc[:,1] - nav["datum"][i]
    cbin = (twttAdj/confDict["simParams"]["dt"]).astype(np.int32)

    cbin = np.mod(cbin, confDict["simParams"]["tracesamples"])

    # Make sure 

    if(out["combined"] or out["combinedadj"]):
        #np.add.at(oDict["combined"][:,i], cbin, pwr)
        oDict["combined"][:,i] = np.bincount(cbin, weights=pwr, minlength=3600)

    if(out["left"]):
        # Left facets are first half
        #np.add.at(oDict["left"][:,i], cbin[lr == 0], pwr[lr == 0])
        oDict["left"][:,i] = np.bincount(cbin[lr==0], weights=pwr[lr==0], minlength=3600)

    if(out["right"]):
        # Right facets are second half
        #np.add.at(oDict["right"][:,i], cbin[lr == 1], pwr[lr == 1])
        oDict["right"][:,i] = np.bincount(cbin[lr==1], weights=pwr[lr==1], minlength=3600)

    if(out["fret"] or out["showfret"]):
        ffacet = fcalc[twttAdj == twttAdj.min(),:]
        oDict["fret"][i,0:3] = ffacet[0,5:8]

    if(out["echomap"] or out["echomapadj"]):
        oDict["emap"][:,i] = np.bincount(cti, weights=pwr, minlength=oDict["emap"].shape[0])
        #np.add.at(oDict["emap"][:,i], cti, pwr)
        #plt.plot(cti[lr == 1])
        #plt.show()

    return 0


def save(confDict, oDict, nav, dem, demData):

    out = confDict["outputs"]

    if(out["shownadir"] or out["nadir"]):
        # Find nadir lat/lon/elev and bin
        x = nav["x"].to_numpy()
        y = nav["y"].to_numpy()
        z = nav["z"].to_numpy()

        gx, gy, gz = pyproj.transform(confDict["navigation"]["xyzsys"], dem.crs, x, y, z)

        gt = ~dem.transform
        ix, iy = gt * (gx, gy)
        ix = ix.astype(np.int32)
        iy = iy.astype(np.int32)

        # Bad mola pixel width patch
        ix[ix > dem.width-1] = dem.width-1
        
        # N-S off mola patch
        iy[iy < 0] = 0
        iy[iy > dem.height-1] = dem.height-1

        demz = demData[iy, ix]

        nx, ny, nz = pyproj.transform(dem.crs, confDict["navigation"]["xyzsys"], gx, gy, demz)
        nlat, nlon, nelev = pyproj.transform(dem.crs, confDict["navigation"]["llesys"], gx, gy, demz)

        nr = np.sqrt((nx-x)**2 + (ny-y)**2 + (nz-z)**2)
        nbin = (((2*nr/confDict["simParams"]["speedlight"]) - nav["datum"].to_numpy())/37.5e-9).astype(np.int32)
        
        if(out["nadir"]):
            nadInfo = np.zeros((nav.shape[0], 4))
            nadInfo[:,0] = nlat
            nadInfo[:,1] = nlon
            nadInfo[:,2] = nelev
            nadInfo[:,3] = nbin
            np.savetxt(confDict["paths"]["outpath"] + "nadir.csv", nadInfo,
                        delimiter=",", header="lat,lon,elev_IAU2000,sample",
                        comments="")

    if(out["showfret"] or out["fret"]):
        # Find fret lat/lon/elev and bin
        x = nav["x"].to_numpy()
        y = nav["y"].to_numpy()
        z = nav["z"].to_numpy()
        fret = oDict["fret"]

        fr = np.sqrt((x-fret[:,0])**2 + (y-fret[:,1])**2 + (z-fret[:,2])**2)
        fbin = (((2*fr/confDict["simParams"]["speedlight"]) - nav["datum"].to_numpy())/37.5e-9).astype(np.int32)

        flat, flon, felev = pyproj.transform(confDict["navigation"]["xyzsys"],
                                                confDict["navigation"]["llesys"],
                                                fret[:,0], fret[:,1], fret[:,2])
        if(out["fret"]):
            fretInfo = np.zeros((nav.shape[0], 4))
            fretInfo[:,0] = flat
            fretInfo[:,1] = flon
            fretInfo[:,2] = felev
            fretInfo[:,3] = fbin
            np.savetxt(confDict["paths"]["outpath"] + "firstReturn.csv", fretInfo,
                        delimiter=",", header="lat,lon,elev_IAU2000,sample",
                        comments="")

    if(out["combined"]):
        cgram = oDict["combined"]*(255.0/oDict["combined"].max())
        cstack = np.dstack((cgram,cgram,cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert('RGB')
        cimg.save(confDict["paths"]["outpath"] + "combined.png")

    if(out["combinedadj"]):
        cgram = (oDict["combined"]*(255.0/oDict["combined"].max())).astype(np.uint8)
        cshape = cgram.shape
        # Auto adjustment
        curve = np.fromfile("curve.txt", sep=' ')
        cgram = curve[cgram]*255
        cstack = np.dstack((cgram, cgram, cgram)).astype('uint8')

        # Add in first return and nadir locations if requested
        if(out["shownadir"]):
            for i in range(len(nbin)):
                cstack[nbin[i],[i]] = [50, 200, 200]

        if(out["showfret"]):
            for i in range(len(fbin)):
                cstack[fbin[i],[i]] = [255, 0, 255]

        cimg = Image.fromarray(cstack)
        cimg = cimg.convert('RGB')
        cimg.save(confDict["paths"]["outpath"] + "combinedAdj.png")

    if(out["left"]):
        cgram = oDict["left"]*(255.0/oDict["left"].max())
        cstack = np.dstack((cgram,cgram,cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert('RGB')
        cimg.save(confDict["paths"]["outpath"] + "left.png")

    if(out["right"]):
        cgram = oDict["right"]*(255.0/oDict["right"].max())
        cstack = np.dstack((cgram,cgram,cgram)).astype(np.uint8)
        cimg = Image.fromarray(cstack)
        cimg = cimg.convert('RGB')
        cimg.save(confDict["paths"]["outpath"] + "right.png")

    if(out["binary"]):
        oDict["combined"].astype('float32').tofile(confDict['paths']['outpath'] + 'combined.img')

    if(out["echomap"]):
        egram = oDict["emap"]*(255.0/oDict["emap"].max())
        estack = np.dstack((egram,egram,egram)).astype(np.uint8)
        eimg = Image.fromarray(estack)
        eimg = eimg.convert('RGB')
        eimg.save(confDict["paths"]["outpath"] + "echomap.png")

    if(out["echomapadj"]):
        emap = oDict["emap"]
        postSpace = np.sqrt(np.diff(nav["x"])**2 + np.diff(nav["y"])**2 + np.diff(nav["z"])**2).mean()
        ySquish = confDict['facetParams']['ctstep']/postSpace
        emap[emap != 0] = emap[emap != 0] - (emap[emap != 0].mean()-emap[emap != 0].std())
        emap = emap*(255.0/(emap[emap != 0].mean()+emap[emap != 0].std()))
        emap = np.minimum(emap, 255)
        emap = np.maximum(0, emap)
        yDim = int(emap.shape[0]*ySquish)
        nemap = skimage.transform.resize(emap, (yDim, len(nav)))
        egram = nemap
        estack = np.dstack((egram,egram,egram)).astype(np.uint8)
        eimg = Image.fromarray(estack)
        eimg = eimg.convert('RGB')
        eimg.save(confDict["paths"]["outpath"] + "echomapAdj.png")