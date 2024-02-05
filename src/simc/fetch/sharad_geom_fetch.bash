#!/bin/bash

# First and only arg is a USRDR SHARAD observation ID in the format s_00168901

mkdir -p ../nav

baseurl="https://pds-geosciences.wustl.edu/mro/mro-m-sharad-5-radargram-v2/mrosh_2101/data/geom/"
s=`echo $1 | cut -c 1-6`
wget -P ../nav -nc "${baseurl}${s}xx/${1}_geom.tab"
