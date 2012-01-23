#!/usr/bin/perl
#create tree - template for available genomes template
#WARNING - all hardcoded paths are corresponding to xc00 directory structure not insulin (scratch instead of scratch2)

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
open(TEMPLATE, ">/scratch/egg/webserv/template/tree") or die("Could not open");
############################################################
#convert the total specieslist into a tree for the user input page
#data/lists/input_list_final 
#construct tree
print "1 START\n";
my $dbh = Bio::DB::Taxonomy->new(-source   => 'flatfile',
                                  -directory=> '/tmp',
                                  -nodesfile=> '/scratch/egg/webserv/data/lists/taxdump/nodes.dmp',
	                          -namesfile=> '/scratch/egg/webserv/data/lists/taxdump/names.dmp');

print "2 - reading database done\n";
#bacteria_root_node_id
my $bacteria_root_node_id = 2;
#everything not on this list will be pruned at the end.
my @relevant_nodes_list;
my @parents = qw(0);
get_children($bacteria_root_node_id, 0, \@parents);
prune_tree(\@relevant_nodes_list);
#prune_tree_file();

sub get_children{
	my $tax_id = shift; 
	my $horizontal_shift = shift;
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
		$horizontal_shift+=20;
		#print "node_with_children\n";
		if(($tax_id eq $parents[1])){
			print TEMPLATE "\<p style=\"margin-left:"."$horizontal_shift"."px;\" id=\"$tax_id\" data-userid=\""."@descendents_tax_ids"."\"\>\<img src=\"../pictures/node.png\" \>$scientific_name-$rank-$tax_id\<\/p\>\n";
                }elsif($tax_id eq $parents[2]){
			print TEMPLATE "\<p style=\"margin-left:"."$horizontal_shift"."px;\" id=\"$tax_id\" data-userid=\""."@descendents_tax_ids"."\"\>\<img src=\"../pictures/node_children.png\" onclick=\"expand_collapse\(this\)\" \>$scientific_name-$rank-$tax_id\<\/p\>\n";
		}else{
                	print TEMPLATE "\<p style=\"display:none;margin-left:"."$horizontal_shift"."px;\" id=\"$tax_id\" data-userid=\""."@descendents_tax_ids"."\"\>\<img src=\"../pictures/node_children.png\" onclick=\"expand_collapse\(this\)\" \>$scientific_name-$rank-$tax_id\<\/p\>\n";
		}
		foreach my $descendent_tax_id(@descendents_tax_ids){
			get_children($descendent_tax_id, $horizontal_shift, \@parents);	
		}	
	}else{
		#if this descendent has no descendents we look for genomes associated with this tax_id	
		#hand over tax id and pixel, shift, we need to have genomes printed out directly unter the parent node
		my $leafs_present;
		$horizontal_shift+=20;
		$leafs_present=find_leaves($tax_id, $horizontal_shift,$scientific_name,$rank,\@parents);
		}
	
#	print "d.add\($tax_id, $parent_id, \"$scientific_name \", \"http:\/\/insulin.tbi.univie.ac.at\/available_genomes.cgi\/ mode=\"tax_id\" id=\"$tax_id\"", \"$tax_id\", \'species\', \'img\/musicfolder.gif\'\);";
}

