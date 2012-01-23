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
#convert the total specieslist into an html table for the user input page
my @lines = (<>);

foreach(@lines){
	chomp($_);
	my @fields = split /\,/;
	#first get the id for each table row, so we can easily identify the user selection
        my $id_info = $fields[0];
	#now we have the whole content of the accessionnumberfield in a variable, but we want to get rid of the .versionnumber part
	my @id_infos= split(/\./,$id_info);
	my $id= $id_infos[0];
	#my $converted_line= "<tr id="$id""."bgcolor='#FFFFFF'"."onMouseOver="this.bgColor='#CCFF99'";"."onMouseOut="this.bgColor='#FFFFFF';""."onclick="select(this)">";
	my $converted_line= "\<tr id\=\"$id\"\>";
	my $i=0;
	foreach my $field(@fields){
		if(($i==3)||($i==2)||($i==0)||($i==5)||($i==6)){
			$converted_line ="$converted_line"."<td>"."$field"."</td>"; 

		}elsif(($i==7)){
			$converted_line ="$converted_line"."<td>"."$field"."<td>";
		}
		$i++;
	}
	$converted_line ="$converted_line"."</tr>";
	print"$converted_line\n";
}

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
		push @{ $taxid_accession_children{$key} }, ":$accession,$replicon";
	}else{
		#if key does not exist add it and taxname as first value in array
		$taxid_accession_children{$key}[0] = "$tax_name,$accession,$replicon";		
	} 
}

#now we should have assembled or hash of tax_ids and print it to html

for my $entries ( keys %taxid_accession_children ){
 	print "<tr><td id=\"$entries\" >"."$entries: @{ $taxid_accession_children{$entries} }"."</td></tr>\n";
}

