#!/usr/bin/perl
#cvs to html

use warnings;
use strict;
use diagnostics;
use utf8;
use Data::Dumper;
use Pod::Usage;
use Cwd;
$|=1;
############################################################
#convert a .ftn file containing | or |: in one with _ instead
#RNAplex cant process |
my $filename = $ARGV[0];
open (IN, "</scratch2/egg/webserv/data/ftn_all_species/$filename") or die "No Input List found\n";
open (OUT, ">/scratch2/egg/webserv/data/ftn_all_species_Final/$filename") or die "could not write output\n";
my @lines;
while(<IN>){
                push(@lines,$_);
}

foreach my $line (@lines){
        chomp($line);
        $line =~ s/(\||:)+/_/g;
	if($line =~ m/\>/){
		print OUT "\n$line\n";
	}else{
	        print OUT "$line";
	}
}



