#!/usr/bin/perl
#cvs to html 

use warnings;
use strict;
use diagnostics;
use utf8;
use Math::Round;
use Data::Dumper;
use Pod::Usage;
use Cwd;
use List::MoreUtils qw/ uniq /;
use Data::Dumper;

##########################################################################
#convert the total specieslist into an html table for the user input page
my $tempdir = $ARGV[0];
my $base_dir=$ARGV[1];
#my $tempdir_parent_directory="/srv/http/RNApredator/html";
my $top= 10000;
#toDO: hand over sourcedir and hand over full tempdir path
my $source_dir="/srv/http/RNApredator";
open (PLEX, "<$base_dir/$tempdir/prediction.res"); #STUFF TO RECOVER
open (BUG,  ">$base_dir/$tempdir/bug");
#results related variables
my @lines;
my $query="";
my $target="";
my $accession_letters=""; #accession letter NC
my $accession_number=""; #accession number 000913
my $accession_version=""; #accession number 000913
my $coordinates="";
my $DEBUG=0;

####Energy mean and variation
my $mean=0;
my $sample_variance=0;
my $standard_variation=0;
my $count=1;

#my $hash
my %HoA;

#which genome are we working on
my @genome_array;
my $temp_hash;

#read. parse. and put energy where it should be.
while(my $line=<PLEX>){
  next if($line=~/^$/);
  chomp($line);
  if($line=~/>/){
    $target=$line;
    $line=<PLEX>;
    chomp($line);
    $query=$line;
    $target=~s/>//;
    $query=~s/>//;
    my @fields = split(/\_/, $target);
    $coordinates=$fields[3]; #save gene location
    ($accession_number, $accession_version)=split(/\./,$fields[2]); #save gene location
    $accession_letters=$fields[1];
  }
  else{
    #parse interactions
    my @fields=split(/[,:\=\+\s]+/,$line);
    my $fields_length = $#fields;
    if($fields_length==8){
	my $dot_bracket_structure=$fields[0];
	my $mRNA_coordinates = $fields[1]."-".$fields[2];
	my $sRNA_coordinates = $fields[3]."-".$fields[4];
	my $binding_energy = $fields[5]; $binding_energy=~s/\(//;
	my $intitial_binding_energy = $fields[6];
	my $opening_energy_1 =$fields[7];
	my $opening_energy_2 =$fields[8];$opening_energy_2=~s/\)//;
	#save info in hash
 	my $key1 = "$coordinates";
 	my $key2 = "$accession_number"."$coordinates"."_"."$mRNA_coordinates";
 	if(defined($HoA{$key1}{$key2})){
  	   $count++;
 	   next;
	}
  	push @{$HoA{$key1}{$key2}}, "$key2", "$accession_letters", "$accession_number", "$coordinates";
	push @{$HoA{$key1}{$key2}}, "$dot_bracket_structure", "$mRNA_coordinates", "$sRNA_coordinates", "$binding_energy", "$intitial_binding_energy", "$opening_energy_1", "$opening_energy_2";
	$temp_hash->{"$HoA{$key1}{$key2}[1]_$HoA{$key1}{$key2}[2]"}=1;
   	#compute one pass Z and Mean
    	$standard_variation+=$binding_energy**2;
    	$mean+=$binding_energy;
   	$count++;
    }else{
        my $dot_bracket_structure=$fields[0];
        my $mRNA_coordinates = $fields[1]."-".$fields[2];
        my $sRNA_coordinates = $fields[3]."-".$fields[4];
        my $binding_energy = $fields[6]; #$binding_energy=~s/\(//;
        my $intitial_binding_energy = $fields[7];
        my $opening_energy_1 =$fields[8];
        my $opening_energy_2 =$fields[9];$opening_energy_2=~s/\)//;
        #save info in hash
        my $key1 = "$coordinates";
        my $key2 = "$accession_number"."$coordinates"."_"."$mRNA_coordinates";
        if(defined($HoA{$key1}{$key2})){
           $count++;
           next;
        }
        push @{$HoA{$key1}{$key2}}, "$key2", "$accession_letters", "$accession_number", "$coordinates";
        push @{$HoA{$key1}{$key2}}, "$dot_bracket_structure", "$mRNA_coordinates", "$sRNA_coordinates", "$binding_energy", "$intitial_binding_energy", "$opening_energy_1", "$opening_energy_2";
        $temp_hash->{"$HoA{$key1}{$key2}[1]_$HoA{$key1}{$key2}[2]"}=1;
        #compute one pass Z and Mean
        $standard_variation+=$binding_energy**2;
        $mean+=$binding_energy;
        $count++;
    }
  }
}
#compute Z-score
$standard_variation = ($standard_variation - $mean**2/$count)/($count-1);
$standard_variation = sqrt($standard_variation);
$mean=$mean/$count;
if($DEBUG) {print $standard_variation," ",$mean," ";}
#fetch chromosom type
@genome_array=keys %{$temp_hash};
my $chromosome_hash; #hash containing chromosome style
my $chromos = join("|",@genome_array);
my @chromosom=`grep -P "($chromos)" $source_dir/data/lists/input_lists/input_list_final | cut -f 1,7 -d ","`;
if($DEBUG){
  print "Chromosome available\n";
  print join(" ",@chromosom);
}
foreach my $chromo (@chromosom){
  chomp($chromo);
  (my $ref_id , my $type)=split(/,/,$chromo);
  $ref_id=~s/^.+_(\d+)\..+/$1/;
  $chromosome_hash->{$ref_id}=$type;
}
if($DEBUG){
  print "Chromosome_hash\n";
  print Dumper($chromosome_hash);
}
#fetch locus_tag
my $command_line="cat ";
foreach my $genome (@genome_array){
  $command_line.="$source_dir/data/ftn_all_species_Final/$genome.ftn ";
}
$command_line.="| grep \">\" | tr -d \">\" | sed -r 's#\\[.+##g' ";
print BUG "commandline:$command_line\n";
my @mapping=`$command_line`;
my $annotation_hash;
foreach my $mapping_line(@mapping){
  chomp($mapping_line);
  my $annotation_key="";
  my $annotation_value="";
  #getting locus tag
  #some locus tags contain underscores which are also contained in the annotation key
  #therefore we copy the mapping_line and split with whitespaces to isolate the locus tag
  my $mapping_line_locus_tag = $mapping_line;
  my @line_splitted_locus_tag=split(/[\s]+/,$mapping_line_locus_tag);
  #the locus tag should be contained in the last element
  my $locus_tag=pop(@line_splitted_locus_tag);
  #get key
  my @line_splitted=split(/[_\s]+/,$mapping_line);
  $annotation_key = $line_splitted[3];
  $annotation_key=~s/\s.+//;
  #do we have annotation???
  if(scalar(@line_splitted) <= 5){
    $annotation_value="NA";
    #$locus_tag       ="NA"; changed
    push @{$annotation_hash->{$annotation_key}}, ($annotation_value, $locus_tag);
    next;
  }
  my @annotation_split=split(/[\s-]/,join(" ",@line_splitted[4..$#line_splitted]));
  #$locus_tag=$annotation_split[$#annotation_split]; changed
  print BUG "locustag:$locus_tag\n";
  $annotation_value=join(" ",@annotation_split[0..$#annotation_split-1]);
  $annotation_value =~ s/,/;/g;
  #$locus_tag       =$annotation_split[$#annotation_split]; changed
  if($locus_tag!~/\d/){
    $annotation_value.=" ".$locus_tag;
    $locus_tag="NA";
  }
  push @{$annotation_hash->{$annotation_key}}, ($annotation_value,$locus_tag);
  print BUG "annotation_value:$annotation_value locus_tag:$locus_tag\n";
}

if($DEBUG){
  print "############Annotation hash\n";
  print Dumper($annotation_hash),"\n";
  print "##############################";
}
#now that we have the same key system go through all key and check where we can add some information

my $parsed_results;
foreach my $key1 (keys %HoA){
  foreach my $key2 (keys %{$HoA{$key1}}){
#    next if(defined($parsed_results->{$key2}));
    push @{$parsed_results->{$key2}}, @{$HoA{$key1}{$key2}};
    my $Z= ($HoA{$key1}{$key2}[7] - $mean)/$standard_variation;
    $Z= nearest(0.01, $Z); 
    push @{$parsed_results->{$key2}}, $Z; #push Z,
    push @{$parsed_results->{$key2}}, $annotation_hash->{$key1}->[0];
    push @{$parsed_results->{$key2}}, $annotation_hash->{$key1}->[1];
    push @{$parsed_results->{$key2}}, $chromosome_hash->{$parsed_results->{$key2}->[2]};
   }
    #annotation and locus in the right order, print stuff and tschuess!!!!!
}
if($DEBUG){
  print "############Result hash\n";
  print Dumper($parsed_results),"\n";
  print "##############################";
}



open (TOP25, ">$base_dir/$tempdir/top25.html");
open (TOP50, ">$base_dir/$tempdir/top50.html");
open (TOP75, ">$base_dir/$tempdir/top75.html");
open (TOP100,">$base_dir/$tempdir/top100.html");
open (TOP500,">$base_dir/$tempdir/top500.html");
open (ALL,   ">$base_dir/$tempdir/topAll.html");
open (CSV,   ">$base_dir/$tempdir/all_predictions.csv");


my $counter=0;
foreach my $sort_key (sort {$parsed_results->{$a}->[7] <=> $parsed_results->{$b}->[7]} keys %{$parsed_results}) {
  $counter++;
  (my $hypothetical_transcript_start, my $hypothetical_transcript_end) = split(/\-/,$parsed_results->{$sort_key}->[5]);
  $hypothetical_transcript_start-=200;
  $hypothetical_transcript_end-=200;
  my $genomic_coordinates = $parsed_results->{$sort_key}->[3];
  my $strand;
  if($genomic_coordinates=~m/c/){
    $strand="-";
    $genomic_coordinates=~s/c//;
  }else{
    $strand="+";
  }
  my $output_line =  "\<tr id\=\"t"."$counter\"\>"."<td>"."<input type=\"checkbox\" id=\"p"."$counter\" name=\"p"."$counter"."\" value=\"$parsed_results->{$sort_key}->[0]\">"."</td>"."<td>"."$counter."."</td>"."<td>"."$parsed_results->{$sort_key}->[7]"."</td>"."<td>"."$parsed_results->{$sort_key}->[11]"."</td>"."<td>"."$parsed_results->{$sort_key}->[4]"."</td>"."<td id=\"t"."$counter"."-start\">"."$hypothetical_transcript_start"."</td>"."<td id=\"t"."$counter"."-end\">"."$hypothetical_transcript_end"."</td>"."<td> $parsed_results->{$sort_key}->[6]"."</td>"."<td>"."$parsed_results->{$sort_key}->[12]"."</td>"."<td>"."$parsed_results->{$sort_key}->[13]"."</td>"."<td>"."$strand"."</td>"."<td>"."$genomic_coordinates"."</td>"."<td>"."$parsed_results->{$sort_key}->[1]_$parsed_results->{$sort_key}->[2]"."</td>"."<td>"."$parsed_results->{$sort_key}->[14]"."</td>"."</tr>";
  if($counter<26){
    print TOP25 "$output_line\n";
  }
  if($counter<51){
    print TOP50 "$output_line\n";
  }
  if($counter<76){
    print TOP75 "$output_line\n";
  }
  if($counter<101){
    print TOP100 "$output_line\n";
  }
  if($counter<501){
    print TOP500 "$output_line\n";
  }
  print ALL "$output_line\n";
  my ($sRNA_start,$sRNA_end) = split(/\-/,$parsed_results->{$sort_key}->[6]);
  #$output_line =  "$parsed_results->{$sort_key}->[0],$parsed_results->{$sort_key}->[1],$parsed_results->{$sort_key}->[2],$parsed_results->{$sort_key}->[3],$parsed_results->{$sort_key}->[4],$hypothetical_transcript_start,$hypothetical_transcript_end,$sRNA_start,$sRNA_end,$parsed_results->{$sort_key}->[7],$parsed_results->{$sort_key}->[8],$parsed_results->{$sort_key}->[9],$parsed_results->{$sort_key}->[10],$parsed_results->{$sort_key}->[11],\"$parsed_results->{$sort_key}->[12]\",$parsed_results->{$sort_key}->[13],$parsed_results->{$sort_key}->[14]";
  $output_line =  "$counter.,$parsed_results->{$sort_key}->[1],$parsed_results->{$sort_key}->[2],$parsed_results->{$sort_key}->[3],$parsed_results->{$sort_key}->[4],$hypothetical_transcript_start,$hypothetical_transcript_end,$sRNA_start,$sRNA_end,$parsed_results->{$sort_key}->[7],$parsed_results->{$sort_key}->[8],$parsed_results->{$sort_key}->[9],$parsed_results->{$sort_key}->[10],$parsed_results->{$sort_key}->[11],\"$parsed_results->{$sort_key}->[12]\",$parsed_results->{$sort_key}->[13],$parsed_results->{$sort_key}->[14],$parsed_results->{$sort_key}->[0]";
  print CSV $output_line,"\n";
}

#open (BUG,   ">$base_dir/$tempdir/bug");
#print BUG Dumper($parsed_results);

my $footer=	"</tbody>\n
		</table>\n
		<table style=\"display:none\">\n
		<tr><td id=\"hits\">$counter</td></tr>\n
		</table>\n";
		print TOP25 "$footer\n";
		print TOP50 "$footer\n";
		print TOP75 "$footer\n";
		print TOP100 "$footer\n";
		print TOP500 "$footer\n";
		print ALL "$footer\n";

close TOP25;
close TOP50;
close TOP75;
close TOP100;
close TOP500;
close ALL;
close CSV;
open (IANUMBER, ">$base_dir/$tempdir/interactionnumber");
#open (IANUMBER, ">$tempdir/interactionnumber");
print IANUMBER "$counter";
