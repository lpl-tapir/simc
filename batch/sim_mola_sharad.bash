#!/bin/bash

# First arg is a text file with lines in the format h2179_0000,s_00266001

outdir=../out/spld

touch job.txt
rm -f job.txt
touch job.txt

## Paths
outdir=/zippy/MARS/targ/modl/simc/mcglasson_4Dec2020
codedir=/zippy/MARS/code/modl/simc

#mkdir $outdir

while read p;
do
    $codedir/simc/fetch/geom_fetch.bash $p
    echo "python $codedir/simc/main.py $codedir/simc/config/sharad_fpb.ini -o $outdir -n $codedir/nav/geom/${p}_geom.tab -d $codedir/dem/MOLA_SHARAD_128ppd_radius.tif" >> job.txt
done <$1

parallel -j 30 < ./job.txt

