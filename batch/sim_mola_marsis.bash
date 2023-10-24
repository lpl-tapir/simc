#!/bin/bash

# First arg is a text file with lines in the format h2179_0000,s_00266001

outdir=/zippy/MARS/targ/modl/simc/marsis/

touch job.txt
rm -f job.txt
touch job.txt

## Paths
codedir=/zippy/MARS/code/modl/simc

#mkdir $outdir

while read p;
do
    echo "python $codedir/simc/main.py $codedir/simc/config/marsis.ini -o $outdir -n /zippy/MARS/orig/supl/MARSIS/PDS/$p -d $codedir/dem/MOLA_SHARAD_128ppd_radius.tif" >> job.txt
done <$1

parallel -j 34 < ./job.txt

