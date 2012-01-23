#!/usr/bin/perl
#Input of  RNaplex Server 
#in script/ Folder
use warnings;
use strict;
use diagnostics;
use Data::Dumper;
use Pod::Usage;
use IO::String;
use Bio::SeqIO;
use Cwd;
use CGI;
use Template;

#debug/dummy function
sub print{
	my $print = shift;
	print "$print\n";
	1;
}
1;

