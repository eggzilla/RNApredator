#!/usr/bin/perl -T
#cvs to html 

use warnings;
use strict;
use diagnostics;
use utf8;
use Data::Dumper;
use Pod::Usage;
use Cwd;

##########################################################################
#add tax_id table
my %taxid_accession_children;
open (IN, "</scratch2/egg/webserv/data/lists/input_lists/input_list_final") or die "No Input List found";
my @lines2;
while(<IN>){
                push(@lines2,$_);
        }

foreach(@lines2){
        chomp($_);
        my @fields = split /\,/;
        #first get the accession for each table row
        my $id_info = $fields[0];
        #now we have the whole content of the accessionnumberfield in a variable, but we want to get rid of the .versionnumber part
        my @id_infos= split(/\./,$id_info);
        my $accession = $id_infos[0];
	my $replicon = $fields[6];
	my $tax_name = $fields[5];
	my $key = $fields[3];
	if(exists($taxid_accession_children{$key})){
		#if key exists push accession,replicon to array
		push @{ $taxid_accession_children{$key} }, ";$accession";
	}else{
		#if key does not exist add it and taxname as first value in array
		$taxid_accession_children{$key}[0] = ";$accession";		
	} 
}

#now we should have assembled or hash of tax_ids and print it to cvs

for my $entries ( keys %taxid_accession_children ){
 	print "$entries @{ $taxid_accession_children{$entries} }\n";
}

