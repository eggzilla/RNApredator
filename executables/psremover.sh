#!/bin/bash
for i in /scratch2/egg/webserv/data/mRNA_accessiblities/all/*;
do 
cd $i/accessiblity/;
echo "cd to $i/accessiblity";
rm *.ps;
cd ../../;
done
