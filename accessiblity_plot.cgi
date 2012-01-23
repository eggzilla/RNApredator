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
use File::Temp qw/tempdir tempfile/;
#get current workdirectory
my $cwd=cwd();
my $webserver_name = "RNApredator";
my $baseDIR ="/u/html/RNApredator";
#Write all Output to file at once
$|=1 ;
#Control of the CGI Object remains with webserv.pl, additional functions are defined in the requirements below.
use CGI;
$CGI::POST_MAX=15000000; #max 15mb posts
my $query = CGI->new;
#using template toolkit to keep static stuff and logic in seperate files
use Template;


######STATE - variables##########################################
#determine the query state by retriving CGI variables
#$page if=0 then input, if=1 then calculate and if=2 then output
#available_genomes can call RNApredator via CGI therfore
#$tax_id has to be taintchecked
#my @parameters = $query->param();
my $page_input = $query->param('page') || undef; 
my $tempdir_input = $query->param('tempdir') || undef;
my $fasta_file_input= $query->param('s') || undef;
my $b_input =  $query->param('b') || undef;
my $e_input = $query->param('e') || undef;

######TAINT-CHECKS##############################################
#get the current page number
#wenn predict submitted wurde ist page 
my $page;
if(defined($page_input)){
	if($page_input == 1){
		$page = 1;
	}else{
		$page = 0;
	}
}else{
	$page = 0;
}


#tempdir taint check ... needs to be a foldername from /u/html/RNApredator
my $tempdir;
if(defined($tempdir_input)){
        if(-e "/u/html/RNApredator/$tempdir_input"){
            $tempdir = $tempdir_input;    
        }
}else{
        $tempdir = "";
}

#check s argument
my $fasta_file;
my $fasta_file_with_extension;
if(defined($tempdir_input)){
        if(-e "/u/html/RNApredator/$tempdir/$fasta_file_input.fasta"){
            	$fasta_file = "$fasta_file_input";
	    	$fasta_file_with_extension="$fasta_file_input.fasta";	
        }
}else{
        $fasta_file = "";
}

#check b argument(begin coordinates of interaction)
my $begin_coordinate;
my $begin_coordinate_length = length($b_input);
if(defined($b_input)){
        if($begin_coordinate_length>10){
       		$begin_coordinate="undef";    
        }elsif($b_input =~ /^\d+/){
		$begin_coordinate=$b_input;
	}
}else{
        $begin_coordinate = undef;
}

#check e argument(end coordinate of interaction)
my $end_coordinate;
my $end_coordinate_length = length($e_input);
if(defined($e_input)){
        if($end_coordinate_length>10){
                $end_coordinate="undef";
        }elsif($e_input =~ /^\d+/){
                $end_coordinate=$e_input;
        }
}else{
        $end_coordinate = undef;
}

######CALCULATE##################################################
#Once user-input is read start search process and show progress bar
if($page == 0){
		print $query->header();
	$ENV{PATH} = "$baseDIR/$tempdir/:/usr/bin/:/u/html/RNApredator2:/bin/:/u/html/RNApredator2/executables";
	#print commands.sh which contains the next orders
	#FORK here
	if (my $pid = fork) {
		$query->delete_all();
		#send user to result page
                print"<script type=\"text/javascript\">
                          window.location = \"http://rna.tbi.univie.ac.at/RNApredator2/accessiblity_plot.cgi?page=1&s=$fasta_file&b=$begin_coordinate&e=$end_coordinate&tempdir=$tempdir\";
                         </script>";
                
	}elsif (defined $pid){		
		close STDOUT;
		open (COMMANDS, ">$baseDIR/$tempdir/commands2.sh") or die "Could not create commands.sh";
		print COMMANDS "#!/bin/bash\n" or die "Error could not print commands2.sh - $!";
		print COMMANDS "cd $baseDIR/$tempdir/; rm -rf *.R\n" or die "Error could not print commands2.sh - $!";
		print COMMANDS "cd $baseDIR/$tempdir/; /u/html/RNApredator2/executables/accessibility_analysis_batch.pl -s $fasta_file_with_extension -b $begin_coordinate -e $end_coordinate -d -30  -f 30\n" or die "Error could not print commands2.sh - $!";
		close COMMANDS;
		chmod (0755,"$baseDIR/$tempdir/commands2.sh");
		exec "cd $baseDIR/$tempdir; ./commands2.sh" or die "Could not execute commands2.sh$!";
	}
	
}

######OUTPUT#####################################################
#Plex output list is ready for display. 
#show some basic info about microorganism from table at the top
#followed by result table with buttons for further requests
if($page == 1){
	if(-e "/u/html/RNApredator/$tempdir/$fasta_file_with_extension.png"){
	        print $query->header();
		
		print "<img src=\"http://rna.tbi.univie.ac.at/RNApredator/$tempdir/$fasta_file_with_extension.png\"><br> \n";
		print "<table border =\"1\">\n
			<tr><td>Legende:</td></tr>\n
			<tr><td><FONT COLOR=\"#FF0000\">red</FONT> line = accessibility before binding of sRNA </td>\n</tr>\n
			<tr><td><FONT COLOR=\"#008000\">green</FONT> line = accessibility after binding of sRNA </td>\n</tr>\n
			<tr><td><FONT COLOR=\"#000000\">black</FONT> line = accessibility after binding - before binding </td>\n</tr>\n
			<tr><td><FONT COLOR=\"#0000FF\">blue</FONT> line = delimiting the target region </td></tr>\n
			<tr><td><FONT COLOR=\"#00FFFF\">cyan</FONT> line = position of the start codon </td></tr>\n
		</tr>
		</table>\n
			";
		
	}else{
		print $query->header();	
		print "Calculating Plot.. this can take some minutes.<br>";
		print "You can bookmark this <a href=\"http://rna.tbi.univie.ac.at/RNApredator2/accessiblity_plot.cgi?page=1&s=$fasta_file&b=$begin_coordinate&e=$end_coordinate&tempdir=$tempdir\">link</a> and return later";
		sleep(10);
                print"<script type=\"text/javascript\">
                        window.location = \"http://rna.tbi.univie.ac.at/RNApredator2/accessiblity_plot.cgi?page=1&s=$fasta_file&b=$begin_coordinate&e=$end_coordinate&tempdir=$tempdir\"; 
			</script>";
                }
}
