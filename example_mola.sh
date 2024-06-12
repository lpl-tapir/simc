#!/bin/bash

#python main.py /path/to/config.ini -n /path/to/nav.tab -d /path/to/dem.tif

#python main.py ./config/sharad_fpb.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0126XX/S_01266602_GEOM.TAB -d ../pds/MOLA_SHARAD_128ppd_radius_mthellasmask.tif
#python main.py ./config/sharad_fpb.ini -n S_00891301_GEOM.TAB -d ../pds/MOLA_SHARAD_128ppd_radius_mthellasmask.tif
#python main.py ./config/sharad_fpb.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0106XX/S_01061401_GEOM.TAB -d ../pds/MOLA_SHARAD_128ppd_radius_mthellasmask.tif
python main.py ./config/sharad_fpb.ini -n /zippy/MARS/targ/modl/MRO/CTX_DEM/GEOM_LDA/S_00691803_GEOM.TAB -d ../pds/MOLA_SHARAD_128ppd_radius_mthellasmask.tif
