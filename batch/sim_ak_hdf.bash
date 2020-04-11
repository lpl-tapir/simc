#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch job.txt
rm -f job.txt
touch job.txt

pfix=/zippy/MARS/code/modl/simc

while read p;
do
    echo "python $pfix/code/simc.py $pfix/code/config/oib_ak_hdf.cfg /zippy/MARS/targ/supl/UAF/2019/hdf5/${p}.h5 /zippy/MARS/code/modl/simc/test/temp/dem/ak2019/${p}.tif" >> job.txt
done <$1

cd ..
parallel -j 10 < /zippy/MARS/code/modl/simc/code/batch/job.txt
#parallel -j 50 --sshloginfile $pfix/code/batch/machines.txt < $pfix/code/batch/job.txt

