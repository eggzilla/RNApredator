#!/usr/bin/perl
#create tree - template for available genomes template
#problem parents with tax children can also have genome - children

use warnings;
use strict;
use diagnostics;
use utf8;
use Data::Dumper;
use Pod::Usage;
#use Bioperl Taxon
use Bio::Taxon;
use Bio::Tree::Tree;
use Cwd;
use List::MoreUtils qw/ uniq /;
#Write all Output to file at once
$|=1 ;
open(TEMPLATE1, ">/scratch2/egg/webserv/template/csv_tree_n1") or die("Could not open");
open(TEMPLATE2, ">/scratch2/egg/webserv/template/csv_tree_n2") or die("Could not open");
open(TEMPLATE3, ">/scratch2/egg/webserv/template/csv_tree_n3") or die("Could not open");
open(TEMPLATE4, ">/scratch2/egg/webserv/template/csv_tree_n4") or die("Could not open");
open(TEMPLATE5, ">/scratch2/egg/webserv/template/csv_tree_n5") or die("Could not open");
open(GENOMES, ">/scratch2/egg/webserv/template/genomes") or die("Could not open");
#open(CHECK,">/scratch2/egg/webserv/template/check") or die "Could not write check";
############################################################
#convert the total specieslist into a tree for the user input page
#data/lists/input_list_final 
#construct tree
print "1 START\n";
my $dbh = Bio::DB::Taxonomy->new(-source   => 'flatfile',
                                  -directory=> '/tmp',
                                  -nodesfile=> '/scratch2/egg/webserv/data/lists/taxdump/nodes.dmp',
	                          -namesfile=> '/scratch2/egg/webserv/data/lists/taxdump/names.dmp');

print "2 - reading database done\n";
#bacteria_root_node_id
my $bacteria_root_node_id = 2;
#everything not on this list will be pruned at the end.
my @relevant_nodes_list;
my @parents = qw(0);
get_children($bacteria_root_node_id, \@parents);
#prune_tree(\@relevant_nodes_list);
#prune_tree_file();

sub get_children{
	my $tax_id = shift; 
	my $parents_reference = shift;
	my @parents = @$parents_reference;
	#print "current tax_id is $tax_id\n";
	my $current_node = $dbh->get_taxon(-taxonid => "$tax_id");
        my $rank = $current_node->rank ;
	my $scientific_name = $current_node->scientific_name;
 	my $division= $current_node->division;
	#determine if node is node 2 or one of its childs and print them without display:none
	push(@parents, $tax_id);
	#print "Parent nodes:\n";
	#foreach my $parent(@parents){
	#	print "$parent\n";
	#}
	
	#add current node
	#1. to template file
	#2. then to tax array
	#get all descendent of current node and iterate over them
	my @descendents = $dbh->each_Descendent($current_node);
	my @descendents_tax_ids;
	if (@descendents){
		my $descendents_tax_ids = undef;
		foreach my $descendent(@descendents){
			my $descendent_tax_id = $descendent->id;
			push(@descendents_tax_ids,$descendent_tax_id); 
		}
		#print current node, then get_children ;-)
		#print "node_with_children\n";
			foreach my $descendent_tax_id(@descendents_tax_ids){
				my $leafs_present;
				#$leafs_present=find_leaves($tax_id, $scientific_name,$rank,\@parents);
				get_children($descendent_tax_id, \@parents);	
			}
			 my $genome_children_reference = find_leaves($tax_id, $scientific_name,$rank,\@parents);
                        my @genome_children = @$genome_children_reference;
			if($tax_id<=250000){
				 print TEMPLATE1 "$tax_id,"."tax,"."@descendents_tax_ids,"."@genome_children,"."$scientific_name,"."$rank,"."\n";
	                }elsif($tax_id<=500000 and $tax_id>250000){
				 print TEMPLATE2 "$tax_id,"."tax,"."@descendents_tax_ids,"."@genome_children,"."$scientific_name,"."$rank,"."\n";
               		}elsif($tax_id<=750000 and $tax_id>500000){
				 print TEMPLATE3 "$tax_id,"."tax,"."@descendents_tax_ids,"."@genome_children,"."$scientific_name,"."$rank,"."\n";
                	}elsif($tax_id<=1000000 and $tax_id>750000){
				 print TEMPLATE4 "$tax_id,"."tax,"."@descendents_tax_ids,"."@genome_children,"."$scientific_name,"."$rank,"."\n";
                	}else{
				 print TEMPLATE5 "$tax_id,"."tax,"."@descendents_tax_ids,"."@genome_children,"."$scientific_name,"."$rank,"."\n";
                	}
	
			
                        #print TEMPLATE "$tax_id,"."tax,"."@descendents_tax_ids,"."@genome_children,"."$scientific_name,"."$rank,"."\n";		
	}
	else{
		#if this descendent has no descendents we look for genomes associated with this tax_id	
		#hand over tax id and pixel, shift, we need to have genomes printed out directly unter the parent node
		my $genome_children_reference = find_leaves($tax_id, $scientific_name,$rank,\@parents);
                my @genome_children = @$genome_children_reference;
		if($tax_id<=250000){
			 print TEMPLATE1 "$tax_id,"."tax,".","."@genome_children,"."$scientific_name,"."$rank,"."\n";
		}elsif($tax_id<=500000 and $tax_id>250000){
			 print TEMPLATE2 "$tax_id,"."tax,".","."@genome_children,"."$scientific_name,"."$rank,"."\n";
		}elsif($tax_id<=750000 and $tax_id>500000){
			 print TEMPLATE3 "$tax_id,"."tax,".","."@genome_children,"."$scientific_name,"."$rank,"."\n";
		}elsif($tax_id<=1000000 and $tax_id>750000){
			 print TEMPLATE4 "$tax_id,"."tax,".","."@genome_children,"."$scientific_name,"."$rank,"."\n";
                }else{
			 print TEMPLATE5 "$tax_id,"."tax,".","."@genome_children,"."$scientific_name,"."$rank,"."\n";
		}

	}
	
#	print "d.add\($tax_id, $parent_id, \"$scientific_name \", \"http:\/\/insulin.tbi.univie.ac.at\/available_genomes.cgi\/ mode=\"tax_id\" id=\"$tax_id\"", \"$tax_id\", \'species\', \'img\/musicfolder.gif\'\);";
}

