import numpy as np
import pyproj
import rasterio as rio

def sim(confDict, dem, nav, xform, demData, i):
    atStep = confDict["facetParams"]["atstep"]
    ctStep = confDict["facetParams"]["ctstep"]
    atNum = confDict["facetParams"]["atdist"]//atStep
    ctNum = confDict["facetParams"]["ctdist"]//ctStep

    # Generate grid in xyz space
    gx,gy,gz = genGrid(nav, ctNum, atNum, atStep, ctStep, i)

    # Transform to dem CRS and sample DEM
    gtx, gty, gtz = xform.transform(gx, gy, gz, direction='FORWARD')
    gt = ~dem.transform
    ix, iy = gt * (gtx, gty)
    ix = ix.astype(np.int32)
    iy = iy.astype(np.int32)
    #iy, ix = dem.index(gtx, gty)
    #ix = np.array(ix)
    #iy = np.array(iy)
    #print(ix, iy)
    #sys.exit()

    # Bad mola pixel width patch
    ix[ix > dem.width-1] = dem.width-1
    
    # N-S off mola patch
    iy[iy < 0] = 0
    iy[iy > dem.height-1] = dem.height-1

    demz = demData[iy, ix]

    # Transform back to xyz for facet calcs
    sx, sy, sz = xform.transform(gtx, gty, demz, direction='INVERSE')

    sx = np.reshape(sx, (2*int(atNum)+1, 2*int(ctNum)+1))
    sy = np.reshape(sy, (2*int(atNum)+1, 2*int(ctNum)+1))
    sz = np.reshape(sz, (2*int(atNum)+1, 2*int(ctNum)+1))

    #print(sx.shape)
    #print(sy)
    #print(sz)
    #sys.exit()

    surface = np.stack((sx, sy, sz), axis=0)

    #print(surface.shape)
    #print(surface)
    #sys.exit()

    facets = genFacets(surface)
    fcalc = calcFacets(facets, nav["x"][i], nav["y"][i], nav["z"][i],
                            confDict["simParams"]["speedlight"])

    return fcalc

def calcFacets(f, px, py, pz, c):
    fcalc = np.zeros((f.shape[0], 9))

    # Calc midpoints
    mx = (f[:,0] + f[:,3] + f[:,6])/3
    my = (f[:,1] + f[:,4] + f[:,7])/3
    mz = (f[:,2] + f[:,5] + f[:,8])/3
    
    # Calc distances to platform/twtt
    rx = px - mx
    ry = py - my
    rz = pz - mz
    #print("mx", mx)
    #print("my", my)
    #print("mz", mz)

    r = np.sqrt(rx**2 + ry**2 + rz**2)

    ## Calc area and normal vector
    # Calc 2->1 vector
    f[:,3] = f[:,0] - f[:,3] #x
    f[:,4] = f[:,1] - f[:,4] #y
    f[:,5] = f[:,2] - f[:,5] #z
    # Calc 1->3 vector
    f[:,0] = f[:,6] - f[:,0] #x
    f[:,1] = f[:,7] - f[:,1] #y
    f[:,2] = f[:,8] - f[:,2] #z
    # Calc cross product
    f[:,6:9] = np.cross(f[:,3:6], f[:,0:3])
    area = np.sqrt(f[:,6]**2 + f[:,7]**2 + f[:,8]**2)/2

    ## Calc power
    # Dot product between facet center -> platform and normal to facet
    ct = ((rx * f[:,6]) + (ry * f[:,7]) + (rz * f[:,8]))
    ct = ct/(r*area*2)

    fcalc[:,0] = np.abs(((area*ct)**2)/(r**4)) #power
    fcalc[:,1] = 2*r/c #twtt
    fcalc[:,2] = f[:,10] # right or left
    fcalc[:,4] = 1 # use all facets for now
    fcalc[:,5] = mx # Facet centers
    fcalc[:,6] = my
    fcalc[:,7] = mz
    fcalc[:,8] = f[:,11] # Cross track indices for echo power map

    return fcalc

