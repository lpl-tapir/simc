#!/bin/bash

# First arg is a text file where each line is the name of a nav file

touch job.txt
rm -f job.txt
touch job.txt

ncore=40

ipfix=/zippy/MARS/code/modl/simc/nav/hypo
pfix=/zippy/MARS/code/modl/simc/simc
dem=/zippy/MARS/code/modl/simc/dem/mala_bag_bering_ADEM_10m.tif
out=/zippy/MARS/targ/modl/simc/hypo_arctic

for p in $ipfix/*.csv;
do
    echo "python $pfix/main.py $pfix/config/oib_hypo.ini -d $dem -n $p -o $out" >> job.txt
done

parallel -j $ncore < ./job.txt
#parallel -j 50 --sshloginfile $pfix/code/batch/machines.txt < $pfix/code/batch/job.txt

#rm job.txt

