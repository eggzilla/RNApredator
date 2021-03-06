#!/usr/bin/perl -w -I /home/mescalin/htafer/rnaplex-0.1/perl_plex/blib/arch -I/home/mescalin/htafer/rnaplex-0.1/perl_plex/blib/lib
use strict;
use Getopt::Std;
use FileHandle;
my %opts;
getopt('besudf', \%opts);
#b -> begin of interaction
#e -> end of interaction
#s -> sequence
if(defined($opts{s}) && defined($opts{b}) && defined($opts{e})){
    if(!defined($opts{d})){
	$opts{d}=-200;
    }
    if(!defined($opts{f})){
	$opts{f}=200;
    }
    $opts{u}=4;
    check_accessibility();
    `R CMD BATCH *.R`;
}
else
{
    usage();
}
sub usage
{
	print "compute the accessibility profile for a given interaction";
}

sub parse_sequence
{
	my $file=readfile($opts{s});
	my $hash;
	return $file->[1];
}

sub readfile
{
    my $name=shift;
    open(TMP, "$name") || die "cant open $name\n";
    my @array=<TMP>;
    close(TMP);
    return \@array;
}

sub check_accessibility
{
	my $sequences=parse_sequence($opts{s}); #read sequence from file
	chomp($sequences);
	#RNAUP
	#RNAup unconstraint
	my $RNAup;
	#`echo "$sequences" | RNAup -u $opts{u} && mv RNA_u$opts{u}.out unconstraint.out`;
	`echo "$sequences" | /u/html/RNApredator2/executables/RNAup -u $opts{u} && mv RNA_u1.out unconstraint.out`;
	#RNAup constraint
	my $constraint;
	$constraint="." x ($opts{b}-1).
	    "x" x ($opts{e}-$opts{b}+1).
	    "." x (length($sequences)-$opts{e});
	#`echo "$sequences\n$constraint" | RNAup -C -u $opts{u} && mv RNA_u$opts{u}.out constraint.out`;
	`echo "$sequences\n$constraint" | /u/html/RNApredator2/executables/RNAup -C -u $opts{u} && mv RNA_u1.out constraint.out`;
	my $constrained=readfile("constraint.out");
	my $unconstrained=readfile("unconstraint.out");
	#put data in datafile
	open(OUT,">data.out");
	print OUT "pos_const const pos_unconst unconst";
	for(my $i=0; $i<$#$constrained+1; $i++){
	    next if($constrained->[$i]=~/#/);
	    $constrained->[$i]=~s/^\s+//;
	    $unconstrained->[$i]=~s/^\s+//;
	    chomp($constrained->[$i]);
	    chomp($unconstrained->[$i]);
	    print OUT $constrained->[$i]," ",$unconstrained->[$i],"\n";
	}
	#generate plot
	open(R, ">tmp.R");
	print R "data<-read.table(\"data.out\", header=TRUE)\n".
	    "png(\"$opts{s}.png\", width=480,height=320)\n".
	    #"postscript(\"$opts{s}.ps\", paper=\"a4\")\n".
	    "plot(data\$pos_const-200, (data\$const-data\$unconst), xlab=\"position\", ylab=substitute(paste(Delta, \"G\")),main=\"Accessibility profile with u=4\",type=\"line\",ylim=c(-5,5),xlim=c($opts{d},$opts{f}), lwd=2)\n".
	    "lines(data\$pos_const-200, data\$const, col=\"green\", lwd=2)\n".
	    "lines(data\$pos_const-200, data\$unconst, col=\"red\", lwd=2)\n".
	    "abline(v=0, col=\"turquoise\", lwd=2)\n".
	    "abline(v=$opts{b}-200, col=\"blue\", lwd=2)\n".
	    "abline(v=$opts{e}-200, col=\"blue\", lwd=2)\n".
	    "abline(h=0, lwd=1, lty=3)\n".
	    "dev.off()\n";
	close(R);
}

sub produce_plot
{
	my $Data=shift;
	open(ENERGY,">energy.out");
	print ENERGY "mRNA ncRNA RNAup Gu_short Gu_long RNAcofold t_begin t_endi m_length n_length\n";
	foreach my $mRNA (keys %{$Data}){
		foreach my $ncRNA (keys %{$Data->{$mRNA}}){
			print ENERGY "$mRNA $ncRNA  $Data->{$mRNA}->{$ncRNA}->{E_RNAup} ".
				     "$Data->{$mRNA}->{$ncRNA}->{t_Gu_s} $Data->{$mRNA}->{$ncRNA}->{g_Gu} $Data->{$mRNA}->{$ncRNA}->{E_cofold} ".
				     "$Data->{$mRNA}->{$ncRNA}->{t_begin} $Data->{$mRNA}->{$ncRNA}->{t_end} ".
				     length($Data->{$mRNA}->{$ncRNA}->{mRNA})." ". length($Data->{$mRNA}->{$ncRNA}->{ncRNA})."\n";
			open(OUT, ">$mRNA$ncRNA.csv");
			print OUT "position p_before p_after t_pu t_pu_const t_Gu t_Gu_const pint G_int\n";
			for(my $i=0; $i<length($Data->{$mRNA}->{$ncRNA}->{mRNA}); $i++){
				print OUT $i," ",$Data->{$mRNA}->{$ncRNA}->{p_before}->{$i+1}," ",
				      $Data->{$mRNA}->{$ncRNA}->{p_after}->{$i+1}," ",
				      $Data->{$mRNA}->{$ncRNA}->{t_pu}->[$i]," ",
				      $Data->{$mRNA}->{$ncRNA}->{t_pu_const}->[$i]," ",
				      $Data->{$mRNA}->{$ncRNA}->{t_Gu}->[$i]," ",
				      $Data->{$mRNA}->{$ncRNA}->{t_Gu_const}->[$i]," ",
				      $Data->{$mRNA}->{$ncRNA}->{pint}->[$i]," ",
				      $Data->{$mRNA}->{$ncRNA}->{Gint}->[$i],"\n";
		        }
			close(OUT);
			open(R, ">$mRNA$ncRNA.R");
			my $name=$mRNA.$ncRNA;
			print R "data<-read.table(\"$name.csv\", header=TRUE)\n".
				"postscript(\"$name.ps\", paper=\"a4\")\n".
				"par(mfrow=c(2,1))\n".
				"plot(data\$position, (data\$p_after-data\$p_before), xlab=\"position\", ylab=substitute(paste(Delta, \"p\")),main=\"$name Prob of being pair (pafter-pbefore) plot Ecof=$Data->{$mRNA}->{$ncRNA}->{E_cofold} Eup=$Data->{$mRNA}->{$ncRNA}->{E_RNAup}\", type=\"line\", xlim=c($Data->{$mRNA}->{$ncRNA}->{ATG}-200, $Data->{$mRNA}->{$ncRNA}->{ATG}+50), ylim=c(-1,1))\n".
				"lines(data\$position, data\$p_after, col=\"turquoise\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{ATG}, col=\"red\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{SD}, col=\"green\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{t_begin}, col=\"blue\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{t_end}, col=\"blue\")\n".
				"plot(data\$t_Gu_const-data\$t_Gu, xlab=\"position\", ylab=substitute(paste(Delta,\"E\")),main=\"$name Energy plot Ecof=$Data->{$mRNA}->{$ncRNA}->{E_cofold} Eup=$Data->{$mRNA}->{$ncRNA}->{E_RNAup}\",type=\"line\",xlim=c($Data->{$mRNA}->{$ncRNA}->{ATG}-200, $Data->{$mRNA}->{$ncRNA}->{ATG}+50), ylim=c(-5,5))\n".
				"lines(data\$position, data\$t_Gu_const, col=\"turquoise\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{ATG}, col=\"red\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{SD}, col=\"green\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{t_begin}, col=\"blue\")\n".
				"abline(v=$Data->{$mRNA}->{$ncRNA}->{t_end}, col=\"blue\")\n".
				"dev.off()\n";
			close(R);
		}
	}
	
	close(ENERGY);
}

sub parse_RNAup_output
{
	my $filename=shift;
	my $file=readfile($filename);
	my $hash;#(contains all information)
	my $flag;
	foreach my $line (@{$file}){
		if($line=~/^# total probability of being unpaired$/){
			$flag="pu_long";
			next;
		}
		elsif($line=~/^# free energy to open all structures$/){
			$flag="Gu_long";
			next;

		}
		elsif($line=~/^# total probability of being unpaired in shorter sequence$/){
			$flag="pu_short";
			next;

		}
		elsif($line=~/^# free energy to open all structures in shorter sequence/){
			$flag="Gu_short";
			next;

		}
		elsif($line=~/^# interaction probability/){
			$flag="pint";
			next;

		}
		elsif($line=~/^# free energy of interaction/){
			$flag="Gint";
			next;

		}
		elsif($line=~/\&/){
			next ;
		}
		else{
			$line=~/\s*(\d+)\s+(\-*\d+\.\d+)/;
			push @{$hash->{$flag}}, $2;
		}
	}
	my $add=$opts{u};
	while($add>1){
		unshift(@{$hash->{pu_long}},0);
		unshift(@{$hash->{Gu_long}},0);
		unshift(@{$hash->{pu_short}},0);
		unshift(@{$hash->{Gu_short}},0);
		$add--;
	}
	return $hash;
}

sub parse_DotPlot_output
{
	my $filename=shift;
	my $file=readfile($filename);
	my $hash;
	foreach my $line (@{$file}){
		next unless ($line=~/\d\subox$/);
		my ($i, $j, $p, $id) = split(/\s/, $line);
		$p=$p*$p;
		$hash->{$i}+=$p;
		$hash->{$j}+=$p;
	}
	return $hash;
}

##sub mean
#{
#    my $nrj=$_[0];
#    my $energy=0;
#    my $variance=0;
#    my $stddv=0;
#    my $mean=0;
#    foreach my $item (@{$nrj}) {$energy+=$item;}
#    $mean=$energy/($#$nrj+1);
#    foreach my $item (@{$nrj}) {$variance+=($item-$mean)**2;}
#    $stddv = sqrt($variance/($#$nrj+1));
#    return($mean)
#}
#
#sub global_compute_access
#{
#	my $ncRNAseq=shift;
#	my $mRNAseq=shift;
#	my $hit=shift;
#	my $u_ncRNA=$hit->{g_end}-$hit->{g_begin};
#	my $u_mRNA=$hit->{t_end}-$hit->{t_begin};
#	`echo $mRNAseq | ~berni/RNAexec64i/RNAplfold -W $opts{w} -L $opts{l} -u $u_mRNA`;
#	my $pos=$hit->{t_end};
#	chomp(my $mRNAaccess=`grep -P "^$pos " plfold_unp`);
#	my $length=length($ncRNAseq);
#	$pos=$hit->{g_begin};
#	if($pos<$u_ncRNA){
#		$ncRNAseq=reverse $ncRNAseq;
#		$pos=$length-$pos;
#	}
#	`echo $ncRNAseq | ~berni/RNAexec64i/RNAplfold -W $length -L $opts{l} -u $u_ncRNA`;
#	chomp(my $ncRNAaccess=`grep -P "^$pos " plfold_unp`);
#	$mRNAaccess=~s/^(\d+\s)//;
#	$ncRNAaccess=~s/^(\d+\s)//;
#	$mRNAaccess+=0.000001;
#	$ncRNAaccess+=0.000001;
#	return [$mRNAaccess, $ncRNAaccess];
#}
#sub parse_line
#{
#	my $line=shift;
#	$line=~/([^\s]*)\s([^:]*):([^:]*):(\d+),(\d+)\s+([\(\)\.\&]*)\s+(\d+),(\d+)\s+(\-\d+)/;
#	my $hit;
#	$hit->{ncRNA}=$1;
#	$hit->{mRNA}=$2.":".$3;
#	$hit->{t_begin}=$4;
#	$hit->{t_end}=$5;
#	$hit->{structure}=$6;
#	$hit->{g_begin}=$7;
#	$hit->{g_end}=$8;
#	$hit->{energy}=$9;
#	return $hit;
#}
#
