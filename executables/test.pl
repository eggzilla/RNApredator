#!/usr/bin/perl -w
use strict;
use Bio::DB::Taxonomy;
my $dbdir = '/scratch2/egg/webserv/data/lists/taxdump/';
my $db = Bio::DB::Taxonomy->new(-source => 'flatfile',
                                 -nodesfile => "$dbdir/nodes.dmp",
                                 -namesfile => "$dbdir/names.dmp",
                                 );
my $taxa = $db->get_taxon(-taxonid => 2);
my @d = $db->get_all_Descendents($taxa);

print join("\n", map { $_->id . " " . $_->rank . " " .
$_->scientific_name } @d), "\n"; 
