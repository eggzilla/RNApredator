#!/usr/bin/perl
use strict;
use CGI::Carp qw(fatalsToBrowser);
use CGI;
use Cwd;
my $source_dir=cwd();
my $cgi_query = CGI->new;
#Data files have following format:
#output format: name, id, type, rank/dna type
#Request has this format:
#NAME: id PARAMETER: 2
print $cgi_query->header();
#print $cgi_query->start_html;
#print "Content-Type: text/html\n\n";
my $query_input = $cgi_query->param('file') || undef;
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
	       print "<p>output!</p>";
}
print "<p>output!</p>";
#Example output:
#	print "{
#			query:'Li',
# 			suggestions:['Liberia','Libyan Arab Jamahiriya','Liechtenstein','Lithuania'],
#		 	data:['LR','LY','LI','LT']
# 		}";
