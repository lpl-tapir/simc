#!/bin/bash

# First arg is a text file with lines in the format s_00266001

touch job.txt
rm -f job.txt
touch job.txt

pfix=/home/mchristo/proj/simc/

while read p;
do
    geom=$p
    ../fetch/geom_fetch.bash $geom
    echo "python $pfix/simc/main.py $pfix/simc/config/sharad_fpb.ini -n $pfix/test/nav/geom/${geom}_geom.tab -d $pfix/test/dem/MOLA_SHARAD_128ppd_radius.tif" >> job.txt
done <$1

cd ..
parallel -j 10 < ./batch/job.txt

