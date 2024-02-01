#!/bin/bash

#python main.py /path/to/config.ini -n /path/to/nav.tab -d /path/to/dem.tif
mkdir -p ../output
python ../src/simc/main.py ../config/sharad_fpb.ini -o ../output/ -n ../nav/s_01294501_geom.tab -d ../dem/mola_radius_128ppd.tif
