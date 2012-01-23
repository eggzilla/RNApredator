#!/usr/bin/perl
#Output of RNAPlex Webserver
#Execute in script/ Folder of webserver
use warnings;
use strict;
use diagnostics;
use Data::Dumper;
use Pod::Usage;
use IO::String;
use Bio::SeqIO;
use Cwd;

#dummy for function
sub print3{
	my $print = shift;
	print "$print";
	1;
}
1;

