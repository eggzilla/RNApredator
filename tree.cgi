#!/usr/bin/perl
#example 75560
use strict;
my ($host,$webserver_name,$source_dir,$server,$available_genomes,$server_static);
use CGI::Carp qw(fatalsToBrowser);
use CGI;
use Cwd;
use Sys::Hostname;
BEGIN{
  #Set host specific variables according to hostname
  $host = hostname;
  $webserver_name = "RNApredator";
  $source_dir="/mnt/storage/progs/RNApredator/";
  $server;
  $available_genomes;
  $server_static="http://nibiru.tbi.univie.ac.at/RNApredator";

  #baseDIR points to the tempdir folder
  my $base_dir;
  if($host eq "erbse"){
      $server="http://localhost:800/RNApredator";
      $base_dir ="$source_dir/html";
  }elsif($host eq "linse"){
      $server="http://rna.tbi.univie.ac.at/RNApredator2";
      $base_dir ="/u/html/RNApredator";
  }elsif($host eq "nibiru"){
      $server = "http://nibiru.tbi.univie.ac.at/cgi-bin/RNApredator/target_search.cgi";
      $available_genomes = "http://nibiru.tbi.univie.ac.at/cgi-bin/RNApredator/available_genomes.cgi";
      $server_static = "http://nibiru.tbi.univie.ac.at/RNApredator";
      $source_dir = "/mnt/storage/progs/RNApredator";
      $base_dir = "$source_dir/html";
  }else{
  #if we are not on erbse or on linse we are propably on rna.tbi.univie.ac.at anyway
      $server = "http://rna.tbi.univie.ac.at/cgi-bin/RNApredator/target_search.cgi";
      $server_static = "http://rna.tbi.univie.ac.at/RNApredator";
      $available_genomes = "http://rna.tbi.univie.ac.at/cgi-bin/RNApredator/available_genomes.cgi";
      $source_dir = "/mnt/storage/progs/RNApredator";
  }
}

#open(DUMP, ">/u/html/test/dump") or die("Could not open - Dump");
#open(TREE, "</scratch2/egg/webserv/template/csv_tree_pruned") or die("Could not open - Tree");
#open(TREE, "</media/ram/egg/csv_tree_pruned") or die("Could not open - Tree");
my $query = CGI->new;
#Data files have following format:
#print TEMPLATE "$tax_id,"."tax,"."@descendents_tax_ids,"."$scientific_name,"."$rank,"."\n";
#"$accession_number,"."genome,"."$tax_name,"."$replicon\n";
#print TEMPLATE "$tax_id_parent,"."species,"."@accession_numbers,"."$scientific_name,"."$rank\n";
#Request has this format:
#NAME: id PARAMETER: 2
print $query->header();
print $query->start_html;
#print "Content-Type: text/html\n\n";
my $id_input = $query->param('id') || undef;
my $id;
#taintcheck 
if(defined($id_input)){
	my $id_length = length($id_input);
        if($id_length>25){
                $id_input = undef;
        }elsif($id_input =~ /\d+/){
		$id = $id_input;	
	}	
}else{
        $id = undef;
}

my $output="";
my @lines;

if(defined($id)){
	#read tree file once
	output($id,1);
	#print DUMP "$id\n";
}
sub output(){
	my $current_id = shift;
	my $root_node = shift;
	my $match=undef;
	if($current_id=~/^[A-Z]/){
		$match=`cd $source_dir/template; grep -P ^$current_id, genomes`;
	}else{
		if($current_id<=250000){
			$match=`cd $source_dir/template; grep -P ^$current_id, csv_tree_n1`;
                }elsif($current_id<=500000 and $current_id>250000){
			$match=`cd $source_dir/template; grep -P ^$current_id, csv_tree_n2`;
                }elsif($current_id<=750000 and $current_id>500000){
			$match=`cd $source_dir/template; grep -P ^$current_id, csv_tree_n3`;
                }elsif($current_id<=1000000 and $current_id>750000){
			$match=`cd $source_dir/template; grep -P ^$current_id, csv_tree_n4`;
                }else{
			$match=`cd $source_dir/template; grep -P ^$current_id, csv_tree_n5`;
                }

	}
        if(defined($match)){
        	chomp($match);
                my @fields = split(/\,/,$match);
                my $tax_id_field = $fields[0];
			#print"tax_id_field:$tax_id_field";
				#if node is a tax node return list of children and make them expandable
				#if they have children, same for species nodes
			if($fields[1] =~ /tax/){
				#get decendends
				#print"<br>tax field";
				if($root_node == 1){ 
					my @descandents = split(/ /,$fields[2]);
					my @genome_descandents = split(/ /,$fields[3]);
					push (@descandents,@genome_descandents);
					foreach my $descendent(@descandents){
							output($descendent,0);
							#print"<br>call recursion";
							#print DUMP "$descendent\n";
					}
				}else{
					#print node - do not print node if it has no children
					if($fields[3] =~ /[0-9]+/){
						my $to_output= "<li id=\"$current_id\" class=\"jstree-closed\" rel=\"species\"><a href=\"$server/target_search.cgi?id=$current_id\">$fields[4]</a></li>";
						$output="$output"."$to_output\n";
					}elsif($fields[2] =~ /[0-9]+/){
						my $to_output= "<li id=\"$current_id\" class=\"jstree-closed\" rel=\"tax\">$fields[4]</li>";
                                                $output="$output"."$to_output\n";	
					}else{
						#my $to_output= "<li id=\"$current_id\" rel=\"tax\"><a href=\"#\">$fields[4]</a></li>";
                                                #$output="$output"."$to_output\n";
					}	
				}
#			}elsif($fields[1] =~ /species/){
#				#get decendends
#                                if($root_node == 1){
#                                	my @descandents = split(/ /,$fields[2]);
#                                       	foreach my $descendent(@descandents){
#                                        	output($descendent,0);
#                                        }
#                              	}else{
#                                #print node - print as not expandable if it has no children
#                                	if($fields[2] =~ /[0-9]+/){
#                                		my $to_output= "<li class=\"jstree-closed\" id=\"$current_id\" rel=\"species\"><a href=\"http://insulin.tbi.univie.ac.at/target_search.cgi?id=$current_id\">$fields[3]</a></li>";
#                                        	$output="$output"."$to_output\n";
#					}else{
#						my $to_output= "<li id=\"$current_id\" rel=\"species\"><a href=\"http://insulin.tbi.univie.ac.at/target_search.cgi?id=$current_id\">$fields[3]</a></li>";
#                                                $output="$output"."$to_output\n";
#					}
#                                }
			}elsif($fields[1] =~ /genome/){
				my $to_output= "<li rel=\"genome\" id=\"$current_id\"><a color=\"#CC00CC\" href=\"$server/target_search.cgi?id=$current_id\">$fields[2] - $fields[3]</a></li>";
                                $output="$output"."$to_output\n";
				
                	}
	}
}
if($output eq ""){
	print "<li id=\"\" rel=\"tax\"><a href=\"#\">No Genomes</a></li>"
}
print "$output";




#my $output= "<li class=\"jstree-closed\"><a href=\"#\">Node 1</a></li><li><a href=\"#\">Node 2</a></li><li class=\"jstree-closed\"><a href=\"#\">Node 1</a></li>";
#print $output;

