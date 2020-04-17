#!/bin/bash

# First arg is a text file with lines in the format s_00266001

touch job.txt
rm -f job.txt
touch job.txt

touch jobd.txt
rm -f jobd.txt
touch jobd.txt

pfix=/home/mchristo/proj/simc/

while read p;
do
    echo "$pfix/simc/fetch/geom_fetch.bash $p" >> jobd.txt
    echo "python $pfix/simc/main.py $pfix/simc/config/sharad_fpb.ini -n $pfix/test/nav/geom/${p}_geom.tab -d $pfix/test/dem/MOLA_SHARAD_128ppd_radius.tif" >> job.txt
done <$1

parallel -j 10 < ./jobd.txt
parallel -j 10 < ./job.txt