def genFacets(s):
    # Generate list of facets (f) from surface grid (s)
    h = s.shape[1]
    w = s.shape[2]
    nfacet = (w-1)*(h-1)*2
    qt = int(nfacet/4)
    hf = int(nfacet/2)
    tq = hf+qt
    f = np.zeros((nfacet,12))

    # Ordering of points along axis 1 is important for cross product later
    # Ordering of points along axis 0 is important for left/right side
 
    ## Left Side Facets First   
    # Group 1 upper left xyz
    f[0:qt, 0] = s[0,0:h-1,0:(w-1)//2].flatten()
    f[0:qt, 1] = s[1,0:h-1,0:(w-1)//2].flatten()
    f[0:qt, 2] = s[2,0:h-1,0:(w-1)//2].flatten()

    # Group 1 upper right xyz
    f[0:qt, 3] = s[0,0:h-1,1:(w+1)//2].flatten()
    f[0:qt, 4] = s[1,0:h-1,1:(w+1)//2].flatten()
    f[0:qt, 5] = s[2,0:h-1,1:(w+1)//2].flatten()

    # Group 1 lower left xyz
    f[0:qt, 6] = s[0,1:h,0:(w-1)//2].flatten()
    f[0:qt, 7] = s[1,1:h,0:(w-1)//2].flatten()
    f[0:qt, 8] = s[2,1:h,0:(w-1)//2].flatten()

    # Group 2 lower right xyz
    f[qt:hf, 0] = s[0,1:h,1:(w+1)//2].flatten()
    f[qt:hf, 1] = s[1,1:h,1:(w+1)//2].flatten()
    f[qt:hf, 2] = s[2,1:h,1:(w+1)//2].flatten()

    # Group 2 lower left xyz
    f[qt:hf, 3] = s[0,1:h,0:(w-1)//2].flatten()
    f[qt:hf, 4] = s[1,1:h,0:(w-1)//2].flatten()
    f[qt:hf, 5] = s[2,1:h,0:(w-1)//2].flatten()

    # Group 2 upper right xyz
    f[qt:hf, 6] = s[0,0:h-1,1:(w+1)//2].flatten()
    f[qt:hf, 7] = s[1,0:h-1,1:(w+1)//2].flatten()
    f[qt:hf, 8] = s[2,0:h-1,1:(w+1)//2].flatten()

    ## Then right side facets
    # Group 1 upper left xyz
    f[hf:tq, 0] = s[0,0:h-1,(w-1)//2:w-1].flatten()
    f[hf:tq, 1] = s[1,0:h-1,(w-1)//2:w-1].flatten()
    f[hf:tq, 2] = s[2,0:h-1,(w-1)//2:w-1].flatten()

    # Group 1 upper right xyz
    f[hf:tq, 3] = s[0,0:h-1,(w+1)//2:w].flatten()
    f[hf:tq, 4] = s[1,0:h-1,(w+1)//2:w].flatten()
    f[hf:tq, 5] = s[2,0:h-1,(w+1)//2:w].flatten()

    # Group 1 lower left xyz
    f[hf:tq, 6] = s[0,1:h,(w-1)//2:w-1].flatten()
    f[hf:tq, 7] = s[1,1:h,(w-1)//2:w-1].flatten()
    f[hf:tq, 8] = s[2,1:h,(w-1)//2:w-1].flatten()

    # Group 2 lower right xyz
    f[tq:nfacet, 0] = s[0,1:h,(w+1)//2:w].flatten()
    f[tq:nfacet, 1] = s[1,1:h,(w+1)//2:w].flatten()
    f[tq:nfacet, 2] = s[2,1:h,(w+1)//2:w].flatten()
    
    # Group 2 lower left xyz
    f[tq:nfacet, 3] = s[0,1:h,(w-1)//2:w-1].flatten()
    f[tq:nfacet, 4] = s[1,1:h,(w-1)//2:w-1].flatten()
    f[tq:nfacet, 5] = s[2,1:h,(w-1)//2:w-1].flatten()

    # Group 2 upper right xyz
    f[tq:nfacet, 6] = s[0,0:h-1,(w+1)//2:w].flatten()
    f[tq:nfacet, 7] = s[1,0:h-1,(w+1)//2:w].flatten()
    f[tq:nfacet, 8] = s[2,0:h-1,(w+1)//2:w].flatten()

    # Add in lr entry - l=0, r=1
    f[0:hf,10] = 0
    f[hf:nfacet,10] = 1

    # Add in cross track indices for echo power map
    hm0 = np.arange(0,h-1)
    wm0 = np.arange(0,(w-1)//2)
    wm0, hm0 = np.meshgrid(wm0, hm0)
    f[0:qt, 11] = wm0.flatten()
    f[qt:hf, 11] = wm0.flatten()

    hm1 = np.arange(0,h-1)
    wm1 = np.arange((w-1)//2, w-1)
    wm1, hm1 = np.meshgrid(wm1, hm1)
    f[hf:tq, 11] = wm1.flatten()
    f[tq:nfacet, 11] = wm1.flatten()


    return f


def genGrid(nav, ctNum, atNum, atStep, ctStep, i):
    # Generate XYZ grid
    ua = nav["uv"][i]*atStep # along track vector (forward)
    uc = nav["ul"][i]*ctStep # cross track vector (right)
    
    # Use meshgrid to come up with vectors to grid points
    ati = np.arange(atNum, -atNum-1, -1)
    cti = np.arange(-ctNum, ctNum+1)
    mgrd = np.meshgrid(cti, ati)

    dATx = mgrd[1]*ua[0]
    dATy = mgrd[1]*ua[1]
    dATz = mgrd[1]*ua[2]

    dCTx = mgrd[0]*uc[0]
    dCTy = mgrd[0]*uc[1]
    dCTz = mgrd[0]*uc[2]

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