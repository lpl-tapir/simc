#!/bin/bash

# First arg is a text file with lines in the format h2179_0000,s_00266001

touch job.txt
rm -f job.txt
touch job.txt

while read p;
do
    hrsc=`cut -d',' -f1 <<< $p`
    geom=`cut -d',' -f2 <<< $p`
    ../fetch/hrsc_fetch.bash $hrsc
    ../fetch/geom_fetch.bash $geom
    echo "python ./simc.py ./config/sharad_hrsc_fpb.cfg /zippy/MARS/code/modl/MRO/simc/test/temp/nav/geom/${geom}_geom.tab /zippy/MARS/code/modl/MRO/simc/test/temp/dem/hrsc/${hrsc}_da4.img" >> job.txt
done <$1

cd ..
parallel -j 48 < ./batch/job.txt

