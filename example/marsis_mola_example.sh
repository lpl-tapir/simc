#!/bin/bash

#python main.py /path/to/config.ini -n /path/to/nav.tab -d /path/to/dem.tif
mkdir -p ../output
python ../src/simc/main.py ../config/marsis.ini -o ../output/ -n ../nav/e_08700_ss3_trk_cmp_m_g.dat -d ../dem/mola_radius_128ppd.tif -p
