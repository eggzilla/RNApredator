#!/usr/bin/perl
#Main executable of the RNAPlex webserver 
use warnings;
use strict;
use diagnostics;
use utf8;
use Data::Dumper;
use Pod::Usage;
use IO::String;
use Bio::SeqIO;
use Cwd;
use CGI::Carp qw(fatalsToBrowser);
my $source_dir=cwd();
#Control of the CGI Object remains with webserv.pl, additional functions are defined in the requirements below.
use CGI;
$CGI::POST_MAX=15000000; #max 15mb posts
my $query = CGI->new;
#using template toolkit to keep static stuff and logic in seperate files
use Template;

#Reset these absolut paths when changing the location of the requirements
#functions for genome selection
require "$source_dir/executables/available_genomes.pl";

######STATE - variables##########################################
#determine the query state by retriving CGI variables
#$page if =0 then input, if =1 then calculate and if =2 then output
my $page = $query->param('page') || "0"; #
my $search_string = $query->param('query') || "";

######INPUT######################################################
#Print HTTP-Header for input-page

if($page eq "0"){
	print $query->header();
	
	my $template = Template->new({
  	  	# where to find template files
    		INCLUDE_PATH => ['./template'],
		#Interpolate => 1 allows simple variable reference
		#INTERPOLATE=>1,
		#allows use of relative include path
		RELATIVE=>1,
	});

	my $file = './template/available_genomes.html';
	my $vars = {
   		title => "RNApredator bacterial sRNA target prediction Webserver - Available Genomes",
	   	tbihome => "http://www.tbi.univie.ac.at/",
		banner => "./pictures/banner_final.png",
		introduction => "introduction.html",
	        available_genomes => "available_genomes.cgi",
	        target_search => "target_search.cgi",
	        help => "help.html"
	};
	$template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
}

######SEARCH-RESULT#####################################################

if($page eq "1"){
	my $output = output($search_string);
        print $query->header();
        my $template = Template->new({
                # where to find template files
                INCLUDE_PATH => ['./template'],
                #Interpolate => 1 allows simple variable reference
                #INTERPOLATE=>1,
                #allows use of relative include path
                RELATIVE=>1,
        });

        my $file = './template/available_genomes_result.html';
        my $vars = {
                title => "RNApredator bacterial sRNA target prediction Webserver - Available Genomes",
                tbihome => "http://www.tbi.univie.ac.at/",
                banner => "./pictures/banner_final.png",
                introduction => "introduction.html",
                available_genomes => "available_genomes.cgi",
                target_search => "target_search.cgi",
		query => "$search_string",
		output=> "$output",
                help => "help.html"
        };
        $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
	
}
  
sub output(){
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
			$output=$output."<tr><td>$fields[0]</td><td>$fields[1]</td><td><a href=\"http://rna.tbi.univie.ac.at/RNApredator2/target_search.cgi?id=$fields[1]\">Link</a></td></tr>";
                
        }
	if($output eq ""){
		$output=$output."<tr><td colspan=\"3\"><u>no match found</u></td></tr>";
	}
	$return_value="$header"."$output";
	return "$return_value";
}
