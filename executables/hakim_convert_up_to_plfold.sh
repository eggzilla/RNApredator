#!/bin/bash
#j=`echo "$1" | sed -r 's/u1.+out/openen/'`; 
#printf "sRNA_openen\n";
cat $1 | tail -n +5 | perl -lane 'my $line=join("\t",@F); if($line=~/^\#\s[ATCGU]+$/){print "#opening energies";}elsif($line=~/^#\spos/){$line=~s/[uS]//g; $line=~s/#/ #i\$/; $line=~s/pos\s+/l=/;print $line;}else{print $line;}' > sRNA_openen
