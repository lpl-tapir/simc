#!/bin/bash

# First arg is a HRSC label in the format h2179_0000

savedir=/zippy/MARS/code/modl/simc/dem/hrsc/

baseurl="http://pds-geosciences.wustl.edu/mex/mex-m-hrsc-5-refdr-dtm-v1/mexhrs_2001/data/"
s=`echo $1 | cut -c 2-5`
wget -P $savedir -nc "${baseurl}${s}/${1}_dt4.img"
