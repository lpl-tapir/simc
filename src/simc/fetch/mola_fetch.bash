#!/bin/bash

# Download MOLA grid
#mkdir -p ../dem
#wget -r -nc -np -nH --cut-dirs 6 -e robots=off --no-parent -P ../dem -A "megr*" https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/

# Merge files into single geotiff, fix meters per pixel
#gdal_merge.py -o ../dem/mola_radius_128ppd.tif ../dem/megr*.lbl
gdal_edit.py ../dem/mola_radius_128ppd.tif -tr 463.0576672 -463.0576672

# to-do, mask out mt. hellas oddity?
