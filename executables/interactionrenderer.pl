#!/usr/bin/perl
use strict;
use diagnostics;
#asccii-like png output of interaction
#parse input
$|=1;
my $tempdir = $ARGV[0];
my $mRNA_identifier = $ARGV[1];
my $mRNA_start =$ARGV[2];
my $mRNA_start_print=$mRNA_start-200;
my $mRNA_end =$ARGV[3];
my $mRNA_end_print=$mRNA_end-200;
my $mRNA_offset = $mRNA_start-1 ; #array and rna-index start at 0 and 1
my $mRNA_length = $mRNA_end - $mRNA_offset;
my $sRNA_start=$ARGV[4];
my $sRNA_end =$ARGV[5];
my $base_dir =$ARGV[7];
my $sRNA_offset = $sRNA_start-1; #array and rna-index start at 0 and 1
my $sRNA_length = ($sRNA_end - $sRNA_offset);
#todo: split dot bracket, finish  substr, include in target_search
my $input_dot_bracket_string=$ARGV[6];
#print STDERR "Interactionrenderer-input: tempdir $tempdir ,mRNA_identifier $mRNA_identifier, mRNA_start $mRNA_start , mRNA_end $mRNA_end , sRNA_start $sRNA_start , sRNA_end $sRNA_end , input_dot_bracket_string $input_dot_bracket_string , base_dir $base_dir \n";
my @input_dot_bracket_array = split("&",$input_dot_bracket_string);
my $mRNA_dot_bracket_string=$input_dot_bracket_array[0];
my $sRNA_dot_bracket_string=$input_dot_bracket_array[1]; 
#open mRNA filehandle and get seq
open (MRNA, "<$base_dir/$tempdir/$mRNA_identifier.fasta") or die "No $tempdir/$mRNA_identifier.fasta found";
my @mRNA_fasta = <MRNA>;
my $whole_mRNA = $mRNA_fasta[1];
my $mRNA = substr $whole_mRNA, $mRNA_offset, $mRNA_length;
#open sRNA filehandle and get seq
open (SRNA, "<$base_dir/$tempdir/sRNA.fasta") or die "No $tempdir/sRNA.fasta found";
my @sRNA_fasta = <SRNA>;
my $whole_sRNA=$sRNA_fasta[1];
my $sRNA = substr $whole_sRNA, $sRNA_offset, $sRNA_length;

#get and calculate al relevant mRNA values
#my $mRNA="GGGATGATGATAACAAATGCGCGTCTTT"; #Interaction Site
	#T gegen U tauschen
my $mRNA_start_html = $mRNA_start - 200; #-200
my $mRNA_end_html = $mRNA_end - 200; #-200
$mRNA =~ s/T/U/g;
my @mRNA = split '', $mRNA;
#my $mRNA_dot_bracket_string = "(.((((((((((((((((((((((((.(";
my @mRNA_dot_bracket = split '', $mRNA_dot_bracket_string;
#print STDERR "mRNA_dot_bracket_string: $mRNA_dot_bracket_string \n";
#get number of RNA basepair by counting brackets
	#my $basepairs=0;
#foreach my $mRNA_dot_bracket_letter (@mRNA_dot_bracket){
#		if($mRNA_dot_bracket_letter =~ m/\(/ ){
#		$basepairs++;
#	}	
#}
#$bild->string(gdGiantFont,1,10,"sequlength = $basepairs",$black);

	#my $sRNA_dot_bracket_string = ").))))))))))))))))))))))))))";
my @sRNA_dot_bracket = split '', $sRNA_dot_bracket_string;
@sRNA_dot_bracket = reverse(@sRNA_dot_bracket);
#my $sRNA="AAGACGCGCAUUUGUUAUCAUCAUCCC"; #Interaction Site
my @sRNA = split '', $sRNA;
@sRNA = reverse(@sRNA);
#my total length
my $length;
if($mRNA_length>$sRNA_length){
    $length=$mRNA_length;	
}else{
    $length=$sRNA_length;
}

