#!/usr/bin/perl
#Main executable of the RNAPlex webserver 
#use warnings;
use strict;
#use diagnostics;
use utf8;
use File::Copy;
use Data::Dumper;
use Pod::Usage;
use IO::String;
use Bio::SeqIO;
use Cwd;
use Digest::MD5;
use CGI::Carp qw(fatalsToBrowser);
use File::Temp qw/tempdir tempfile/;
use Sys::Hostname;

######################### Webserver machine specific settings ############################################
##########################################################################################################

#Set host specific variables according to hostname
my $host = hostname;
my $webserver_name = "RNApredator";
my $source_dir=cwd();
my $server;
#baseDIR points to the tempdir folder
my $base_dir;
if($host eq "erbse"){
    $server="http://localhost:800/RNApredator";
    $base_dir ="$source_dir/html";
}elsif($host eq "linse"){
    $server="http://rna.tbi.univie.ac.at/RNApredator2";
    $base_dir ="/u/html/RNApredator";
}else{
#if we are not on erbse or on linse we are propably on rna.tbi.univie.ac.at anyway
    $server="http://rna.tbi.univie.ac.at/RNApredator2";
    $base_dir ="/u/html/RNApredator";
}

#sun grid engine settings
my $qsub_location="/usr/bin/qsub";
my $sge_queue_name="web_short_q";
my $sge_error_dir="$base_dir/error";
my $sge_log_output_dir="$base_dir/error";
my $accounting_dir="$base_dir/accounting";
my $sge_root_directory="/usr/share/gridengine";
##########################################################################################################
#Write all Output to file at once
$|=1;
#Control of the CGI Object remains with webserv.pl, additional functions are defined in the requirements below.
use CGI;
$CGI::POST_MAX=100000; #max 100kbyte posts
my $query = CGI->new;
#using template toolkit to keep static stuff and logic in seperate files
use Template;

#Reset these absolut paths when changing the location of the requirements
#functions for gathering user input
require "$source_dir/executables/input.pl";
#functions for calculating of results
require "$source_dir/executables/calculate.pl";
#funtions for output of results
require "$source_dir/executables/output.pl";

######STATE - variables##########################################
#determine the query state by retriving CGI variables
#$page if=0 then input, if=1 then calculate and if=2 then output
#available_genomes can call RNApredator via CGI therfore
#$tax_id has to be taintchecked
my $id_input = $query->param('id') || undef; #from available_genomes.cgi - contains either accession_number or tax-id
my $tax_id_input = $query->param('tax-id') || undef;
my $accession_number_input = $query->param('accession') || undef; 
my $page = $query->param('page') || undef; 
my $sRNA_input = $query->param('sRNA-submit') || undef;
my $predict_input = $query->param('submit') || undef;
my $top_input = $query->param('top') || undef;
my $tempdir_input = $query->param('tempdir') || undef;
my $begin_check = $query->param('begincheck')|| undef;
my @names = $query->param;
my $email=$query->param('email-address')|| undef;
my $sRNA_input_filename=$query->param('fasta-file')|| undef;
my $sRNA_input_filehandle=$query->upload('fasta-file')||undef;
my $tempdir_array_input=$query->param('tempdir_array')|| undef;
my $suboptimal_toggle_input=$query->param('suboptimal_toggle')|| undef;

sub check_fasta(){
    my $inputstring=shift;
    $inputstring =~ s/\r/\n/g;
    #print STDERR "Check-fasta Input-string:$inputstring\n";
    my $is_ok=1;
    my $is_fasta=1;
    my $sRNA_number=0;
    my $validation_message;
    my @return_array;
    my @sRNA_input_splits;
    if($inputstring=~/>/g){
	$is_fasta=1;
	$validation_message=$validation_message."Fasta-Format detected:<br>";
	@sRNA_input_splits=split(/>/,$inputstring);
	$sRNA_number= scalar @sRNA_input_splits -1;
	if($sRNA_number>5){
	    $validation_message=$validation_message."sRNA fasta-file must not contain more than 5 sequences<br>";
	    $is_ok=0;
	}
	#print STDERR "sRNA-splits:@sRNA_input_splits";
	shift(@sRNA_input_splits);
	my $input_sequence_number=1;
	foreach my $sRNA_split (@sRNA_input_splits){
	    #now we have the different entries, we split them again by linebreak
	    my @sRNA_entry=split(/\n/,$sRNA_split);
	    #print STDERR "sRNA-Entry:@sRNA_entry\n";
	    #get the header
	    my $entry_header=shift(@sRNA_entry);
	    #atm we throw header away
	    #print STDERR "sRNA-header:$entry_header\n";
	    #have a look if we find unwanted chars in the header
	    #if($entry_header=~/test/g){
	    #		my @match_array;
	    #		while ($entry_header =~ /test/g){
	    #			print STDERR "match: $&";
	    #			push(@match_array, $&);	
	    #		}
	    #		print STDERR "found unwanted chars in fasta_header: @match_array\n";
	    #		my $join_match_array= join(",", @match_array);
	    #		$is_ok=0;
	    #		$validation_message=$validation_message."sRNA #$input_sequence_number header: contains invalid characters:$join_match_array<br>";
	    #}
	    my $header_index=2*$input_sequence_number+1;
	    my $sequence_index=2*$input_sequence_number+2;
	    $return_array[$header_index]="sRNA$input_sequence_number";
	    #join the sequence fragments without linebreaks
	    my $sRNA_sequence=join("",@sRNA_entry);
	    #remove whitespaces from sequence
	    $sRNA_sequence=~s/\s+//g;
	    if(length($sRNA_sequence)<5){
		$is_ok=0;
		$validation_message=$validation_message."sRNA #$input_sequence_number sequence: too short, has to be >4 letters<br>";	
	    }
	    #check if we find unwanted characters in the sequence
	    if($sRNA_sequence=~m/[^GTCUA]+/gi){
		my @match_array = ($sRNA_sequence=~ /[^GTCUA]+/gi);
		my $join_match_array= join(",", @match_array);
		$is_ok=0;
		$validation_message=$validation_message."sRNA #$input_sequence_number sequence: contains invalid characters, only GgTtcCuUaA allowed<br>";
	    }
	    $sRNA_sequence =~s/a/A/g;
	    $sRNA_sequence =~s/g/G/g;
	    $sRNA_sequence =~s/t/U/g;
	    $sRNA_sequence =~s/T/U/g;
	    $sRNA_sequence =~s/u/U/g;
	    $sRNA_sequence =~s/c/C/g;
	    $return_array[$sequence_index]=$sRNA_sequence;
	    $input_sequence_number++;
	}			
    }else{	
	#"just" a sequence
	$sRNA_number++;
	$inputstring=~s/\n+//g;	
	$inputstring=~s/\s+//g;
	if(length($inputstring)<5){
	    $is_ok=0;
	    $validation_message=$validation_message."sRNA sequence: too short, has to be >4 letters<br>";   
	}
	#check if we find unwanted characters in the sequence
	if($inputstring=~m/[^GTCUA]+/gi){
	    my @match_array = ($inputstring=~m/[^GTCUA]+/gi);
	    my $join_match_array= join(",", @match_array);
	    $is_ok=0;
	    $validation_message=$validation_message."sRNA sequence: contains invalid characters:$join_match_array<br>";
	}
	$inputstring=~s/a/A/g;
	$inputstring=~s/g/G/g;
	$inputstring=~s/t/U/g;
	$inputstring=~s/T/U/g;
	$inputstring=~s/u/U/g;
	$inputstring=~s/c/C/g;
	$return_array[3]="sRNA";
	$return_array[4]="$inputstring";
    }
    $return_array[0]=$is_ok;
    $return_array[1]=$validation_message;
    $return_array[2]=$sRNA_number;	
    return \@return_array;
    #we return a array reference, first field of the array containing true if the
    #provided seq/fastafile is valid and does not contain more than 5 seq.
    #the second field contains the number of sequences, followed by a field
    #for the name of the first sequence and a field for the sequence,.. and so on
    #up to 5 seq/name pairs (up to index 11)
}



#my %postprocess_input = $query->param('postprocess') || undef;
######TAINT-CHECKS##############################################
#get the current page number
#wenn predict submitted wurde ist page 1
if(defined($page)){
    if($page eq 1){
	$page = 1;
    }elsif($page eq 2){
	$page = 2;
    }elsif($page eq 3){
	$page = 3;
    }
}else{
    $page = 0;
}


#tempdir_array
my @tempdir_array;
if(defined($tempdir_array_input)){
    @tempdir_array= split(",",$tempdir_array_input);
}

#suboptimal_toggle
my $suboptimal_toggle;
if(defined($suboptimal_toggle_input)){
    if($suboptimal_toggle_input eq "on"){
	$suboptimal_toggle="on";
    }else{
	$suboptimal_toggle="off";
    }
}else{
    $suboptimal_toggle="off";
}
#top taint check can either be 10. 25 or 100
my $top;
if(defined($top_input)){
    if($top_input eq "25"){
	$top = 25;
    }elsif($top_input eq "50"){
	$top = 50;
    }elsif($top_input eq "75"){
	$top = 75;
    }elsif($top_input eq "100"){
	$top = 100;
    }elsif($top_input eq "500"){
	$top=500;
    }elsif($top_input eq "All"){
	$top="All";
    }
}else{
    $top = 100;
}

#tempdir taint check ... needs to be a foldername from $base_dir
my $tempdir;
if(defined($tempdir_input)){
    if(-e "$base_dir/$tempdir_input"){
	$tempdir = $tempdir_input;    
    }
}else{
    $tempdir = "";
}

#parsing and taintchecking of param - id, which can be handed over by available genomes.
my $accession_default = "";
my $tax_id_default = "";
my @accession_number_array;
if(defined($id_input)){
    my $id_length = length($id_input);
    if($id_length>25){
	$id_input = undef;
    }elsif($id_input =~ /^\d+/){
	#only numbers = Taxid - preset on form in taxid field
	$tax_id_default = $id_input;
    }elsif($id_input =~ /^[A-Z]+\_\d+/){
	$accession_default = $id_input;
    }elsif($id_input =~ /^[A-Z]+\_[A-Z]+\d+/){
	$accession_default = $id_input;
    }else{
	$id_input = undef;	
    }
}

#accession number from target_search
my $accession_number;
if(defined($accession_number_input)){
    my $accession_number_length = length($accession_number_input);
    if($accession_number_length>25){
	$accession_number = undef;
    }elsif($accession_number_input =~ /^[A-Z]+\_\d+/){
	$accession_number = $accession_number_input;
	push(@accession_number_array,$accession_number);
    }elsif($accession_number_input =~ /^[A-Z]+\_[A-Z]+\d+/){
	$accession_number = $accession_number_input;
	push(@accession_number_array,$accession_number);
    }else{
	$accession_number = undef;
    }
}

