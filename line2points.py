import shapely.geometry
import fiona
import sys
import pyproj
import rasterio as rio
import numpy as np
import matplotlib.pyplot as plt

def rollmean(x, n):
	lenx = len(x)
	pre = np.ones(n)*x[0]
	post = np.ones(n)*x[-1]
	x = np.append(pre, x)
	x = np.append(x, post)
	xs = np.convolve(x, np.ones(n)/n, 'same')
	return xs[n:n+lenx]


demPath = "/home/mchristo/proj/akOIB/akmap/basemap/Alaska_albers_V2.tif"
shpPath = "./malaspina.gpkg"
step = 20

dem = rio.open(demPath, "r")
shp = fiona.open(shpPath)

for line in shp:
	name = line["properties"]['name']
	alt = line["properties"]["alt"]
	xords = line["geometry"]["coordinates"][0]
	shpx, shpy = zip(*xords)
	
	# Sample DEM at shapefile points for general shape
	shpx = np.array(shpx)
	shpy = np.array(shpy)
	xform = pyproj.Transformer.from_crs(shp.crs, dem.crs)
	demX, demY = xform.transform(shpx, shpy)

	points = zip(demX, demY)

	zvals = list(rio.sample.sample_gen(dem, points))

	demZ = np.zeros(len(zvals))
	for i,z in enumerate(zvals):
		demZ[i] = z + alt

	# Convert to cartesian xyz
	xyz = "+proj=geocent +a=6378140 +b=6356750 +no_defs"
	xform = pyproj.Transformer.from_crs(dem.crs, xyz)
	cartX, cartY, cartZ = xform.transform(demX, demY, demZ)

	# Interpolate with shapely	
	line = list(zip(cartX, cartY, cartZ))

	line = shapely.geometry.LineString(line)

	lineInterp = []

	for dist in range(0, int(line.length), step):
		lineInterp.append(line.interpolate(dist))

	lineInterp = shapely.geometry.LineString(lineInterp)
	lineInterp = list(lineInterp.coords)

	cartX, cartY, cartZ = zip(*lineInterp)
	
	# Convert back to dem crs and sample dem
	xform = pyproj.Transformer.from_crs(xyz, dem.crs)
	demX, demY, demZ = xform.transform(cartX, cartY, cartZ)

	points = zip(demX, demY)

	zvals = list(rio.sample.sample_gen(dem, points))

	demZ = np.zeros(len(zvals))
	for i,z in enumerate(zvals):
		demZ[i] = z + alt

	demZsmooth = rollmean(demZ, 100//step)
	# Convert back to cartesian and save
	xform = pyproj.Transformer.from_crs(dem.crs, xyz)
	cartX, cartY, cartZ = xform.transform(demX, demY, demZsmooth)

	fd = open("./hypo/%s_%dmAGL_%dmPost.csv" % (name, alt, step),'w')
	fd.write("x,y,z\n")
	for i in range(len(cartX)):
		fd.write("%.3f,%.3f,%.3f\n" % (cartX[i], cartY[i], cartZ[i]))
	fd.close()


dem.close()
shp.close()
sys.exit()