my $mRNA_asccii="";
my $interaction_asccii="";
my $sRNA_asccii="";

for(my $i=0;$i<=$length;$i++){
    #we look at s and mRNA dot braket arrays and have 4 different cases
    if(@mRNA_dot_bracket){
	my $mRNA_dot_bracket_letter = shift(@mRNA_dot_bracket);
	my $sRNA_dot_bracket_letter = shift(@sRNA_dot_bracket);
	#print STDERR "input_dot_bracket_string:  $input_dot_bracket_string \n";
	#print STDERR "mRNA_dot_bracket_letter $mRNA_dot_bracket_letter\n , $sRNA_dot_bracket_letter $sRNA_dot_bracket_letter \n";
	if(($mRNA_dot_bracket_letter =~ m/\(/ ) and ( $sRNA_dot_bracket_letter =~ m/\)/)){
	    #case 1 basepair	
	    #mRNA
	    my $mRNA_letter=shift(@mRNA);
	    #add to asccii
	    $mRNA_asccii = "$mRNA_asccii"."$mRNA_letter";
	    #add interaction letter to asccii
	    $interaction_asccii = "$interaction_asccii"."|";
	    #draw letter
	    #sRNA
	    #calculate coordinates
	    my $sRNA_y=60;
	    my $sRNA_x=7*9 + ($i*9)*2 -9;
	    if($i!=0){
		#calculate coordinates for covalent bond and print
	    }      
	    #fetch letter
	    my $sRNA_letter=shift(@sRNA);
	    $sRNA_asccii = "$sRNA_asccii"."$sRNA_letter";
	    #draw letter
	    #basepair
	    
	}elsif(($mRNA_dot_bracket_letter =~ m/\./ ) and ( $sRNA_dot_bracket_letter =~ m/\./)){
	    #case 2 no basepair 
	    #mRNA
	    my $mRNA_letter=shift(@mRNA);
	    #asccii
	    $mRNA_asccii = "$mRNA_asccii"."$mRNA_letter";
	    #draw letter
	    #fetch letter
	    my $sRNA_letter=shift(@sRNA);
	    #asccii
	    $sRNA_asccii = "$sRNA_asccii"."$sRNA_letter";
	    $interaction_asccii = "$interaction_asccii"." ";
	    
	}elsif(($mRNA_dot_bracket_letter =~ m/\./ ) and ( $sRNA_dot_bracket_letter =~ m/\)/)){
	    #case 3 no pairing base on mRNA
	    #get letter and print dash
	    #mRNA
	    #calculate coordinates
	    my $mRNA_letter=shift(@mRNA);
	    #asscci
	    $mRNA_asccii = "$mRNA_asccii"."$mRNA_letter";
	    $interaction_asccii = "$interaction_asccii"." ";
	    $sRNA_asccii = "$sRNA_asccii"."-";
	    #draw letter
	    
	}elsif(($mRNA_dot_bracket_letter =~ m/\(/ ) and ( $sRNA_dot_bracket_letter =~ m/\./)){
	    #case 4 no basepair on sRNA	
	    #get letter and print dash
	    #mRNA
	    my $sRNA_letter=shift(@sRNA);
	    #asscci
	    $mRNA_asccii = "$mRNA_asccii"."-";
	    $interaction_asccii = "$interaction_asccii"." ";
	    $sRNA_asccii = "$sRNA_asccii"."$sRNA_letter";
	    #draw letter
	}
    }
    
}

#asccii output:
open (ASCII, ">$base_dir/$tempdir/$mRNA_identifier.ascii") or die "Could not write $tempdir/$mRNA_identifier.ascii";
print ASCII  "<table><tr><td style=\"border:0px solid #000000;\"><pre>mRNA: 5'-<br><br>sRNA: 3'-</pre></td><td style=\"border:0px solid #000000;\"><pre>$mRNA_asccii<br>$interaction_asccii<br>$sRNA_asccii<br></pre></td><td style=\"border:0px solid #000000;\"><pre>-3'<br><br>-5'</pre></td></tr></table>";	
close ASCII;
