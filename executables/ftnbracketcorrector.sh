#!/bin/bash
cd /scratch2/egg/webserv/data/ftn_all_species/;
for k in `ls *`;
do echo "processing $k";
/scratch2/egg/webserver/ftnbracketremover.pl $k;
done
