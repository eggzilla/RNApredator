#!/bin/bash
for k in /scratch2/egg/webserv/data/mRNA_accessiblities/all/*;
do cd $k/accessiblity/;
echo "cd to $i/accessiblity";
for i in *openen; do j=`echo $i | sed -r 's/(\||:)+/_/g'`; mv $i $j; done 
cd ../../;
done