#tax-id from target_search
my $tax_id;
if(defined($tax_id_input)){
    my $tax_id_input_length = length($tax_id_input);
    if($tax_id_input_length>25){
	$tax_id_input = undef;
    }elsif($tax_id_input =~ /^\d+/){
	#only numbers = Taxid - preset on form in taxid field
	$tax_id = $tax_id_input;
	# get accession array - created with csv_to_tax_id_child_accession_number_csv_converter.pl
	# read from file - /data/tax_accession_children.csv
	open (IN, "<$source_dir/data/lists/input_lists/tax_accession_children.csv") or die "No Input List found";
	my @lines;
	while(<IN>){
	    push(@lines,$_);
	}
	foreach(@lines){
	    chomp($_);
	    my @fields = split /\;/;
	    #first get the tax_id for each line
	    my $tax_id_field = $fields[0];
	    if($tax_id_field == $tax_id){
		shift @fields;
		foreach my $field(@fields){
		    $field =~ s/ //;
		    push(@accession_number_array,$field);
		}
	    }         
	}
    }else{
	$tax_id = undef;
    }
}
#sRNA from target_search
#if there is a sRNAfile for this folder we read from there
my $sRNA;
my @sRNA_tempdir_file_array;
if(-e "$base_dir/$tempdir/sRNA.fasta"){
    open(SRNA, "<$base_dir/$tempdir/sRNA.fasta") or die("Could not open");
    while(<SRNA>) {
	chomp;
	push(@sRNA_tempdir_file_array, $_);
    }
    $sRNA=join("",@sRNA_tempdir_file_array);
}

#postprocess - list of ids
#parse @names for entries postprocess[1-100]
my @postprocess_selected;
my $postprocess_value;
foreach my $name(@names){
    if($name =~ m/p/){
	#check value
	$postprocess_value = $query->param("$name");
	if (($postprocess_value =~ m/[0-9]+\-[0-9]+/)&&(length($postprocess_value)<250)){
	    push(@postprocess_selected, $postprocess_value);
	}
    }
}

#begincheck - check if its neccessary to delete begin2 and done2 at beginning of page=3
if(defined($begin_check)){
    if($begin_check eq 1){
	$begin_check = 1;
    }
}else{
    $begin_check=undef;
}

#############sRNA-Input################################
#First process sRNA-Input
#If we have a file we check it for correctess (if not we return to page=0 with error message), 
#otherwise we contine with the sRNA-Input
my @parsed_array;
my $errorscript="";
#print STDERR "Got_here_lastest:sRNAinputfilename:!$sRNA_input_filename!:sRNA_input:!$sRNA_input!\n";
if($page==1){
    #print STDERR "sRNAinputfilename:!$sRNA_input_filename!\n";
    if(defined($sRNA_input_filename)){
	#if the file does not meet requirements we delete it before returning to page0 for error
	my $name = Digest::MD5::md5_base64(rand);
	$name =~ s/\+/_/g;
	$name =~ s/\//_/g;
	my $uploaddir="$base_dir/test/";
	unless(-e "$base_dir/test/"){
            mkdir("$uploaddir");
	}
	#my $io_handle = $sRNA_input_filehandle->handle;
	#open (OUTFILE,'>',"$base_dir/test/$name");
	#my $buffer;
	#my $bytesread;
	#while ($bytesread = $io_handle->read($buffer,1024)) {
	#  print OUTFILE $buffer;
	#}
	open ( UPLOADFILE, ">$uploaddir/$name" ) or die "$!"; binmode UPLOADFILE; while ( <$sRNA_input_filehandle> ) { print UPLOADFILE; } close UPLOADFILE;
	my $check_size = -s "$uploaddir/$name";
	my $max_filesize =10000;
	if($check_size < 1){
	    print STDERR "RNApredator: Uploaded Input file is empty\n";
	}elsif($check_size > $max_filesize){
	    print STDERR "RNApredator: Uploaded Input file is too large\n";
	}
	#now check for fasta format
	open (SRNAINPUTFILE, "<$uploaddir/$name") or die "No Input List found";
	my @srna_file_lines;
	while(<SRNAINPUTFILE>){
	    push(@srna_file_lines,$_);
	}
	#print STDERR "srna_file_lines:@srna_file_lines\n";
	my $srna_joined_file=join("",@srna_file_lines);
	#print STDERR "RNApredator Input-file: $srna_joined_file\n";
	my $parsed_array_reference=&check_fasta($srna_joined_file);
	@parsed_array=@$parsed_array_reference;
	#print STDERR "Parsed Array:@parsed_array\n";
	
    }elsif(defined($sRNA_input)){
	#print STDERR "Got here3\n";
	#parse fasta and go to page 1 for one sequence and to page 4 for multiple
	my $parsed_array_reference=&check_fasta($sRNA_input);
	@parsed_array=@$parsed_array_reference;
	#print STDERR "Parsed Array:@parsed_array\n";
    }else{
	print STDERR "RNApredator:No sRNA input provided\n";
    }
}

