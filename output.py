import numpy as np
import sys, os
from PIL import Image
import pyproj
import matplotlib.pyplot as plt
import skimage.transform
import curve
import datetime
import hashlib

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
  
    cbin = np.mod(cbin, confDict["simParams"]["tracesamples"])

    for j in oi:
        oDict["combined"][:, j] = np.bincount(
            cbin, weights=pwr, minlength=confDict["simParams"]["tracesamples"]
        )

        oDict["left"][:, j] = np.bincount(
            cbin[lr == 0],
            weights=pwr[lr == 0],
            minlength=confDict["simParams"]["tracesamples"],
        )

        oDict["right"][:, j] = np.bincount(
            cbin[lr == 1],
            weights=pwr[lr == 1],
            minlength=confDict["simParams"]["tracesamples"],
        )

        ffacet = fcalc[twttAdj == twttAdj.min(), :]
        oDict["fret"][j, 0:3] = ffacet[0, 5:8]

        oDict["emap"][:, j] = np.bincount(
            cti, weights=pwr * (twtt ** 4), minlength=oDict["emap"].shape[0]
        )
        frFacets = cti[cbin == cbin.min()]
        oDict["frmap"][frFacets, j] = 1

    return 0



def genLabels(confDict):
    ## Open and read PDS3 radargram label, make dict
    fd = open(confDict["paths"]["lblpath"], 'r')
    lbl = fd.read()
    fd.close()
    lbl = lbl.split("\n")
    ld = {}
    for line in lbl:
        if(line == '' or line == 'END'):
            continue
        elif(line[0] == '/' and line[1] == '*'):
            continue
        else:
            line = line.split('=')
            ld[line[0].strip()] = line[1].strip()

    sim_nameU = ld["PRODUCT_ID"].replace('"','').strip("_RGRAM")
    sim_nameL = sim_nameU.lower()
    num_trace = ld["LINE_SAMPLES"]
    num_tracet4 = str(int(num_trace)*4)
    num_tracet3600p9 = str((int(num_trace)*3600)+9)
    num_tracet179p9 = str((int(num_trace)*179)+9)
    num_tracet3600t4 = str(int(num_trace)*3600*4)
    start_lat = ld["MRO:START_SUB_SPACECRAFT_LATITUDE"].strip(" <DEGREE>")
    stop_lat = ld["MRO:STOP_SUB_SPACECRAFT_LATITUDE"].strip(" <DEGREE>")
    start_lon = ld["MRO:START_SUB_SPACECRAFT_LONGITUDE"].strip(" <DEGREE>")
    stop_lon = ld["MRO:STOP_SUB_SPACECRAFT_LONGITUDE"].strip(" <DEGREE>")
    start_datetime = ld["START_TIME"]
    stop_datetime = ld["STOP_TIME"]
    orbit_num = ld["ORBIT_NUMBER"]

    # Approx label creation time
    utc = datetime.datetime.utcnow()
    sim_time_utc = utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[0:-3]

    # File sizes and md5 checksums of all outputs
    od = {"CTIFF" : "browse_combined.tif",
          "LTIFF" : "browse_left.tif",
          "RTIFF" : "browse_right.tif",
          "ETIFF" : "browse_emap.tif",
          "LRBIN" : "sim_lr.img",
          "EBIN" : "sim_emap.img",
          "FNCSV" : "rtrn.csv"}

    sd = {}

    for key in od:
        fname = confDict["paths"]["outpath"] + od[key]
        sd['['+key+"_SIZE]"] = str(os.path.getsize(fname))
        sd['['+key+"_MD5]"] = hashlib.md5(open(fname,'rb').read()).hexdigest()

    # Template replacement dictionary
    rd = {"[SIM_NAME3]" : sim_nameU,
          "[SIM_NAME4]" : sim_nameL,
          "[NUM_TRACE]" : num_trace,
          "[NUM_TRACE*4]" : num_tracet4,
          "[NUM_TRACE*3600+9]" : num_tracet3600p9,
          "[NUM_TRACE*179+9]" : num_tracet179p9,
          "[NUM_TRACE*3600*4]" : num_tracet3600t4,
          "[START_LAT]" : start_lat,
          "[STOP_LAT]" : stop_lat,
          "[START_LON]" : start_lon,
          "[STOP_LON]" : stop_lon,
          "[START_DATETIME]" : start_datetime,
          "[STOP_DATETIME]" : stop_datetime,
          "[ORBIT_NUM]" : orbit_num,
          "[SIM_TIME_UTC]" : sim_time_utc}

    rd.update(sd)

    ## Generate PDS3 labels
    for lbltype in ["sim", "emap", "rtrn", "browse"]:
        fd = open(confDict["paths"]["tmplpath"] + "/" + lbltype + ".lbl", 'r')
        tmpl = fd.read()
        fd.close()
        for key in rd:
            tmpl = tmpl.replace(key, rd[key])

        tmpl = tmpl.replace("\n","\r\n") # Replace any linux newlines with DOS
        fd = open(confDict["paths"]["outpath"] + lbltype + ".lbl", 'w')
        fd.write(tmpl)
        fd.close()

    ## Generate PDS4 sim labels
    for lbltype in ["sim", "rtrn", "browse"]:
        fd = open(confDict["paths"]["tmplpath"] + "/" + lbltype + ".xml", 'r')
        tmpl = fd.read()
        fd.close()
        for key in rd:
            tmpl = tmpl.replace(key, rd[key])

        fd = open(confDict["paths"]["outpath"] + lbltype + ".xml", 'w')
        fd.write(tmpl)
        fd.close()


    return 0

