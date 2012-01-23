require("topGO")#load toGo package read the data in tabular format
library("SubpathwayMiner")

paste(fil,go,kegg,gene_list,sep=" ")
#load all data
data<-read.table(fil,header=T,sep=",")
#load gene of interest
genelist<-read.table(gene_list,header=F)
#load go annotation
goannotation<-readMappings(go)
eco2GO<-inverseList(goannotation)
#load kegg annotation
#loadKe2g(kegg)

#GO statistics
geneNames <- names(eco2GO)
geneList<-factor(as.integer( geneNames %in% genelist$V1 ))
names(geneList)<-geneNames
#generate GO data objects
GOdataMF <- new("topGOdata", ontology = "MF", allGenes = geneList, annot = annFUN.gene2GO, gene2GO = eco2GO)
GOdataBP <- new("topGOdata", ontology = "BP", allGenes = geneList, annot = annFUN.gene2GO, gene2GO = eco2GO)
GOdataCC <- new("topGOdata", ontology = "CC", allGenes = geneList, annot = annFUN.gene2GO, gene2GO = eco2GO)
#generate results
resultMF<-runTest(GOdataMF, algorithm ="weight01", statistic="fisher")
resultBP<-runTest(GOdataBP, algorithm ="weight01", statistic="fisher")
resultCC<-runTest(GOdataCC, algorithm ="weight01", statistic="fisher")
#generate tables
allResMF<-GenTable(GOdataMF, weight01 = resultMF, orderBy="weight01", ranksOf="weight01", topNodes=20)
allResBP<-GenTable(GOdataBP, weight01 = resultBP, orderBy="weight01", ranksOf="weight01", topNodes=20)
allResCC<-GenTable(GOdataCC, weight01 = resultCC, orderBy="weight01", ranksOf="weight01", topNodes=20)

write.table(allResMF,sep=",",file=paste(output_path,"/MF.csv",sep=""))
write.table(allResBP,sep=",",file=paste(output_path,"/BP.csv",sep=""))
write.table(allResCC,sep=",",file=paste(output_path,"/CC.csv",sep=""))


#load background gene list (important)
#genelist<-read.table(gene_list,header=F)
#background_gene<-data$locus.id
##obtain annotation
#ann<-getAnn(genelist,background=background_gene)
##get tabulated results
#result<-printAnn(ann)
##print ten best pathways
#print(result[1:10,])
#nothing
