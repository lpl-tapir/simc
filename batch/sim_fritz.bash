#!/bin/bash

# First arg is a text file with lines in the format 261202.csv

touch job.txt
rm -f job.txt
touch job.txt

while read p;
do
    geom=$p
    echo "python ./simc.py ./config/sharad_fritz_fpb.cfg ../test/temp/nav/${geom} ../test/temp/dem/MOLA_SHARAD_128ppd.tif" >> job.txt
done <$1

cd ..
parallel -j 20 < ./batch/job.txt