sub find_leaves{
	my $tax_id_parent = shift;
	my $scientific_name = shift;
	my $rank = shift;
	my $parents_reference = shift;
	my @parents = @$parents_reference;
	open (IN, "</scratch2/egg/webserv/data/lists/input_lists/input_list_final") or die "No Input List found";
	my @lines;
	while(<IN>){
        	push(@lines,$_);
	}
	my $title_line = shift(@lines);
	#First look if there are genomes attached to a tax-id, if yes print first the species node, then the genome nodes.
	#If not print the Species -Node indication that no genomes are available
	my @genomes;	
	my @accession_numbers;
	foreach(@lines){
		chomp;
		my @fields = split /\,/;
		#print "@fields\n";
		my $tax_id = $fields[3];
		$tax_id_parent =~ s/ //;
		$tax_id =~ s/ //;
		#if($tax_id_parent=~/51/){
		#	print CHECK "$tax_id_parent.$tax_id\n"; 
		#}
		if($tax_id_parent eq $tax_id){
			#print CHECK "match:$tax_id_parent.$tax_id\n";
			#first get the id for each table row, so we can easily identify the user selection
        	        my $accession_number_with_version = $fields[0];
			#print"leaf added\n";
	                #now we have the whole content of the accessionnumberfield in a variable, but we want to get rid of the .versionnumber part
               		 my @accession_number_with_version_split= split(/\./,$accession_number_with_version);
               		 my $accession_number= $accession_number_with_version_split[0];
               		 my $lenght = $fields[2];
                	 my $tax_id = $fields[3];
                	 my $tax_name = $fields[5];
               		 my $replicon = $fields[6];
               		#now we have all we need to add this leaf to the template file,.. we call a recursive function called find partents to find all phylogenetic nodes higher up in the tree
                	#the nodes already found by this function will be saved in an array and used as termination condition.
                	#the leafs below are labled with the accession_number
			push(@accession_numbers, $accession_number);
			#foreach(@parents){
			#	print"$_\n";	## Print Genome Node Parents
			#}
			$accession_number=~ s/\s+//;
			push(@parents, $accession_number);
			push(@relevant_nodes_list, @parents);
			
			#PRINT genomes and plasmids
                	print GENOMES "$accession_number,"."genome,"."$tax_name,"."$replicon\n";
		}
	}
        #if(@genomes){
        #       #print "species\n";
        #        #print TEMPLATE "$tax_id_parent,"."species,"."@accession_numbers,"."$scientific_name,"."$rank\n";
	#	#print genomes if available
	#	print TEMPLATE "@genomes";
        #}else{
        #        #print "no genome\n";
        #        #print TEMPLATE "$tax_id_parent,"."tax,".","."$scientific_name,"."$rank\n";
        #}
	return (\@accession_numbers);
}
close TEMPLATE1;
close TEMPLATE2;
close TEMPLATE3;
close TEMPLATE4;
close TEMPLATE5;

