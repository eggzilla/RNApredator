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
#convert the total specieslist into an html table for the user input page
my @lines = (<>);

foreach(@lines){
	chomp($_);
	my @fields = split /\,/;
	my $converted_line= "<tr>";
	foreach my $field(@fields){
		$converted_line ="$converted_line"."<td>"."$field"."</td>"; 
	}
	$converted_line ="$converted_line"."</tr>";
	print"$converted_line\n";
}
