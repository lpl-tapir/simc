#!/bin/bash

# First arg is a text file with lines in the format s_00266001

#source /opt/anaconda3/etc/profile.d/conda.sh
#conda activate sim3

touch jobm.txt
rm -f jobm.txt
touch jobm.txt

while read p;
do
    geom=$p
    ../fetch/geom_fetch.bash $geom
    echo "python ./simc.py ./config/sharad_fpb.cfg ../test/temp/nav/geom/${geom}_geom.tab ../test/temp/dem/megt_128_merge.tif" >> jobm.txt
done <$1

cd ..
parallel -j 20 < ./batch/jobm.txt

