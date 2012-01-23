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
#parse csv_tree_pruned and filter for genomes and species
#examples
#NC_012967,genome,Escherichia coli B str. REL606,chromosome
#316385,species,NC_010473,Escherichia coli str. K-12 substr. DH10B,no rank
open(TREE, "</scratch2/egg/webserv/template/genomes");
open(OUTPUT, ">/scratch2/egg/webserv/template/csv_autocomplete");
my @lines;
while(<TREE>){
	push(@lines,$_);
}

#output format: name, id, type, rank/dna type

foreach(@lines){
	chomp($_);
	my @fields = split /\,/;
	#0=id 2=id 
        my $type=$fields[1];
	if($type =~/genome/){
		print OUTPUT "$fields[2] $fields[3],$fields[0]\n";	
	#}elsif($type =~/species/){
	#	print OUTPUT "$fields[3],$fields[0],$fields[1],$fields[4]\n";
	}
}
