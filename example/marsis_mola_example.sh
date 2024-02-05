#!/bin/bash

# Download MARSIS file
python simc-fetch-marsis 8700 ../nav/

mkdir -p ../output
simc ../config/marsis.ini -o ../output/ -n ../nav/e_08700_ss3_trk_cmp_m_g.dat -d ../dem/mola_radius_128ppd.tif -p
