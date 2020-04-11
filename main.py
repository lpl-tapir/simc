import sys
import ingest, prep, sim, output
import rasterio as rio
import numpy as np
import pprint
import pyproj

def main():
    argDict = ingest.parseCmd()
    confDict = ingest.readConfig(argDict)
    dem = rio.open(confDict["paths"]["dempath"], mode='r')
    nav = ingest.readNav(confDict["paths"]["navpath"], 
                            confDict["navigation"]["navsys"], 
                            confDict["navigation"]["xyzsys"],
                            confDict["navigation"]["navfunc"])
    
    xform = pyproj.transformer.Transformer.from_crs(confDict["navigation"]["xyzsys"], dem.crs)
    nav, oDict = prep.prep(confDict, dem, nav)
    #pprint.pprint(confDict)

    demData = dem.read(1)
    for i in range(nav.shape[0]):
        fcalc = sim.sim(confDict, dem, nav, xform, demData, i)
        output.build(confDict, oDict, fcalc, nav, i)

    output.save(confDict, oDict, nav, dem, demData)
    dem.close()

# execute only if run as a script.
if __name__ == '__main__':
    main()