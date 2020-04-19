#!/bin/bash

# First arg is a HRSC label in the format h2179_0000

baseurl="http://pds-geosciences.wustl.edu/mex/mex-m-hrsc-5-refdr-dtm-v1/mexhrs_2001/data/"
s=`echo $1 | cut -c 2-5`
wget -P /zippy/MARS/code/modl/MRO/simc/test/temp/dem/hrsc/ -nc "${baseurl}${s}/${1}_da4.img"