if(@parsed_array){
    #if isok is true
    #print STDERR Dumper(@parsed_array);
    if($parsed_array[0]){
	#hand over values for further processing
	#if we have one sequence we proceed as planed
	#if we have several sequences we go to new page 4 and start a search for every entry
	if($parsed_array[2]>1){
	    $page="4";
	    #hand over $sRNA in the loop
	}else{
	    $page=1;
	    #set $sRNA to the first sequence
	    $sRNA=$parsed_array[4];
	}
    }else{
	if(defined($accession_number)){
	    #return to page=0 with errormessage
	    $page="0";
	    my $error_message=$parsed_array[1];
	    $errorscript="<script type=\"text/javascript\">
			\$(document).ready(function(){
               		 var accession =\"$accession_number\";
               		 var sRNA_seq =\"\";
                	//set accession field and trigger eventhandler
                	var accession_field = document.getElementById(\"accession_id\");
                	accession_field.value=accession;
                	accession_field.onkeyup(accession_field);
                	document.getElementById(\"step2_confirm\").onclick();
			document.getElementById(\"file_message\").innerHTML=\"$error_message\";
                	document.getElementById(\"sRNA-Input\").value=sRNA_seq;
                	});
			</script>";
	}else{
	    #return to page=0 with errormessage
	    $page="0";
	    my $error_message=$parsed_array[1];
	    $errorscript="<script type=\"text/javascript\">
                        \$(document).ready(function(){
                         var taxid =\"$tax_id\";
                         var sRNA_seq =\"\";
                        //set taxid field and trigger eventhandler
                        var taxidfield = document.getElementById(\"tax-id\");
                        taxidfield.value=taxid;
                        taxidfield.onkeyup(taxidfield);
                        document.getElementById(\"step2_confirm\").onclick();
                        document.getElementById(\"file_message\").innerHTML=\"$error_message\";
                        document.getElementById(\"sRNA-Input\").value=sRNA_seq;
                        });
                        </script>";	
	}
    }
}

#document.getElementById(\"file_message\").innerHTML=\"<font color=\"#FF0000\">$error_message</font>\";

######CALCULATE-Multiple##################################################
#Once user-input is read start search process and show progress bar
#Interface variables from input are $tax_id, $sRNA_string
if($page==4){
    #if $tax_id is set $accessionnumber is set to undef
    if(defined($tax_id)){$accession_number=undef;}
    print $query->header();
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	RELATIVE=>1,
				 });
    
    my $file = './template/calc.html';
    #if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
    my $vars = {
	title => "RNApredator bacterial sRNA target prediction Webserver - Calculation",
	tbihome => "http://www.tbi.univie.ac.at/",
	banner => "./pictures/banner_final.png",
	introduction => "introduction.html",
	available_genomes => "available_genomes.cgi",
	target_search => "target_search.cgi",
	help => "help.html",
	accession_default => "$accession_default",
	tax_id_default => "$tax_id_default",
	java_script_location  => "./javascript/calculate.js",
	scriptfile => "calculationscriptfile",
	stylefile => "calculationstylefile" 
    };
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
    #process parsed array here we need to loop once for each sRNA and then redirect to page=5
    my $number_of_sRNAs=$parsed_array[2];
    #print STDERR "######################################PREDATOR-DEBUG:"; 
    #print STDERR "number_of_sRNAs:$number_of_sRNAs\n";
    my $sRNA_count=0;
    for($sRNA_count;$sRNA_count<$number_of_sRNAs; $sRNA_count++){
	#retrieve sRNA!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	$sRNA=$parsed_array[2*($sRNA_count+1)+2];
	$tempdir = tempdir ( DIR => $base_dir );
	#print STDERR "Tempdir:$tempdir, sRNA-seq:$sRNA\n";
	$tempdir =~ s/$base_dir\///;
	chmod 0755, "$base_dir/$tempdir";
	push(@tempdir_array,$tempdir);
	#print"- folder created<br>";
	open(SRNA, ">$base_dir/$tempdir/sRNA.fasta") or die("Could not open");
	#upper bound for -u argument of RNAup must not exceed string length
	my $sRNA_length = length($sRNA);
	my $u_argument_upperbound = "40";
	if($sRNA_length =~ /^[0-9]/){
	    if($sRNA_length<40){
		$u_argument_upperbound = $sRNA_length;
	    }
	}
	print SRNA ">sRNA\n"."$sRNA";
	close SRNA;
	#add to path or taintcheck will complain
	$ENV{PATH} = "$base_dir/$tempdir/:/usr/bin/:$source_dir/:/bin/:$source_dir/executables";
	#print commands.sh which contains the next orders
	open (COMMANDS, ">$base_dir/$tempdir/commands.sh") or die "Could not create comments.sh";
	#TODO send to sge
	#calculate sRNA accessiblity
	print COMMANDS "#!/bin/bash\n";
	#print COMMANDS "cd $base_dir/$tempdir/; RNAplfold -O 1-$u_argument_upperbound <$base_dir/$tempdir/sRNA.fasta;\n";
	print COMMANDS "cd $base_dir/$tempdir/; $source_dir/executables/RNAup -u 1-$u_argument_upperbound <$base_dir/$tempdir/sRNA.fasta;\n";
	print COMMANDS "mv sRNA_u1*.out sRNA_u1_to_$u_argument_upperbound.out;\n";
	print COMMANDS "$source_dir/executables/hakim_convert_up_to_plfold.sh $base_dir/$tempdir/sRNA_u1_to_$u_argument_upperbound.out;\n";
	#PREDICTION
	#this part is run once in case of submitted accession number or for submitted tax_id for every child accession number
	#FORK here and hand over tempdir names for page 5
    }
    my $tempdir_submit_array=join(",",@tempdir_array);
    if (my $pid = fork) {
	$query->delete_all();
	#send user to result page
	if(defined $tax_id){
	    print"<script type=\"text/javascript\">
	                          window.location = \"$server/target_search.cgi?page=5&tax-id=$tax_id&tempdir_array=$tempdir_submit_array\";
	                         </script>";
	}else{
	    print"<script type=\"text/javascript\">
	                        window.location = \"$server/target_search.cgi?page=5&accession=$accession_number&tempdir_array=$tempdir_submit_array\";
	                       </script>";
	}
	close COMMANDS; #close COMMANDS so child can reopen filehandle
	#print STDERR Dumper(@tempdir_array);
    }elsif (defined $pid){
	#exec_command 
	my $exec_command="export SGE_ROOT=$sge_root_directory;";
	#we loop again once for each sRNA
	close STDOUT;
	my $sRNA_count2=0;
	for($sRNA_count2; $sRNA_count2<$number_of_sRNAs; $sRNA_count2++){
	    #retrieve tempdir
	    $tempdir=$tempdir_array[$sRNA_count2];
	    #print STDERR "2.Using tempdir:$tempdir";
	    #retrieve sRNA
	    my $sRNA_index_number=(2*($sRNA_count2+1))+2;
	    $sRNA=$parsed_array[$sRNA_index_number];
	    open (COMMANDS, ">>$base_dir/$tempdir/commands.sh") or die "Could not create comments.sh";
	    #prepare mRNAaccessiblitites
	    mkdir("$base_dir/$tempdir/accessibilites/",0744);
	    my $mRNA_accessibility_root_path ="$source_dir/data/mRNA_accessiblities/all/";
	    #create link to sRNA accessiblity in mRNAaccessiblity folder
	    my $query = "$base_dir/$tempdir/sRNA.fasta";
	    ## run plex prediction
	    my $run=1;
	    my $interaction_length;
	    my $sRNA_length = length($sRNA);
	    if($sRNA_length>30){
		$interaction_length=30;
	    }else{
		$interaction_length=$sRNA_length-1;
	    }
	    my $total_mRNA_counter=0;
	    foreach my $accession_number_entry(@accession_number_array){
		#RNAplex accepts only one folder for all accessibilites (sRNA/mRNA) 
		#create a temporary accessiblity folder containing symlinks to sRNA and mRNA needed
		my $mRNA_accessiblity_path = $mRNA_accessibility_root_path . "$accession_number_entry/accessiblity/";
		mkdir("$base_dir/$tempdir/accessibilites/$accession_number_entry",0744);
		my @count_files=<$mRNA_accessiblity_path/*>;
		my $file_count =@count_files;
		$total_mRNA_counter+=$file_count;
		my $target = "$source_dir/data/ftn_all_species_Final/"."$accession_number_entry.ftn";
		print COMMANDS "cd $mRNA_accessiblity_path; for file in *; do cp -s $mRNA_accessiblity_path\$file $base_dir/$tempdir/accessibilites/$accession_number_entry/\$file; done\n";
		print COMMANDS "cd $base_dir/$tempdir/;\n";
		print COMMANDS "cp -s $base_dir/$tempdir/sRNA_openen $base_dir/$tempdir/accessibilites/$accession_number_entry/sRNA_openen;\n";
		if($run==1){
		    if($suboptimal_toggle eq "on"){
			print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -z 20 -e -8 -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >prediction.res;\n";
		    }else{
			print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >prediction.res;\n";
		    }
		    $run ++;
		}else{
		    if($suboptimal_toggle eq "on"){
			print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -z 20 -e -8 -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >>prediction.res;\n";
		    }else{
			print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >>prediction.res;\n";
		    }
		}
	    }
	    #write total_mRNA_counter to file
	    open (TOTALMRNACOUNTER, ">$base_dir/$tempdir/total_mRNA_counter") or die "Could not create total_mRNA_counter";
	    print TOTALMRNACOUNTER "$total_mRNA_counter";
	    close TOTALMRNACOUNTER;
	    print COMMANDS "$source_dir/executables/plex_to_html.pl $tempdir $base_dir;\n";
	    print COMMANDS "touch done;\n";
	    close COMMANDS;
	    chmod (0755,"$base_dir/$tempdir/commands.sh");
	    my $ip_adress=$ENV{'REMOTE_ADDR'};
	    $ip_adress=~s/\.//g;
	    my ($sec,$min,$hour,$day,$month,$yr19,@rest) = localtime(time);
	    my $timestamp=(($yr19+1900)."-".sprintf("%02d",++$month)."-".sprintf("%02d",$day)."-".sprintf("%02d",$hour).":".sprintf("%02d",$min).":".sprintf("%02d",$sec));
	    #write report to accounting file
	    open(ACCOUNTING, ">>$accounting_dir/accounting") or die "Could not write to accounting file: $!/n";
	    #ipaddress tempdir timestamp querynumber suboptimal_toggle
	    print ACCOUNTING "$ip_adress $tempdir $timestamp $number_of_sRNAs $suboptimal_toggle\n";
	    close ACCOUNTING;
	    $exec_command=$exec_command." $qsub_location -N IP$ip_adress -q $sge_queue_name -e $sge_error_dir  -o $source_dir/error  $base_dir/$tempdir/commands.sh >$base_dir/$tempdir/Jobid;";	
	}
	#send all jobs to the queue 
	exec "$exec_command" or die print STDERR "RNApredator: calculate multiple failed: $!";
    }
    
}

######INPUT######################################################
#Print HTTP-Header for input-page
if($page == 0){
    print $query->header();
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	#Interpolate => 1 allows simple variable reference
	#INTERPOLATE=>1,
	#allows use of relative include path
	RELATIVE=>1,
				 });

    my $file = './template/input.html';
    #if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
    my $vars = {
	title => "RNApredator bacterial sRNA target prediction Webserver - Input form",
	tbihome => "http://www.tbi.univie.ac.at/",
	banner => "./pictures/banner_final.png",
	introduction => "introduction.html",
	available_genomes => "available_genomes.cgi",
	target_search => "target_search.cgi",
	help => "help.html",
	accession_default => "$accession_default",
	tax_id_default => "$tax_id_default",
	#errorscript is a short javascript that returns the errormessage from parsing the fasta-file on the client side
	error_script => "$errorscript",
	java_script_location  => "./javascript/input.js",
	scriptfile => "inputscriptfile",
	stylefile => "inputstylefile"
    };
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
}
#The species or the Plasmid is selected by ta_id which is later translated by calculate to the corresponding accession number

######CALCULATE##################################################
#Once user-input is read start search process and show progress bar
#Interface variables from input are $tax_id, $sRNA_string
if($page==1){
    #if $tax_id is set $accessionnumber is set to undef
    if(defined($tax_id)){$accession_number=undef;}
    print $query->header();
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	#Interpolate => 1 allows simple variable reference
	#INTERPOLATE=>1,
	#allows use of relative include path
	RELATIVE=>1,
				 });
    
    my $file = './template/calc.html';
    #if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
    my $vars = {
	title => "RNApredator bacterial sRNA target prediction Webserver - Calculation",
	tbihome => "http://www.tbi.univie.ac.at/",
	banner => "./pictures/banner_final.png",
	introduction => "introduction.html",
	available_genomes => "available_genomes.cgi",
	target_search => "target_search.cgi",
	help => "help.html",
	accession_default => "$accession_default",
	tax_id_default => "$tax_id_default",
        java_script_location  => "./javascript/calculate.js",
	scriptfile => "calculationscriptfile",
	stylefile => "calculationstylefile"
    };
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";	
    #print "Input: <br> <br> Accession Number - $accession_number <br> Tax-id - $tax_id <br> sRNA - $sRNA <br> page - $page <br><br>";
    #get all relevant accession numbers
    #case accession_number submitted..done
    #case tax_id push accession numbers on accession array
    ## create temp folder /in /u/html/www
    #File::Temp code by agruber
    $tempdir = tempdir ( DIR => $base_dir );
    $tempdir =~ s/$base_dir\///;
    chmod 0755, "$base_dir/$tempdir";
    #print"- folder created<br>";
    open(SRNA, ">$base_dir/$tempdir/sRNA.fasta") or die("Could not open");
    #upper bound for -u argument of RNAup must not exceed string length
    my $sRNA_length = length($sRNA);
    my $u_argument_upperbound = "40";
    if($sRNA_length =~ /^[0-9]/){
	if($sRNA_length<40){
	    $u_argument_upperbound = $sRNA_length;
	}
    }
    print SRNA ">sRNA\n"."$sRNA";
    close SRNA;
    #add to path or taintcheck will complain
    $ENV{PATH} = "$base_dir/$tempdir/:/usr/bin/:$source_dir/:/bin/:$source_dir/executables";
    #print commands.sh which contains the next orders
    open (COMMANDS, ">$base_dir/$tempdir/commands.sh") or die "Could not create comments.sh";	
    #TODO send to sge
    #calculate sRNA accessiblity
    print COMMANDS "#!/bin/bash\n";
    #print COMMANDS "cd $base_dir/$tempdir/; RNAplfold -O 1-$u_argument_upperbound <$base_dir/$tempdir/sRNA.fasta;\n";
    print COMMANDS "cd $base_dir/$tempdir/; $source_dir/executables/RNAup -u 1-$u_argument_upperbound <$base_dir/$tempdir/sRNA.fasta;\n";
    print COMMANDS "mv sRNA_u1*.out sRNA_u1_to_$u_argument_upperbound.out;\n";    
    print COMMANDS "$source_dir/executables/hakim_convert_up_to_plfold.sh $base_dir/$tempdir/sRNA_u1_to_$u_argument_upperbound.out;\n";
    #`cd $base_dir/$tempdir/; RNAplfold -O 1-$u_argument_upperbound <$base_dir/$tempdir/sRNA.fasta`;
    #`cd $base_dir/$tempdir/; ~ronny/WORK/ViennaRNA/Progs/RNAup -u 1-$u_argument_upperbound <$base_dir/$tempdir/sRNA.fasta >$base_dir/$tempdir/sRNA.log;
    # /scratch2/egg/webserv/executables/hakim_convert_up_to_plfold.sh *.out`;
    #print"outfile produced";
    #PREDICTION
    #this part is run once in case of submitted accession number or for submitted tax_id for every child accession number
    #FORK here
    if (my $pid = fork) {
	$query->delete_all();
	#send user to result page
	#redirect 
	if(defined $tax_id){
	    print"<script type=\"text/javascript\">
                          window.setTimeout (\'window.location = \"$server/target_search.cgi?page=2&tax-id=$tax_id&sRNA=$sRNA&tempdir=$tempdir\"\', 5000);
                          //window.location = \"$server/target_search.cgi?page=2&tax-id=$tax_id&sRNA=$sRNA&tempdir=$tempdir\";
                         </script>";
	}else{
	    print"<script type=\"text/javascript\">
                        window.setTimeout (\'window.location = \"$server/target_search.cgi?page=2&accession=$accession_number&sRNA=$sRNA&tempdir=$tempdir\"\', 5000);
                        //window.location = \"$server/target_search.cgi?page=2&accession=$accession_number&sRNA=$sRNA&tempdir=$tempdir\";
                       </script>";
	}
	close COMMANDS; #close COMMANDS so child can reopen filehandle
    }elsif (defined $pid){		
	close STDOUT;
	open (COMMANDS, ">>$base_dir/$tempdir/commands.sh") or die "Could not create commands.sh";
	#prepare mRNAaccessiblitites
	mkdir("$base_dir/$tempdir/accessibilites/",0744);
	my $mRNA_accessibility_root_path ="$source_dir/data/mRNA_accessiblities/all/";
	#create link to sRNA accessiblity in mRNAaccessiblity folder
	#print COMMANDS "Accession-Array:@accession_number_array\n";
	#print COMMANDS "tax-id_input:$tax_id_input";
	my $query = "$base_dir/$tempdir/sRNA.fasta";
	## run plex prediction
	#TODO for each accession number + send to sge
	my $run=1;
	my $interaction_length;
	if($sRNA_length>30){	
	    $interaction_length=30;
	}else{	
	    $interaction_length=$sRNA_length-1;
	}
	my $total_mRNA_counter=0;
	foreach my $accession_number_entry(@accession_number_array){
	    #check if /ebi/accessionnumber.ftn.goa is present, otherwise write goa_no file in temp folder		
	    #RNAplex accepts only one folder for all accessibilites (sRNA/mRNA) 
	    #create a temporary accessiblity folder containing symlinks to sRNA and mRNA needed
	    my $mRNA_accessiblity_path = $mRNA_accessibility_root_path . "$accession_number_entry/accessiblity/";
	    my @count_files=<$mRNA_accessiblity_path/*>;
	    my $file_count =@count_files;
	    $total_mRNA_counter+=$file_count;
	    mkdir("$base_dir/$tempdir/accessibilites/$accession_number_entry",0744);
	    my $target = "$source_dir/data/ftn_all_species_Final/"."$accession_number_entry.ftn";	
	    #print COMMANDS "cp -sR $mRNA_accessiblity_path $base_dir/$tempdir/accessibilites/$accession_number_entry/";
	    #print COMMANDS "for file in $mRNA_accessiblity_path/*;\n do cp -s $mRNA_accessiblity_path/$file $base_dir/$tempdir/accessibilites/$accession_number_entry/$file done\n";
	    print COMMANDS "cd $mRNA_accessiblity_path; for file in *; do cp -s $mRNA_accessiblity_path\$file $base_dir/$tempdir/accessibilites/$accession_number_entry/\$file; done\n";
	    print COMMANDS "cd $base_dir/$tempdir/;\n";
	    print COMMANDS "cp -s $base_dir/$tempdir/sRNA_openen $base_dir/$tempdir/accessibilites/$accession_number_entry/sRNA_openen;\n";
	    if($run==1){
		if($suboptimal_toggle eq "on"){
		    print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -z 20 -e -8 -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >prediction.res;\n";
		}else{
		    print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >prediction.res;\n";
		}
		$run ++;
	    }else{
		if($suboptimal_toggle eq "on"){
		    print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -z 20 -e -8 -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >>prediction.res;\n";
		}else{
		    print COMMANDS "$source_dir/executables/RNAplex -l $interaction_length -t $target -q $query  -a $base_dir/$tempdir/accessibilites/$accession_number_entry >>prediction.res;\n";
		}
	    }
	}
	#write total_mRNA_counter to file
	open (TOTALMRNACOUNTER, ">$base_dir/$tempdir/total_mRNA_counter") or die "Could not create total_mRNA_counter";
	print TOTALMRNACOUNTER "$total_mRNA_counter";
	close TOTALMRNACOUNTER;
	print COMMANDS "$source_dir/executables/plex_to_html.pl $tempdir $base_dir;\n";
	print COMMANDS "touch done;\n";
	close COMMANDS;
	chmod (0755,"$base_dir/$tempdir/commands.sh");
	my $ip_adress=$ENV{'REMOTE_ADDR'};
	$ip_adress=~s/\.//g;
	my ($sec,$min,$hour,$day,$month,$yr19,@rest) = localtime(time);
	my $timestamp=(($yr19+1900)."-".sprintf("%02d",++$month)."-".sprintf("%02d",$day)."-".sprintf("%02d",$hour).":".sprintf("%02d",$min).":".sprintf("%02d",$sec));
	#write report to accounting file
	open(ACCOUNTING, ">>$accounting_dir/accounting") or die "Could not write to accounting file: $!/n";
	#ipaddress tempdir timestamp querynumber suboptimal_toggle
	print ACCOUNTING "$ip_adress $tempdir $timestamp 1 $suboptimal_toggle\n";
	close ACCOUNTING;
	exec "export SGE_ROOT=$sge_root_directory; $qsub_location -N IP$ip_adress -q web_short_q -e $sge_error_dir -o $sge_log_output_dir $base_dir/$tempdir/commands.sh >$base_dir/$tempdir/Jobid" or die "$!";
	#exec "cd $base_dir/$tempdir/; ./commands.sh" or die "$!";
	#analysing and displaying progress:	
	#if(defined($tax_id)){
	#print"<script type=\"text/javascript\">
	#          window.location = \"http://insulin.tbi.univie.ac.at/target_search.cgi?page=2&tax_id=$tax_id&sRNA=$sRNA&tempdir=$tempdir\";
	#         </script>";	
	#}else{
	#print"<script type=\"text/javascript\">
	#	 window.location = \"http://insulin.tbi.univie.ac.at/target_search.cgi?page=2&accession=$accession_number&sRNA=$sRNA&tempdir=$tempdir\";
	#	</script>";
	#}
	#print "Plex executed: cd $base_dir/$tempdir/; RNAplex -l 30 -t $target -q $query  -a $mRNA_accessiblity_path/accessiblity >prediction.res<br>";	
	# clean up -> in output
	#remove sRNA accessiblity link
	#`rm $mRNA_accessiblity_path/sRNA_openen`;
	#print "
	#	 \<div class=\"copyright\"\>
	#        \<hr\>
	#        	2010 TBI - \<a href=\"mailto:egg\@tbi.univie.ac.at\"\>Florian Eggenhofer\<\/a\> - last update 20. Dec 2010
	#	\<\/div\>
	#	\<\/body\>
	#	\<\/html\>
	#
	#	";
	## hand stuff over to output
    }
    
}

######OUTPUT-MULTIPLE#####################################################
#Plex output list is ready for display. 
#show some basic info about microorganism from table at the top
#followed by result table with buttons for further requests
if($page == 5){
    #we check each of the tempdirs from the array and display a list
    #when one of them is done we link to the fitting page2
    
    print $query->header(); 
    my $template = Template->new({
	# where to find template files
	INCLUDE_PATH => ['./template'],
	#allows use of relative include path
	RELATIVE=>1,
				 });
    my $file = './template/calc.html';
    #if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
    print "</table>";
    my $vars = {
	title => "RNApredator bacterial sRNA target prediction Webserver - Calculation",
	tbihome => "http://www.tbi.univie.ac.at/",
	banner => "./pictures/banner_final.png",
	introduction => "introduction.html",
	available_genomes => "available_genomes.cgi",
	target_search => "target_search.cgi",
	help => "help.html",
	accession_default => "$accession_default",
	tax_id_default => "$tax_id_default",
	java_script_location  => "./javascript/calculate.js",
	scriptfile => "calculationscriptfile",
	stylefile => "calculationstylefile"
    };
    $template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
    print "<p>This can take some minutes.</p>";
    if(defined($tax_id)){
	print "Wait for calculation to finish or return <a href=\"$server/target_search.cgi?page=5&tax-id=$tax_id&tempdir_array=$tempdir_array_input\">here</a> later.<br>";
    }else{
	print "Wait for calculation to finish or return <a href=\"$server/target_search.cgi?page=5&accession=$accession_number&tempdir_array=$tempdir_array_input\">here</a> later.<br>";
    }
    print "<br>";
    my $tempdir_progress_counter=1;
    print "<table style=\"border:1px solid #000; width:60%\";>"; #RNA, queueing status, sRNA accessiblity, RNAplex Interaction Prediction, Parsing Results, Result Page Link
    print"<tr><td style=\"width:3%\">RNA</td><td style=\"width:10%\">Queueing Status</td><td style=\"width:10%\">sRNA accessiblity</td><td style=\"width:15%\">RNAplex Interaction Prediction</td><td style=\"width:10%\">Parsing Output</td><td style=\"width:10%\">Result Page Link</td></tr>";
    foreach my $tempdir_progress(@tempdir_array){
	#Stuff for progress:    
	#Number of Genes: precalculated: lookup number in file total_mRNA_number in tmpfolder, then look how often ">sRNA" appears in the predicts.res file
	open (TOTALMRNACOUNTER, "<$base_dir/$tempdir_progress/total_mRNA_counter") or die "Could not open total_mRNA_counter";
	my @total_counter_array;
	while(<TOTALMRNACOUNTER>){
	    push(@total_counter_array,$_);
	}
	my $total_mRNA_number=shift(@total_counter_array);
	close TOTALMRNACOUNTER;
	my $mRNAs_processed=`grep sRNA $base_dir/$tempdir_progress/prediction.res | wc -l`;
	my $progress_percentage=($mRNAs_processed/$total_mRNA_number)*100;
	my $rounded_progress_percentage=sprintf("%.2f",$progress_percentage);
	my $queueing_status="";
	my $sRNA_status="";
	my $RNAplex_interaction_prediction="";
	my $parsing_results="";
	my $result_page_link="";
	if(-e "$base_dir/$tempdir_progress/commands.sh"){$queueing_status="Processing..";} 
	else {$queueing_status="<span style=\"color:#CCCCCC\">Queued</span>";}
	if(-e "$base_dir/$tempdir_progress/sRNA_openen"){$sRNA_status="Processing..";} 
	else {$sRNA_status="<span style=\"color:#CCCCCC\">-</span>";}
	if(-e "$base_dir/$tempdir_progress/prediction.res"){$sRNA_status="done"; $RNAplex_interaction_prediction="Progress: $rounded_progress_percentage%";} 
	else {$RNAplex_interaction_prediction="<span style=\"color:#CCCCCC\">-</span>";}
	if(-e "$base_dir/$tempdir_progress/top100.html"){$RNAplex_interaction_prediction="done"; $parsing_results="Processing.."; } 
	else {$parsing_results= "<span style=\"color:#CCCCCC\">-</span>";}
	if(defined($tax_id)){
	    if(-e "$base_dir/$tempdir_progress/done"){$parsing_results="done"; $queueing_status="done"; $result_page_link="<a href=\"$server/target_search.cgi?page=2&tax-id=$tax_id&tempdir=$tempdir_progress\">Link</a>";}
	    else {$parsing_results= "<span style=\"color:#CCCCCC\"><br>-</span>";}
	    print"<script type=\"text/javascript\">
                                 window.setTimeout (\'window.location = \"$server/target_search.cgi?page=5&tax-id=$tax_id&tempdir_array=$tempdir_array_input\"\', 5000);
                         </script>";
	}else{
	    if(-e "$base_dir/$tempdir_progress/done"){ $parsing_results="done"; $queueing_status="done"; $result_page_link=" <a href=\"$server/target_search.cgi?page=2&accession=$accession_number&tempdir=$tempdir_progress\">Link</a>";} 
	    else {print "<span style=\"color:#CCCCCC\">-</span>";}
	    print"<script type=\"text/javascript\">
                         window.setTimeout (\'window.location = \"$server/target_search.cgi?page=5&accession=$accession_number&tempdir_array=$tempdir_array_input\"\', 5000);
                       </script>";
	}
	#RNA, queueing status, sRNA accessiblity, RNAplex Interaction Prediction, Parsing Results, Result Page Link
	print "<tr><td>$tempdir_progress_counter</td><td>$queueing_status</td><td>$sRNA_status</td><td>$RNAplex_interaction_prediction</td><td>$parsing_results</td><td>$result_page_link</td></tr>";
	$tempdir_progress_counter++;
    }
    print"</table>";
    
}

######OUTPUT#####################################################
#Plex output list is ready for display. 
#show some basic info about microorganism from table at the top
#followed by result table with buttons for further requests
#RESULTPAGE
if($page == 2){
    if(-e "$base_dir/$tempdir/done"){
	print $query->header();
	my $template = Template->new({
	    # where to find template files
	    INCLUDE_PATH => ['./template'],
	    #Interpolate => 1 allows simple variable reference
	    #INTERPOLATE=>1,
	    #allows use of relative include path
	    RELATIVE=>1,
				     });
	my $file = './template/results.html';
	#calculate appropriate dropmenu
	#get number of interactions and selected number of top interaction	
	open(IANUMBER, "<$base_dir/$tempdir/interactionnumber");
	my $interactionnumber;
	my $drop_menu_number;
	while(<IANUMBER>){
	    $interactionnumber=$_;
	}
	#READ Srna from file
	my $filter="";
	if($top eq "All"){
	    $filter = "- binding site filter not available for all hits"
	}else{
	    $filter = "- Show only Interactions on mRNA from <input name=\"from\" id=\"fromid\" type=\"text\" size=\"4\" onkeyup=\"filter(this)\" > to <input name=\"to\" id=\"toid\" size=\"4\" type=\"text\"  onkeyup=\"filter(this)\"> (0=Translation - Start)";
    }
	
	if($interactionnumber<100){
	    if($top==25){
		$drop_menu_number=5;	
	    }elsif($top==50){
		$drop_menu_number=4;
	    }elsif($top==75){
		$drop_menu_number=3;
	    }elsif($top==100){
		$drop_menu_number=2;
	    }elsif($top eq "All"){
		$drop_menu_number=1;
	    }	
	}else{
	    if($top==25){
		$drop_menu_number=11;
	    }elsif($top==50){
		$drop_menu_number=10;
	    }elsif($top==75){
		$drop_menu_number=9;
	    }elsif($top==100){
		$drop_menu_number=8;
	    }elsif($top eq "500"){
		$drop_menu_number=7;
	    }elsif($top eq "All"){
		$drop_menu_number=6;
	    }
	    
	}
	my $resulthtmlfile="top".$top.".html";	
	#if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
	my $vars = {
	    title => "RNApredator bacterial sRNA target prediction Webserver - Results",
	    tbihome => "http://www.tbi.univie.ac.at/",
	    #hier weiter
	    #drop_options => "$source_dir/template/dropmenu$drop_menu_number",
	    drop_options => "dropmenu$drop_menu_number",
	    banner => "./pictures/banner_final.png",
	    introduction => "introduction.html",
	    available_genomes => "available_genomes.cgi",
	    target_search => "target_search.cgi",
	    help => "help.html",
	    filter => "$filter",
	    accession_default => "$accession_default",
	    tax_id_default => "$tax_id_default",
	    java_script_location  => "./javascript/result.js",
	    interactionnumber => "$interactionnumber",
	    top => "$top",
	    #hier weiter
	    resulttable => "./html/$tempdir/$resulthtmlfile",
	    all_predictions => "./html/$tempdir/all_predictions.csv",
	    sRNA_fasta => "./html/$tempdir/sRNA.fasta",
	    plex_output_file => "./html/$tempdir/prediction.res",
	    sRNA => "$sRNA",
	    tempdir => "$tempdir",
	    scriptfile => "resultscriptfile",
	    stylefile => "resultstylefile"
	};
	$template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
    }else{
	#PROGRESS PAGE
	print $query->header();	
	my $template = Template->new({
	    # where to find template files
	    INCLUDE_PATH => ['./template'],
	    #Interpolate => 1 allows simple variable reference
	    #INTERPOLATE=>1,
	    #allows use of relative include path
	    RELATIVE=>1,
				     });
	my $file = './template/calc.html';
	#if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
	my $vars = {
	    title => "RNApredator bacterial sRNA target prediction Webserver - Calculation",
	    tbihome => "http://www.tbi.univie.ac.at/",
	    banner => "./pictures/banner_final.png",
	    introduction => "introduction.html",
	    available_genomes => "available_genomes.cgi",
	    target_search => "target_search.cgi",
	    help => "help.html",
	    accession_default => "$accession_default",
	    tax_id_default => "$tax_id_default",
	    java_script_location  => "./javascript/calculate.js",
	    scriptfile => "calculationscriptfile",
	    stylefile => "calculationstylefile"
	};
	$template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
	if(defined($accession_number)){
	    my $accession_link="$server/target_search.cgi?"."page=$page"."&accession=$accession_number"."&sRNA=$sRNA"."&tempdir=$tempdir";
	    print "<p>Processing:</p>";
	    print "This can take some minutes.";
	    print "<br>Wait for calculation to finish or";
	    print "<br>bookmark following <a href=\"$accession_link\">link</a> and return later.";
	}else{
	    my $tax_link="";
	    print "<p>Processing:</p>";
	    print "This can take some minutes.";
	    print "<br>Wait for calculation to finish or";
	    print "<br>bookmark following <a href=\"$tax_link\">link</a> and return later.";
	}
	print "<br>";
	print "<br>Progress:<br>";
	#hier weiter - progress is not shown
	#Stuff for progress:	
	#Number of Genes: precalculated: lookup number in file total_mRNA_number in tmpfolder, then look how often ">sRNA" appears in the predicts.res file
	open (TOTALMRNACOUNTER, "<$base_dir/$tempdir/total_mRNA_counter") or die "Could not open total_mRNA_counter";
	my @total_counter_array;
	while(<TOTALMRNACOUNTER>){
	    push(@total_counter_array,$_);
	}
	# my $total_mRNA_number=shift(@total_counter_array);
	# close TOTALMRNACOUNTER;
	# my $mRNAs_processed=`grep sRNA $base_dir/$tempdir/prediction.res | wc -l`;
	# my $progress_percentage=($mRNAs_processed/$total_mRNA_number)*100;
	# my $rounded_progress_percentage=sprintf("%.2f",$progress_percentage); 
	# if(-e "$base_dir/$tempdir/commands.sh"){ print "- Writing Job Script";} else {print "<span style=\"color:#CCCCCC\">- Writing Job Script</span>";}
	# if(-e "$base_dir/$tempdir/"){ print " .. done<br>- Creating Temporary Folder";} else {print "<span style=\"color:#CCCCCC\"><br>- Creating Temporary Folder</span>";}
	#if(-e "$base_dir/$tempdir/sRNA_openen"){ print " .. done<br>- Calculating sRNA - Accessibility";} else {print "<span style=\"color:#CCCCCC\"><br>- Calculating sRNA - Accessibility</span>";}
	#if(-e "$base_dir/$tempdir/prediction.res"){ print " .. done<br>- Calculating RNAplex Interaction Prediction - Progress: $rounded_progress_percentage%";} else {print "<span style=\"color:#CCCCCC\"><br>- Calculating RNAplex Interaction Prediction</span>";}
	# if(-e "$base_dir/$tempdir/topAll.html"){ print " .. done<br>- Parsing and Extracting Top Hits";} else {print "<span style=\"color:#CCCCCC\"><br>- Parsing and Extracting Top Hits</span>";}
	# if(-e "$base_dir/$tempdir/all_predictions.csv"){ print " .. done<br>- Dumping all Hits to .csv";} else {print "<span style=\"color:#CCCCCC\"><br>- Dumping all Hits to .csv</span>";}
	#print " .. done<br>- Dumping all Hits to .csv" if -e "$base_dir/$tempdir/all_predictions.csv";
	print "<table style=\"border:1px solid #000; width:60%\";>"; #RNA, queueing status, sRNA accessiblity, RNAplex Interaction Prediction, Parsing Results, Result Page Link
	print"<tr><td style=\"width:3%\">RNA</td><td style=\"width:10%\">Queueing Status</td><td style=\"width:10%\">sRNA accessiblity</td><td style=\"width:15%\">RNAplex Interaction Prediction</td><td style=\"width:10%\">Parsing Output</td><td style=\"width:10%\">Result Page Link</td></tr>";
	#Stuff for progress:    
	#Number of Genes: precalculated: lookup number in file total_mRNA_number in tmpfolder, then look how often ">sRNA" appears in the predicts.res file
	open (TOTALMRNACOUNTER, "<$base_dir/$tempdir/total_mRNA_counter") or die "Could not open total_mRNA_counter";
	my @total_counter_array;
	while(<TOTALMRNACOUNTER>){
	    push(@total_counter_array,$_);
	}
	my $total_mRNA_number=shift(@total_counter_array);
	close TOTALMRNACOUNTER;
	my $tempdir_progress_counter=1;
	my $mRNAs_processed=`grep sRNA $base_dir/$tempdir/prediction.res | wc -l`;
	my $progress_percentage=($mRNAs_processed/$total_mRNA_number)*100;
	my $rounded_progress_percentage=sprintf("%.2f",$progress_percentage);
	my $queueing_status="";
	my $sRNA_status="";
	my $RNAplex_interaction_prediction="";
	my $parsing_results="";
	my $result_page_link="";
	if(-e "$base_dir/$tempdir/commands.sh"){$queueing_status="Processing..";} 
	else {$queueing_status="<span style=\"color:#CCCCCC\">Queued</span>";}
	if(-e "$base_dir/$tempdir/sRNA_openen"){$sRNA_status="Processing..";} 
	else {$sRNA_status="<span style=\"color:#CCCCCC\">-</span>";}
	if(-e "$base_dir/$tempdir/prediction.res"){$sRNA_status="done"; $RNAplex_interaction_prediction="Progress: $rounded_progress_percentage%";} 
	else {$RNAplex_interaction_prediction="<span style=\"color:#CCCCCC\">-</span>";}
	if(-e "$base_dir/$tempdir/top100.html"){$RNAplex_interaction_prediction="done"; $parsing_results="Processing.."; } 
	else {$parsing_results= "<span style=\"color:#CCCCCC\">-</span>";}
	if(defined($tax_id)){
	    if(-e "$base_dir/$tempdir/done"){$parsing_results="done"; $queueing_status="done"; $result_page_link="<a href=\"$server/target_search.cgi?page=2&tax-id=$tax_id&tempdir=$tempdir\">Link</a>";}
	    else {$parsing_results= "<span style=\"color:#CCCCCC\"><br>-</span>";}
	}
	print "<tr><td>$tempdir_progress_counter</td><td>$queueing_status</td><td>$sRNA_status</td><td>$RNAplex_interaction_prediction</td><td>$parsing_results</td><td>$result_page_link</td></tr>";
	
        
	print"</table>";
	if(defined($tax_id)){
	    print"<script type=\"text/javascript\">
				 window.setTimeout (\'window.location = \"$server/target_search.cgi?page=2&tax-id=$tax_id&sRNA=$sRNA&tempdir=$tempdir\"\', 5000);
                          //window.location = \"$server/target_search.cgi?page=2&tax-id=$tax_id&sRNA=$sRNA&tempdir=$tempdir\";
                         </script>";
	}else{
	    print"<script type=\"text/javascript\">
			 window.setTimeout (\'window.location = \"$server/target_search.cgi?page=2&accession=$accession_number&sRNA=$sRNA&tempdir=$tempdir\"\', 5000);
                        //window.location = \"$server/target_search.cgi?page=2&accession=$accession_number&sRNA=$sRNA&tempdir=$tempdir\";
                       </script>";
	}
    }
    
}

#####POST-PROCESSING###########################################
if($page == 3){
    #Delete Progress files from possible earlier displays of selected entries
    #done2 begin2
    #if(@postprocess_selected == 0){
    #			print  $query->header();
    #       print "No Entries selected\n<br>";
    #}
    
    if(defined($begin_check)){
	if($begin_check == 1){
	    if(-e "$base_dir/$tempdir/begin2"){
		`rm $base_dir/$tempdir/begin2`;
	    }
	    if(-e "$base_dir/$tempdir/done2"){
		`rm $base_dir/$tempdir/done2`;
	    }
	}
    }
    
    unless(-e "$base_dir/$tempdir/begin2"){
	`touch $base_dir/$tempdir/begin2`;
	print $query->header();
	my $template = Template->new({
	    # where to find template files
	    INCLUDE_PATH => ['./template'],
	    #Interpolate => 1 allows simple variable reference
	    #INTERPOLATE=>1,
	    #allows use of relative include path
	    RELATIVE=>1,
				     });
	my @output_array;
	$ENV{PATH} = "$base_dir/$tempdir/:/usr/bin/:$source_dir/:/bin/:$source_dir/executables";
	my $file = './template/postprocessing.html';
	#if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
	my $vars = {
	    title => "RNApredator bacterial sRNA target prediction Webserver - Postprocessing",
	    tbihome => "http://www.tbi.univie.ac.at/",
	    banner => "./pictures/banner_final.png",
	    introduction => "introduction.html",
	    available_genomes => "available_genomes.cgi",
	    target_search => "target_search.cgi",
	    help => "help.html",
	    accession_default => "$accession_default",
	    tax_id_default => "$tax_id_default",
	    postprocess => "../../../..$base_dir/$tempdir/postprocess",
	    java_script_location  => "./javascript/postprocessing.js",
	    scriptfile => "postprocessingscriptfile",
	    stylefile => "postprocessingstylefile"
	};
	$template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";	
	if (my $pid = fork) {
	    $query->delete_all();
	    #send user to result page
	    print"<script type=\"text/javascript\">
                        			window.location = \"$server/target_search.cgi?page=3&tempdir=$tempdir\";
                       			</script>";
	}elsif (defined $pid){
	    # close STDOUT;
	    open (RESULTTABLE, "<$base_dir/$tempdir/all_predictions.csv") or die "No Result Table Found $! - $tempdir";	
	    open (POSTPROCESSING, ">$base_dir/$tempdir/postprocess") or die "Could Not Write POSTPROCESSING $! - $tempdir";
	    my @result_table_array;
	    while(<RESULTTABLE>){
		push(@result_table_array,$_);
	    }
	    my $headerline="<tr>
               	 <td>Energy [kJ/mol]</td><td>z-Score</td><td>Interaction [dot-bracket]</td><td>mRNA [Start]</td><td>mRNA [End]</td><td>sRNA [Start]</td><td>sRNA [End]</td><td>Gene Annotation</td><td>Locus Tag</td><td>Genomic Coordinates</td><td>Accession</td><td>Replicon</td>
       			</tr>\n";
	    my $entry_counter=1;
	    #fields selected for post-processing can be found in @postprocess_selected
	    
	    #GO-Analysis-Preparation:
	    my @entries_print_array;
	    my @tag_array;		
	    my @accession_number_array;
	    my %genomes_without_goa;
	    my @genomes_without_goa_array;
	    #print STDERR "List of postprocessesing_selected:@postprocess_selected\n";
	    foreach my $postprocess_selected (@postprocess_selected){
		#print "$postprocess_selected<br>\n";
		chomp $postprocess_selected;
		$postprocess_selected =~s/\s$//;
		foreach my $result_line (@result_table_array){
		    chomp $result_line;
		    if($result_line =~ m/$postprocess_selected/){
			#print STDERR "Result line:  $result_line\n";
			#parse result line
			my $entry_line="<tr><td><strong>Interaction"."$entry_counter"."</strong></td></tr>\n";
			#key0,accession_letters1,accession_number2,coordinates3,dot_bracket_structure4,hypothetical_transcript_start5,hypothetical_transcript_end6,sRNA_start7,sRNA_end8,binding_energy9,intitial_binding_energy10,openening_energy_mRNA11,openening_energy_sRNA12,z-score13,annnotation14,locus-tag15,replicon16
			#00999945718-46562,NC,009999,45718-46562,((((((((&)))))))),406,413,34,41,-0.23,-3.40,0.26,2.91,-1.36,"putative phage repressor",Sbal195_4635,plasmid pS19502
			my @split_result_line = split (/,/,$result_line);
			my $dataline = "<tr id=\"$split_result_line[0]\">";
			my $accession_without_html="$split_result_line[1]"."\_"."$split_result_line[2]";
			push(@accession_number_array, $accession_without_html);
			my $accession = "<td>"."$split_result_line[1]"."\_"."$split_result_line[2]"."</td>";
			my $coordinates = "<td>"."$split_result_line[3]"."</td>";
			my @genomic_coordinates=split(/-/,$split_result_line[3]);
			#if first coordinate contains a c at the beginning its complementary
			#therefore first entry is the end, if not complementary its the start and substract 200 for translation start
			#and coordinates in .gbk file
			my $genomic_start;
			my $genomic_end;
			my $genomic_first_coordinate= $genomic_coordinates[0];
			my $genomic_second_coordinate= $genomic_coordinates[1];
			if($genomic_first_coordinate =~ m/c/){
			    $genomic_first_coordinate =~ s/c//;
			    $genomic_end = $genomic_first_coordinate - 200; #formulation misleading translation beginns here
			    $genomic_start = $genomic_second_coordinate;	
			}else{
			    $genomic_start = $genomic_first_coordinate + 200; #translation start
			    $genomic_end = $genomic_second_coordinate ;
			}
			
			my $dot_bracket = "<td>"."$split_result_line[4]"."</td>";
			#mRNA coordinates
			my $mRNA_start= $split_result_line[5];
			my $mRNA_start_html= "<td>"."$mRNA_start"."</td>";
			my $mRNA_end= $split_result_line[6];
			my $mRNA_end_html= "<td>"."$mRNA_end"."</td>";
			my $sRNA_start= "<td>"."$split_result_line[7]"."</td>";
			my $sRNA_end= "<td>"."$split_result_line[8]"."</td>";
			my $energy = "<td>"."$split_result_line[9]"."</td>";
			my $zscore = "<td>"."$split_result_line[13]"."</td>";
			my $annotation = "<td>"."$split_result_line[14]"."</td>";
			my $replicon = "<td>"."$split_result_line[16]"."</td>";
			
			#push(@tag_array,$split_result_line[15]);
			my $locus_tag_line = "<td>$split_result_line[15]</td>";
			#get associated GO-terms
			my $associated_go_terms;
			#try to open .ftn.goa file if it is not there remove selected from @goa_selected 
			if(-e "$source_dir/data/ebi_hakim/$accession_without_html.ftn.goa"){
			    my @go_input =`grep -P $split_result_line[15] $source_dir/data/ebi_hakim/$accession_without_html.ftn.goa`;
			    foreach my $go_input_line(@go_input){
				my @split_line=split(/\s/,$go_input_line);
				$associated_go_terms=$associated_go_terms."$split_line[0] ";
			    }
			    if(@go_input==0){
				$associated_go_terms="No GO-terms associated";
			    }
			    push(@tag_array,$split_result_line[15]);
			}else{
			    #and set associated go_terms to not available
			    $associated_go_terms="No GO-terms available";
			    $genomes_without_goa{$accession_without_html}=0;
			    #push(@genomes_without_goa,"$accession_without_html ");	
			}
			
			
			$dataline = "$dataline"."$energy"."$zscore"."$dot_bracket"."$mRNA_start_html"."$mRNA_end_html"."$sRNA_start"."$sRNA_end"."$annotation"."$locus_tag_line"."$coordinates"."$accession"."$replicon\n";
			#build processing line
			#get fasta sequence of mRNA
			open (SEQUENCESEARCH, "<$source_dir/data/ftn_all_species_Final/"."$accession_without_html".".ftn") or die "Could NOT Open Sequence <$source_dir/data/ftn_all_species_Final/"."$accession_without_html".".ftn $! - $tempdir";		
			my @sequence_lines;
			while(<SEQUENCESEARCH>){
			    push(@sequence_lines,$_);	
			}
			my $sequence_header_found=0;
			my $sequence;
			my $sequence_header;
			my @sequence_interesting_seq;
			foreach my $sequence_entry(@sequence_lines){
			    chomp $sequence_entry;
			    if($sequence_header_found==1){
				$sequence=$sequence_entry;
				$sequence_header_found=0;
			    }
			    if($sequence_entry =~ m/\>/){
				if($sequence_entry =~ m/$split_result_line[3]/){
				    $sequence_header_found=1;
				    $sequence_header=$sequence_entry;
				}	
			    }
			}
			open (SEQUENCEPRINT, ">$base_dir/$tempdir/$split_result_line[0].fasta") or die "Could NOT write Sequence >$base_dir/$tempdir/$split_result_line[0].fasta $! - $tempdir";
			print SEQUENCEPRINT "$sequence_header\n$sequence\n";
			open (sRNA, "<$base_dir/$tempdir/sRNA.fasta")	or die "could not open sRNA.fasta";
			my $sRNA_seq;
			while(<sRNA>){
			    $sRNA_seq=$_;
			}
			#Retrieve locus tag from corresponding gbk file	
			#filename: e.g. NC_008752.gbk line containing coordinates: gene start..end , next line below that has /locus_tag="example tag"
			#open (GENEBANKFILE, "</scratch/egg/sandbox/DA/gbk/$accession_without_html.gbk") or die "could not open .gbk";
			#my @gbk_lines;
			#my $tag_found=0;
			#my $locus_tag="";
			#while(<GENEBANKFILE>){
			#         push(@gbk_lines,$_);
			#}
			#close GENEBANKFILE;
			#print POSTPROCESSING "check for: "."$genomic_start\.\.$genomic_end\n<br>";	
			#foreach my $gbk_line(@gbk_lines){
			#        chomp $gbk_line;
			#        if($tag_found==1){
			#		if($gbk_line =~m/locus_tag/){
			#			my @split_gbk_line = split(/"/,$gbk_line);
			#			$locus_tag=$split_gbk_line[1];
			#			#print POSTPROCESSING "$locus_tag<br>\n";
			#			$tag_found=0;
			#		}
			#      	}
			#        if($gbk_line =~ m/gene/){
			#									
			#                if($gbk_line =~ m/$genomic_start\.\.$genomic_end/){
			#                       $tag_found=1;
			#			#print POSTPROCESSING "found: "."$genomic_start\.\.$genomic_end\n<br>";
			#                }
			#        }
			#}						
			#Calculate parameters for accessbility plot change
			my $absolute_mRNA_interaction_start = $mRNA_start + 200;
			my $absolute_mRNA_interaction_stop = $mRNA_end + 200;
			
			#Calculate detailed interaction view
			my @arguments_array = ("$source_dir/executables/interactionrenderer.pl", "$tempdir","$split_result_line[0]", "$absolute_mRNA_interaction_start" , "$absolute_mRNA_interaction_stop" , "$split_result_line[7]", "$split_result_line[8]" , "$split_result_line[4]" , "$base_dir");
			# exec'/scratch2/egg/webserv/executables/interactionrenderer.pl',"$tempdir $split_result_line[0] $absolute_mRNA_interaction_start $absolute_mRNA_interaction_stop $sRNA_coordinates[0] $sRNA_coordinates[1] \'$split_result_line[4]\'" or die "$!";
			system(@arguments_array) == 0 or die "$! - $?"; #creates interactionplot
			#Calculate parameters for gene ontology
			#Assemble Output
			#my $locus_tag_line = "locus tag: $locus_tag <br>";
			my $get_mRNA_sequence = "<tr><td>download:<br>  <a href=\"$server/html/$tempdir/$split_result_line[0].fasta\">mRNA sequence</a><br>";
			my $get_sRNA_sequence = "download:<br> <a href=\"$server/html/$tempdir/sRNA.fasta\">sRNA sequence</a><br>";	
			my $accessiblity_plot ="Accessiblity Plot: <a href=\"$server/accessiblity_plot.cgi?s=$split_result_line[0]&b=$absolute_mRNA_interaction_start&e=$absolute_mRNA_interaction_stop&tempdir=$tempdir&page=0\" target=\"_blank\"><br>Calculate (new window)</a><br>";
			my $rna_up_submit ="RNAup Webserver: <a href=\"$server/cgi-bin/RNAup.cgi?PAGE=2&SCREEN=$sequence\n&SCREEN2=$sRNA_seq\n&tempdir=$tempdir&page=0\" target=\"_blank\"><br>Submit (new window)</a><br>";
			#my $go_calculation="Gene Ontology:  <a href=\"http://insulin.tbi.univie.ac.at/accessiblity_plot.cgi?s=$split_result_line[0]&b=$absolute_mRNA_interaction_start&e=$absolute_mRNA_interaction_stop&sRNA=$sRNA&tempdir=$tempdir\"\ target=\"_blank\">Calculate (new window)</a><br>";
			open(ASCII, "<$base_dir/$tempdir/$split_result_line[0].ascii") or die "could not open $base_dir/$tempdir/$split_result_line[0].asccii ,$! ";
			my $ascii_string="";
			while(<ASCII>){
			    $ascii_string="$ascii_string"."$_";
			}
			
			#my $processing_field = "</td><td id=\"processing-$split_result_line[0]\" colspan=\"11\"><strong>Detailed Interaction.png):</strong><br>
			#<img alt=\"Detailed Interaction\" src=\"$server/html/$tempdir/$split_result_line[0].png\"><br>
			my $processing_field = "</td><td id=\"processing-$split_result_line[0]\" colspan=\"11\">
						<br><strong>Detailed Interaction(as ASCII):</strong>
						$ascii_string
						</td></tr><tr><td style=\"border:none\">&nbsp;</td></tr>";
			my $go_term_line="<tr><td>Associated GO-terms</td><td colspan=\"11\">$associated_go_terms</td></tr>";
			my $processing_line = "$get_mRNA_sequence"."$get_sRNA_sequence"."$accessiblity_plot"."$rna_up_submit"."$processing_field\n";
			#print POSTPROCESSING "$entry_line"."$headerline"."$dataline"."$processing_line";
			my $entry_print = "$entry_line"."$headerline"."$dataline"."$go_term_line"."$processing_line";
			push(@entries_print_array,$entry_print);
			$entry_counter++;
			
			#exec "/scratch2/egg/webserv/executables/accessibility_analysis_batch.pl -s $base_dir/$tempdir/$split_result_line[0].fasta -b $absolute_mRNA_interaction_start -e $absolute_mRNA_interaction_stop -d $calculate_accessiblity_begin -f $calculate_accessiblity_end";
			#system(@arguments_array) == 0 or die "$! - $?"; #creates interactionplot
		    }
		}
	    }
	    #now calclate go, then print go, then everything else
	    #merge all NC_id.goa files into one and name it tempdir.goa and put it in the tempdir
	    #exec "export SGE_ROOT = $sge_root_directory\n";
	    @genomes_without_goa_array=keys(%genomes_without_goa);
	    unless(@tag_array==0){	
		open (MERGEDGOA, ">$base_dir/$tempdir/$tempdir.ftn.goa") or die "Could Not Write Merged .goa file $! - $tempdir";
		foreach my $nc_id (@accession_number_array){
		    open (GOA, "<$source_dir/data/ebi_hakim/$nc_id.ftn.goa") or print STDERR "Could Not Read $nc_id.goa file $! - $tempdir";
		    while(<GOA>){
			#push(@lines,$_);
			print MERGEDGOA "$_";
		    }
		    close GOA;	
		}
		close MERGEDGOA;
		my $GO_path = "$base_dir/$tempdir/";
		my $accession_number = $tempdir; #$tempdir.goa
		my $csv_path="$base_dir/$tempdir/all_predictions.csv";
		my $GO_Kegg_path = "$base_dir/$tempdir/";
		open (SELECTEDLIST, ">$base_dir/$tempdir/selected_list") or die "Could Not Write Selected List $! - $tempdir";
		foreach my $tag(@tag_array){
		    print SELECTEDLIST "$tag\n";
		}
		close SELECTEDLIST;
		copy("$source_dir/executables/launch_go_kegg.sh","$base_dir/$tempdir/launch_go_kegg.sh") or die "Copy failed launch_go_kegg.sh : $!";
		copy("$source_dir/executables/GO_Kegg.R","$base_dir/$tempdir/GO_Kegg.R") or die "Copy failed- GO_Kegg.R: $!";
		chmod 0755, "$base_dir/$tempdir/launch_go_kegg.sh", "$base_dir/$tempdir/GO_Kegg.R";
		my @GO_arguments_array = ("$base_dir/$tempdir/launch_go_kegg.sh", "$GO_path","$accession_number","$csv_path","$base_dir/$tempdir/selected_list","$GO_Kegg_path");
		system(@GO_arguments_array) == 0 or die "GO-calculation error:$! - $?"; #creates GO.csvs
		print POSTPROCESSING "<h3>Gene Ontologie Terms for selected Interactions: </h3>\n";
		unless(@genomes_without_goa_array==0){
		    print POSTPROCESSING "No GO-terms available for: @genomes_without_goa_array, no GO analysis possible.";
		}
		#MF - Molecular Function
		open (MF, "<$base_dir/$tempdir/MF.csv") or die "Could Not Read MF.csv file $! - $tempdir";
		my @mf_lines;
		while(<MF>){
		    push(@mf_lines,$_);
		}
		close MF;
		#print mf table
		print POSTPROCESSING "<u>Molecular Function:</u><br>\n";
		print POSTPROCESSING "<table style=\"display:none\" class=\"tablesorter\" id=\"myTable\" border=\"1\"  cellspacing=\"1\" width=\"75%\">\n";
		print POSTPROCESSING "<thead>\n";
		print POSTPROCESSING "<tr>\n
								<th>GO.ID</th>\n 
						        	<th>Term</th>\n
							        <th>Annotated</th>\n
							        <th>Significant</th>\n
								<th>Expected</th>\n
								<th>Weight01 p-value</th>\n
							</tr>\n";
		print POSTPROCESSING "</thead>\n";
		shift(@mf_lines);
		#"GO.ID","Term","Annotated","Significant","Expected","weight01"
		#"1","GO:0043768","S-ribosylhomocysteine lyase activity",1,1,0,"0.00065"
		#0 1 2 3          4 5                                    6       7        8
		print POSTPROCESSING "<tbody>\n";
		foreach my $print_mf_line(@mf_lines){
		    print  POSTPROCESSING "<tr>\n";
		    my @split_print_mf_line_array=split(/"/,$print_mf_line);
		    my $GO_id="<td>$split_print_mf_line_array[3]</td>\n";
		    my $GO_term="<td>$split_print_mf_line_array[5]</td>\n";
		    my @split_annotated_significant_expected=split(/,/,$split_print_mf_line_array[6]);
		    my $GO_annotated="<td>$split_annotated_significant_expected[1]</td>\n";
		    my $GO_significant="<td>$split_annotated_significant_expected[2]</td>\n";
		    my $GO_expected="<td>$split_annotated_significant_expected[3]</td>\n";
		    my $GO_weight="<td>$split_print_mf_line_array[7]</td>\n";
		    print POSTPROCESSING "$GO_id"."$GO_term"."$GO_annotated"."$GO_significant"."$GO_expected"."$GO_weight";		
		    print POSTPROCESSING "</tr>\n";
		}
		print POSTPROCESSING "</tbody>\n";	
		print POSTPROCESSING "</table>\n";
		print POSTPROCESSING "<p class=\"demo5\"></p>\n";
		#BP - Biological Process
		open (BP, "<$base_dir/$tempdir/BP.csv") or die "Could Not Read BP.csv file $! - $tempdir";
		my @bp_lines;
		while(<BP>){
		    push(@bp_lines,$_);
		}
		close BP;
		#print bp table
		print POSTPROCESSING "<u>Biological Process:</u><br>\n";
		print POSTPROCESSING "<table style=\"display:none\"  class=\"tablesorter\" id=\"myTable1\" border=\"1\"  cellspacing=\"1\" width=\"75%\">\n";
		print POSTPROCESSING "<thead>\n";
		print POSTPROCESSING "<tr>\n
        	                                                <th>GO.ID</th>\n
                	                                        <th>Term</th>\n
                        	                                <th>Annotated</th>\n
	                                                        <th>Significant</th>\n
        	                                                <th>Expected</th>\n
                	                                        <th>Weight01 p-value</th>\n
                        	                        </tr>\n";
		print POSTPROCESSING "</thead>\n";
		shift(@bp_lines);
		#"GO.ID","Term","Annotated","Significant","Expected","weight01"
		#"1","GO:0043768","S-ribosylhomocysteine lyase activity",1,1,0,"0.00065"
		#0 1 2 3          4 5                                    6       7        8
		print POSTPROCESSING "<tbody>\n";
		foreach my $print_bp_line(@bp_lines){
		    print  POSTPROCESSING "<tr>\n";
		    my @split_print_bp_line_array=split(/"/,$print_bp_line);
		    my $GO_id="<td>$split_print_bp_line_array[3]</td>\n";
		    my $GO_term="<td>$split_print_bp_line_array[5]</td>\n";
		    my @split_annotated_significant_expected=split(/,/,$split_print_bp_line_array[6]);
		    my $GO_annotated="<td>$split_annotated_significant_expected[1]</td>\n";
		    my $GO_significant="<td>$split_annotated_significant_expected[2]</td>\n";
		    my $GO_expected="<td>$split_annotated_significant_expected[3]</td>\n";
		    my $GO_weight="<td>$split_print_bp_line_array[7]</td>\n";
		    print POSTPROCESSING "$GO_id"."$GO_term"."$GO_annotated"."$GO_significant"."$GO_expected"."$GO_weight";
		    print POSTPROCESSING "</tr>\n";
		}
		print POSTPROCESSING "</tbody>\n";
		print POSTPROCESSING "</table>\n";
		print POSTPROCESSING "<p class=\"demo5\"></p>\n";
		#CC - Cell Compartment
		open (CC, "<$base_dir/$tempdir/CC.csv") or die "Could Not Read CC.csv file $! - $tempdir";
		my @cc_lines;
		while(<CC>){
		    push(@cc_lines,$_);
		}
		#print cc table
		print POSTPROCESSING "<u>Cell Component:</u><br>\n";
		print POSTPROCESSING "<table style=\"display:none\"  class=\"tablesorter\" id=\"myTable2\" border=\"1\"  cellspacing=\"1\" width=\"75%\">\n";
		print POSTPROCESSING "<thead>\n";
		print POSTPROCESSING "<tr>\n
        	                                                <th>GO.ID</th>\n
	        	                                        <th>Term</th>\n
                        	                                <th>Annotated</th>\n
                                	                        <th>Significant</th>\n
                                        	                <th>Expected</th>\n
                                                	        <th>Weight01 p-value</th>\n
                                 	               </tr>\n";
		print POSTPROCESSING "</thead>\n";
		shift(@cc_lines);
		#"GO.ID","Term","Annotated","Significant","Expected","weight01"
		#"1","GO:0043768","S-ribosylhomocysteine lyase activity",1,1,0,"0.00065"
		#0 1 2 3          4 5                                    6       7        8
		print POSTPROCESSING "<tbody>\n";
		foreach my $print_cc_line(@cc_lines){
		    print  POSTPROCESSING "<tr>\n";
		    my @split_print_cc_line_array=split(/"/,$print_cc_line);
		    my $GO_id="<td>$split_print_cc_line_array[3]</td>\n";
		    my $GO_term="<td>$split_print_cc_line_array[5]</td>\n";
		    my @split_annotated_significant_expected=split(/,/,$split_print_cc_line_array[6]);
		    my $GO_annotated="<td>$split_annotated_significant_expected[1]</td>\n";
		    my $GO_significant="<td>$split_annotated_significant_expected[2]</td>\n";
		    my $GO_expected="<td>$split_annotated_significant_expected[3]</td>\n";
		    my $GO_weight="<td>$split_print_cc_line_array[7]</td>\n";
		    print POSTPROCESSING "$GO_id"."$GO_term"."$GO_annotated"."$GO_significant"."$GO_expected"."$GO_weight";
		    print POSTPROCESSING "</tr>\n";
		}
		print POSTPROCESSING "</tbody>\n";
		print POSTPROCESSING "</table>\n";
		print POSTPROCESSING "<p class=\"demo5\"></p>\n";
	    }else{
		if(@genomes_without_goa_array==0){
		    print POSTPROCESSING "No GO-terms associated to selected entries.";
		}else{
		    print POSTPROCESSING "No GO-terms available for @genomes_without_goa_array, no GO analysis possible.";
		}
	    }
	    #Selected Entries:	
	    print POSTPROCESSING "<h3>Detailed View for selected Interactions: </h3>\n";
	    print POSTPROCESSING "<table class=\"postprocess\" cellspacing=\"3\" border=\"1\">";
	    foreach my $print_entry (@entries_print_array){
		print POSTPROCESSING "$print_entry";
	    }
	    `touch $base_dir/$tempdir/done2`;			
	}
    }
    unless(-e "$base_dir/$tempdir/done2"){
	print $query->header();
	my $template = Template->new({
	    # where to find template files
	    INCLUDE_PATH => ['./template'],
	    #Interpolate => 1 allows simple variable reference
	    #INTERPOLATE=>1,
	    #allows use of relative include path
	    RELATIVE=>1,
				     });
	my @output_array;
	my $file = './template/postprocessing.html';
	#if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
	my $vars = {
	    title => "RNApredator bacterial sRNA target prediction Webserver - Postprocessing",
	    tbihome => "http://www.tbi.univie.ac.at/",
	    banner => "./pictures/banner_final.png\" alt=\"Banner\"",
	    introduction => "introduction.html",
	    available_genomes => "available_genomes.cgi",
	    target_search => "target_search.cgi",
	    help => "help.html",
	    accession_default => "$accession_default",
	    tax_id_default => "$tax_id_default",
	    postprocess => "../../../..$base_dir/$tempdir/postprocess",
	    java_script_location  => "./javascript/postprocessing.js",
	    scriptfile => "postprocessingscriptfile",
	    stylefile => "postprocessingstylefile"    
	};
	$template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";
	my $link="$server/target_search.cgi?"."page=$page"."&tempdir=$tempdir";
	print "<p>Postprocessing:</p>";
	print "<p>This can take some minutes.</p>";
	print "<p>Wait for calculation to finish or</p>";
	print "<p>bookmark following <a href=\"$link\">link</a> and return later.</p>";
	print "<br>";
	print"<script type=\"text/javascript\">
			window.setTimeout (\' window.location = \"$server/target_search.cgi?page=3&tempdir=$tempdir\"\', 5000);
                    	</script>";
    }
# window.location = \"http://insulin.tbi.univie.ac.at/target_search.cgi?page=3&tempdir=$tempdir\";	
    if(-e "$base_dir/$tempdir/done2"){
	print $query->header();
	my $template = Template->new({
	    # where to find template files
	    INCLUDE_PATH => ['./template'],
	    #Interpolate => 1 allows simple variable reference
	    #INTERPOLATE=>1,
	    #allows use of relative include path
	    RELATIVE=>1,
				     });
	my @output_array;
	my $file = './template/postprocessingdone.html';
	#if id param is set we already preset it in the appropiate input field e.g. tax_default, accession_default
	my $vars = {
	    title => "RNApredator bacterial sRNA target prediction Webserver - Postprocessing",
	    tbihome => "http://www.tbi.univie.ac.at/",
	    banner => "./pictures/banner_final.png",
	    introduction => "introduction.html",
	    available_genomes => "available_genomes.cgi",
	    target_search => "target_search.cgi",
	    help => "help.html",
	    accession_default => "$accession_default",
	    tax_id_default => "$tax_id_default",
	    postprocess => "../../../..$base_dir/$tempdir/postprocess",
	    java_script_location  => "./javascript/postprocessing.js",
	    scriptfile => "postprocessingscriptfile",
	    stylefile => "postprocessingstylefile"
	};
	$template->process($file, $vars) || die "Template process failed: ", $template->error(), "\n";	
    }
}

