#!/bin/bash

# First arg is a text file with lines in the format s_00266001

outdir=../out/stefano

#source /opt/anaconda3/etc/profile.d/conda.sh
#conda activate sim3

touch jobm.txt
rm -f jobm.txt
touch jobm.txt

touch jobd.txt
rm -f jobd.txt
touch jobd.txt

while read g;
do
    echo "./fetch/geom_fetch.bash $g" >> jobd.txt
    echo "python ./main.py ./config/sharad_fpb.ini -o $outdir -n ../test/nav/geom/${g}_geom.tab -d ../test/dem/MOLA_SHARAD_128ppd_radius.tif" >> jobm.txt
done <$1

cd ..
parallel -j 12 < ./batch/jobd.txt
parallel -j 10 < ./batch/jobm.txt

rm ./batch/jobd.txt ./batch/jobm.txt
