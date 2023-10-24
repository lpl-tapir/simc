#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch job.txt
rm -f job.txt
touch job.txt

ncore=36

year=2021

ipfix=/zippy/MARS/targ/xped/OIB-AK/radar/$year/hdf5
pfix=/zippy/MARS/code/modl/simc/simc
#opfix=/zippy/MARS/targ/supl/UAF/$year/clutter
opfix=/zippy/MARS/targ/xped/OIB-AK/radar/$year/sim/ifsar

for p in $ipfix/*.h5;
do
    echo $p
    echo "python $pfix/main.py $pfix/config/oib_ak_ifsar.ini -n $p -o $opfix/" >> job.txt
done

parallel -j $ncore < ./job.txt
#parallel -j 50 --sshloginfile $pfix/code/batch/machines.txt < $pfix/code/batch/job.txt

rm job.txt

