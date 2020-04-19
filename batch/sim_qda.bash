#!/bin/bash

# First arg is a text file with lines in the format 261202.csv

touch job.txt
rm -f job.txt
touch job.txt

root=/zippy/MARS/code/modl/simc_3d
simc=$root/code/simc.py
cfg=$root/code/config/sharad_qda.cfg
nav=$root/test/temp/nav/qda
dem=$root/test/temp/dem/MOLA_SHARAD_128ppd.tif

while read p;
do
    geom=$p
    echo "python ${simc} ${cfg} ${nav}/${geom} ${dem}" >> job.txt
done <$1

cd ..
parallel -j 20 < ./batch/job.txt

