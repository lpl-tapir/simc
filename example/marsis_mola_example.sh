#!/bin/bash

# Download MARSIS file
python ../fetch/marsis_fetch.py 8700

mkdir -p ../output
python ../src/simc/main.py ../config/marsis.ini -o ../output/ -n ../nav/e_08700_ss3_trk_cmp_m_g.dat -d ../dem/mola_radius_128ppd.tif -p
