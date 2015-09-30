#!/usr/bin/perl
#functional,.. but data is inconsistent... child nodes are missing
#example 75560
my ($host,$webserver_name,$source_dir,$server,$available_genomes,$server_static);
use strict;
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
      $base_dir = "$source_dir/html";
  }
}
my $cgi_query = CGI->new;
#Data files have following format:
#output format: name, id, type, rank/dna type
#Request has this format:
#NAME: id PARAMETER: 2
print $cgi_query->header();
#print $cgi_query->start_html;
#print "Content-Type: text/html\n\n";
my $query_input = $cgi_query->param('query') || undef;
my $query;
#taintcheck 
if(defined($query_input)){
	my $query_length = length($query_input);
        if($query_length>25){
                $query_input = undef;
        }elsif($query_input =~ //){
		$query = $query_input;	
		output($query);
	}	
}else{
        $query = undef;
}

sub output(){
	my $query_output = shift;
	chdir("$source_dir/template/");
	#escape characters for bash
	my $query_output_quoted=quotemeta($query_output);
	my @match=`grep -ihP $query_output_quoted csv_autocomplete`;
	my $suggestion= "";
	my $data = "";
	#parse matching lines
	foreach my $matching_line (@match){
		chomp($matching_line);
		my @fields =split(/\,/,$matching_line);
		if($suggestion eq ""){
			$suggestion=$suggestion."\'$fields[0]\'";
		}else{
			$suggestion=$suggestion.",\'$fields[0]\'";
		}
		if($data eq ""){
			$fields[1]=~s/ //;
               		$data=$data."\'$fields[1]\'"; 
		}else{
			$fields[1]=~s/ //;
                	$data=$data.",\'$fields[1]\'";
                }	
	}
	       print "{
                       query:\'$query_output\',
                       suggestions:[$suggestion],
                       data:[$data]
               }";
}
#Example output:
#	print "{
#			query:'Li',
# 			suggestions:['Liberia','Libyan Arab Jamahiriya','Liechtenstein','Lithuania'],
#		 	data:['LR','LY','LI','LT']
# 		}";
