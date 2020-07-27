#!/bin/bash

# First arg is a text file with lines in the format h2179_0000,s_00266001

touch job.txt
rm -f job.txt
touch job.txt

## Paths
outdir=/zippy/MARS/targ/modl/simc/stefano
codedir=/zippy/MARS/code/modl/simc

while read p;
do
    hrsc=`cut -d',' -f1 <<< $p`
    geom=`cut -d',' -f2 <<< $p`
    $codedir/simc/fetch/hrsc_fetch.bash $hrsc
    $codedir/simc/fetch/geom_fetch.bash $geom
    echo "python $codedir/simc/main.py $codedir/simc/config/sharad_hrsc.ini -o $outdir -n $codedir/nav/geom/${geom}_geom.tab -d $codedir/dem/hrsc/${hrsc}_dt4.img" >> job.txt
done <$1

#parallel -j 48 < ./job.txt

