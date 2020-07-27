#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch job.txt
rm -f job.txt
touch job.txt

pfix=/zippy/MARS/code/modl/simc/simc

while read p;
do
    echo "python $pfix/main.py $pfix/config/oib_ak.cfg -n /zippy/MARS/targ/supl/UAF/2018/hdf5/${p}.h5" >> job.txt
done <$1

cd ..
#parallel -j 34 < /zippy/MARS/code/modl/simc/code/batch/job.txt
#parallel -j 50 --sshloginfile $pfix/code/batch/machines.txt < $pfix/code/batch/job.txt

