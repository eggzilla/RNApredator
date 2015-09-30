#!/usr/bin/perl
#Available genomes page
my ($host,$webserver_name,$source_dir,$server,$available_genomes,$server_static); 
use warnings;
use strict;
use diagnostics;
use utf8;
use Cwd;
use CGI::Carp qw(fatalsToBrowser);
use Sys::Hostname;

BEGIN{
  #Set host specific variables according to hostname
  $host = hostname;
  $webserver_name = "RNApredator";
  $source_dir="/mnt/storage/progs/RNApredator/";
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
#Control of the CGI Object remains with webserv.pl, additional functions are defined in the requirements below.
use CGI;
$CGI::POST_MAX=15000000; #max 15mb posts
my $query = CGI->new;
#using template toolkit to keep static stuff and logic in seperate files
use Template;

#Reset these absolut paths when changing the location of the requirements
#functions for genome selection
use lib "$source_dir/lib/BioPerl-1.6.901/";
use lib "$source_dir/executables/";
#require "$source_dir/executables/available_genomes.pl";
use Data::Dumper;
use Pod::Usage;
use IO::String;
use Bio::SeqIO;

sub output{
        my $query_output = shift;
        #escape characters for bash
        my $query_output_quoted=quotemeta($query_output);
        my @match=`grep -ihP $query_output_quoted $source_dir/template/csv_autocomplete`;
        my $return_value="";
        my $header="<tr><td style=\"width: 60%\">Designation</td><td style=\"width: 15%\">Accession Number</td><td style=\"width: 20%\">Select for Target Search</td></tr>";
        my $output="";
        #parse matching lines
        foreach my $matching_line (@match){
                chomp($matching_line);
                my @fields =split(/\,/,$matching_line);
                        $output=$output."<tr><td>$fields[0]</td><td>$fields[1]</td><td><a href=\"$server/target_search.cgi?id=$fields[1]\">Link</a></td></tr>";

        }
        if($output eq ""){
                $output=$output."<tr><td colspan=\"3\"><u>no match found</u></td></tr>";
        }
        $return_value="$header"."$output";
        return "$return_value";
}


######STATE - variables##########################################
#determine the query state by retriving CGI variables
#$page if =0 then input, if =1 then calculate and if =2 then output
my $page = $query->param('page') || "0"; #
my $search_string = $query->param('query') || "";

######INPUT######################################################
#Print HTTP-Header for input-page

if($page eq "0"){
	print "Content-type: text/html; charset=utf-8\n\n";
	my $template = Template->new({
  	  	# where to find template files
    		INCLUDE_PATH => ["$source_dir"],
		#Interpolate => 1 allows simple variable reference
		#INTERPOLATE=>1,
		#allows use of relative include path
		RELATIVE=>1,
	});

	my $file = 'template/available_genomes.html';
	my $vars = {
   		title => "RNApredator bacterial sRNA target prediction Webserver - Available Genomes",
	   	tbihome => "http://www.tbi.univie.ac.at/",
		banner => "$server_static/pictures/banner_final.png",
                serveradress => "$server",
		introduction => "introduction.html",
	        available_genomes => "$available_genomes",
                staticcontentaddress => "$server_static",
	        target_search => "$server",
	        help => "help.html",
		scriptfile => "template/availablegenomesscriptfile",
		stylefile => "template/availablegenomesstylefile"
	};
	$template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
}

######SEARCH-RESULT#####################################################

if($page eq "1"){
        print "Content-type: text/html; charset=utf-8\n\n";
        my $template = Template->new({
                # where to find template files
                INCLUDE_PATH => ["$source_dir"],
                #Interpolate => 1 allows simple variable reference
                #INTERPOLATE=>1,
                #allows use of relative include path
                RELATIVE=>1,
        });
	my $output = output($search_string);	
        my $vars = {
                title => "RNApredator bacterial sRNA target prediction Webserver - Available Genomes",
                tbihome => "http://www.tbi.univie.ac.at/",
                banner => "$server_static/pictures/banner_final.png",
                serveradress => "$server",
                introduction => "introduction.html",
                available_genomes => "$available_genomes",
                target_search => "$server",
                staticcontentaddress => "$server_static",
		query => "$search_string",
		output=> "$output",
                help => "help.html",
		scriptfile => "template/availablegenomesscriptfile",
                stylefile => "template/availablegenomesstylefile"
        };
        my $file = "template/available_genomes_result.html";	
        $template->process($file, $vars) || die "Template process failed: $page, $search_string", $template->error(), "\n";
	
}
  
