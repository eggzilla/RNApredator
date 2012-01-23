#!/usr/bin/perl -T
#cvs to html 

use warnings;
use strict;
use diagnostics;
use utf8;
use Data::Dumper;
use Pod::Usage;
use Cwd;

############################################################
#parse summary.txt converted to csv
my @lines = (<>);

foreach(@lines){
	chomp($_);
	my @fields = split /\,/;
	#0=accession 3=taxid 5=taxname
        my $field = $fields[5];
	#now we have the whole content of the accessionnumberfield in a variable, but we want to get rid of the .versionnumber part
	print "$field, ";
}
