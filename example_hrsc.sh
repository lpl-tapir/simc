#!/bin/bash

#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0089XX/S_00894601_GEOM.TAB  -d ../pds/MOLA_SHARAD_128ppd_radius_mthellasmask.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0089XX/S_00894601_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0680XX/S_06802001_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0089XX/S_00891301_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0125XX/S_01252601_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0106XX/S_01061401_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_dt4.ini -n S_00894601_GEOM.TAB  -d ../dem/hrsc/h1887_0000_dt4.img
#python main.py ./config/sharad_hrsc_dt4.ini -n S_01061401_GEOM.TAB  -d ../dem/hrsc/h1887_0000_dt4.img
#python main.py ./config/sharad_hrsc_dt4.ini -n S_00891301_GEOM.TAB  -d ../dem/hrsc/h1887_0000_dt4.img
#python main.py ./config/sharad_hrsc_dt4.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0680XX/S_06802001_GEOM.TAB  -d ../dem/hrsc/h1423_0001_dt4.img
#python main.py ./config/sharad_hrsc_dt4.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0089XX/S_00891301_GEOM.TAB  -d ../dem/hrsc/h1887_0000_dt4.img
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0089XX/S_00891301_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0126XX/S_01266602_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n S_00891301_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n GEOM_LDA/S_00915701_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n GEOM_LDA/S_01255901_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n GEOM_LDA/S_01252601_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif

#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0089XX/S_00891301_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0089XX/S_00894601_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0091XX/S_00915701_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0095XX/S_00951301_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0106XX/S_01061401_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0125XX/S_01252601_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0106XX/S_01061401_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0421XX/S_04211701_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_dt4.ini -n /zippy/MARS/targ/modl/MRO/CTX_DEM/GEOM_LDA/S_04211701_GEOM.TAB  -d ../dem/hrsc/h0380_0001_dt4.img
#python main.py ./config/sharad_hrsc_dt4.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0682XX/S_06825401_GEOM.TAB  -d ../dem/hrsc/h5196_0000_dt4.img
#python main.py ./config/sharad_hrsc_roberto.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0682XX/S_06825401_GEOM.TAB  -d ../dem/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif
#python main.py ./config/sharad_hrsc_dt4.ini -n /zippy/MARS/targ/modl/MRO/CTX_DEM/GEOM_LDA/S_06825401_GEOM.TAB  -d ../dem/hrsc/h5196_0000_dt4.img
python main.py ./config/sharad_hrsc_dt4.ini -n /zippy/MARS/orig/supl/SHARAD/PDS_v2/DATA/GEOM/S_0421XX/S_04211701_GEOM.TAB  -d ../dem/hrsc/h0380_0001_dt4.img
