#!/bin/bash
printf $1" "$2" "$3" "$4" "$5"\n";
echo "go<-\"$1/$2.ftn.goa\" ; kegg<-\"$1/$2.ftn.rad\";fil<-\"$3\" ; gene_list<-\"$4\"; output_path<-\"$5\"" | cat - "/$5/GO_Kegg.R" | R --slave \ --vanilla >> /dev/null