def save(confDict, oDict, nav, dem, demData, win):

    out = confDict["outputs"]
    frColor = [255, 0, 255]
    nColor = [50, 200, 200]

    ## Binary L/R sim products
    lrstack = np.dstack((oDict["left"], oDict["right"]))
    lrstack[np.isnan(lrstack)] = 0
    lrstack.astype("float32").tofile(
        confDict["paths"]["outpath"] + "sim_lr.img"
    )

    ## Nadir and first return information
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

    # Nadir csv
    nfInfo = np.zeros((nav.shape[0], 9)) # Combined table
    nfInfo[:, 0] = np.arange(1, nav.shape[0]+1, 1)
    nfInfo[:, 1] = nlat
    nfInfo[:, 2] = nlon
    nfInfo[:, 3] = nelev
    nfInfo[:, 4] = nbin

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

    # First return CSV
    nfInfo[:, 5] = flat
    nfInfo[:, 6] = flon
    nfInfo[:, 7] = felev
    nfInfo[:, 8] = fbin

    nadhead = "NadirLat,NadirLon,NadirElev,NadirSamp"
    frhead = "FirstLat,FirstLon,FirstElev,FirstSamp"
    np.savetxt(
        confDict["paths"]["outpath"] + "rtrn.csv",
        nfInfo,
        delimiter=",",
        newline="\r\n",
        header="Column,"+nadhead+","+frhead,
        fmt="%d,%.6f,%.6f,%.3f,%d,%.6f,%.6f,%.3f,%d",
        comments="",
    )

    ## Auto adjusted combined and L/R browse producs
    # Combined
    cgram = (oDict["combined"] * (255.0 / oDict["combined"].max())).astype(np.uint8)
    # Auto adjustment
    scaling = np.array(curve.curve)
    cgram = scaling[cgram] * 255
    #cstack = np.dstack((cgram, cgram, cgram)).astype("uint8")
    cstack = cgram.astype("uint8")
    # Add in first return and nadir locations if requested
    """
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
    """
    cimg = Image.fromarray(cstack)
    #cimg = cimg.convert("RGB")
    cimg.save(confDict["paths"]["outpath"] + "browse_combined.tif")

    # Left
    cgram = (oDict["left"] * (255.0 / oDict["left"].max())).astype(np.uint8)
    scaling = np.array(curve.curve)
    cgram = scaling[cgram] * 255    
    #cstack = np.dstack((cgram, cgram, cgram)).astype(np.uint8)
    cstack = cgram.astype("uint8")
    cimg = Image.fromarray(cstack)
    #cimg = cimg.convert("RGB")
    cimg.save(confDict["paths"]["outpath"] + "browse_left.tif")

    # Right
    cgram = (oDict["right"] * (255.0 / oDict["right"].max())).astype(np.uint8)
    scaling = np.array(curve.curve)
    cgram = scaling[cgram] * 255
    #cstack = np.dstack((cgram, cgram, cgram)).astype(np.uint8)
    cstack = cgram.astype("uint8")
    cimg = Image.fromarray(cstack)
    #cimg = cimg.convert("RGB")
    cimg.save(confDict["paths"]["outpath"] + "browse_right.tif")


    ## Browse echo power map
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

    if(egram.shape != (179,oDict["right"].shape[1])):
        print("BAD EMAP DIMENSION", emap.shape)
        
    ## Binary echo power map
    egram.astype("float32").tofile(
        confDict["paths"]["outpath"] + "sim_emap.img"
    )

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
    eimg.save(confDict["paths"]["outpath"] + "browse_emap.tif")

    # Generate labels
    genLabels(confDict)

    return 0