sub find_leaves{
	my $tax_id_parent = shift;
	my $horizontal_shift = shift;
	my $scientific_name = shift;
	my $rank = shift;
	my $parents_reference = shift;
	my @parents = @$parents_reference;
	$horizontal_shift+=20;
	open (IN, "</scratch/egg/webserv/data/lists/input_lists/input_list_final") or die "No Input List found";
	my @lines;
	while(<IN>){
        	push(@lines,$_);
	}
	my $title_line = shift(@lines);
#	my @lines = (</scratch/egg/webserv/data/lists/input_list_final>);
	#print "LINES @lines\n";
	#First look if there are genomes attached to a tax-id, if yes print first the species node, then the genome nodes.
	#If not print the Species -Node indication that no genomes are available
	my @genomes;	
	my @accession_numbers;
	foreach(@lines){
		chomp;
		my @fields = split /\,/;
		#print "@fields\n";
		my $tax_id = $fields[3];
		#print"if-param $tax_id_parent == $tax_id";
		#print "Parent-Taxid:$tax_id_parent\n";
		#print "Taxid:$tax_id\n";
		if($tax_id_parent == $tax_id){
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
			my $horizontal_shift_genome = $horizontal_shift + 20;
			#foreach(@parents){
			#	print"$_\n";	## Print Genome Node Parents
			#}
			push(@parents, $accession_number);
			push(@relevant_nodes_list, @parents);
                	push(@genomes, "\<p style=\"display:none;margin-left:"."$horizontal_shift_genome"."px;\" id=\"$accession_number\"\>\<img src=\"../pictures/genome.png\" alt=\"Image\" onclick=\"expand_collapse\(this\)\"\> \<a href=\"http:\/\/insulin.tbi.univie.ac.at\/target_search.cgi\?id\=$accession_number\"\>\-$tax_name"."\-$replicon"."\-$accession_number"."\<\/a\> \<\/p\>\n");
		}
	}
        if(@genomes){
               #print "species\n";
                print TEMPLATE "\<p style=\"display:none;margin-left:"."$horizontal_shift"."px;\" id=\"$tax_id_parent\" data-userid=\""."@accession_numbers"."\"\>\<img src=\"../pictures/species.png\" alt=\"Image\" onclick=\"expand_collapse\(this\)\"\> \<a href=\"http:\/\/insulin.tbi.univie.ac.at\/target_search.cgi\?id\=$tax_id_parent\"\>\-  $scientific_name\-$rank\-$tax_id_parent <\/a\>\<\/p\>\n";
		#print genomes if available
                #horizontal shift has to be incremented by 20 for this
		print TEMPLATE "@genomes";
        }else{
                #print "no genome\n";
                        #print TEMPLATE "\<p style=\"margin-left:"."$horizontal_shift"."px;\" id=\"$tax_id_parent\" children=\""."none"." \"\>\<img src\=\"../pictures/no_genomes.png\" alt=\"Image\"\> \<a href=\"test.html\"\>-$scientific_name-$rank-$tax_id_parent-no Genomes\<\/a\> \<\/p\>\n";
        }
	
}
close TEMPLATE;

sub prune_tree{
	my $relevant_nodes_list_reference = shift;
	my @relevant_node_list = @$relevant_nodes_list_reference; 
	my @tree_pruned;
	print "3. Tree Pruning\n";
	#get rid of all nodes who are in the list more than once
	use List::MoreUtils qw/ uniq /;
	my @relevant_nodes_list_reduced = uniq @relevant_node_list;
	#now we prune the tree by eliminating unwanted lines from the tree file
	open(TEMPLATE, "</scratch/egg/webserv/template/tree") or die("Could not open");
	open(TREE, ">/scratch/egg/webserv/template/tree_pruned") or die("Could not open");
	my @lines;
	while(<TEMPLATE>){
                push(@lines,$_);
        }
	foreach my $line(@lines){
		my $relevant = 0;
		foreach my $relevance_check(@relevant_nodes_list_reduced){
                        if($line=~/id=\"$relevance_check\"/){
                                $relevant = 1;
                       }
		}
		if($relevant){
			print TREE "$line";
		}
	}	
}	

sub prune_tree_file{
	`cat /scratch/egg/webserv/template/relevant | sort -u > /scratch/egg/webserv/template/relevant_uniq`;
        open(RELEVANT, "</scratch/egg/webserv/template/relevant_uniq") or die("Could not open");
        my @relevant_nodes_list;
	#input spliten funkt nicht gescheit!!!!
        while(<RELEVANT>){
		@relevant_nodes_list=split /\s/;		
        }
        my @relevant_nodes_list_reduced = qw ( 2 );
        my @tree_pruned;
        print "3. Tree Pruning\n";
        #get rid of all nodes who are in the list more than once
	#does not work.. done over bash iwth sort -u
        #foreach my $node(@relevant_nodes_list){
        #        foreach my $check_node(@relevant_nodes_list_reduced){
        #                my $node_present = 0;
        #                if($node eq $check_node){
        #                        $node_present = 1;
        #                }
        #                unless($node_present){
        #                        push (@relevant_nodes_list_reduced,$node);
        #                }
        #        }
        #}
        #now we prune the tree by eliminating unwanted lines from the tree file
        open(TEMPLATE, "</scratch/egg/webserv/template/tree") or die("Could not open");
        open(TREE, ">/scratch/egg/webserv/template/tree_pruned") or die("Could not open");
        my @lines;
        while(<TEMPLATE>){
                push(@lines,$_);
        }
        foreach my $line(@lines){
                my $relevant = 0;
                foreach my $relevance_check(@relevant_nodes_list_reduced){
                        if($line=~/id=\"$relevance_check\"/){
                                $relevant = 1;
                       }
                }
                if($relevant){
                        print TREE "$line";
                }
        }
}

