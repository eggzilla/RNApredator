#!/usr/bin/perl
#functional,.. but data is inconsistent... child nodes are missing
#example 75560
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
