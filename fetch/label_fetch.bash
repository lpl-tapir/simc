#!/bin/bash

# First arg is a sharad number in the format s_00168901

savedir=/home/mchristo/proj/simc/label

baseurl="http://pds-geosciences.wustl.edu/mro/mro-m-sharad-5-radargram-v1/mrosh_2001/data/rgram/"
s=`echo $1 | cut -c 1-6`
wget -P $savedir -nc "${baseurl}${s}xx/${1}_rgram.lbl"
