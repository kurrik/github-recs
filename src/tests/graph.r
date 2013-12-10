# Run with:
#   R --no-save --slave [path/to/data] [out] [label] < graph.r

args <- commandArgs();
dpth <- args[4];
opth <- args[5];
main <- args[6];
data <- read.table(dpth, header=TRUE, skip=0, sep='\t')

m    <- dim(data)[1]
n    <- dim(data)[2]

plotdata <- as.matrix(data[,c(2:n)])
plotlbls <- as.vector(data[,1])

pdf(file=opth, height=5, width=10);
options(scipen=5)
# Bottom, Left, Top, Right
# par(mai=c(0.9,0.9,0.1,0.1))

barplot(
  plotdata,
  main=main,
  ylab=main,
  beside=TRUE,
  col=rainbow(m)
);

legend("topleft",
  plotlbls,
  cex=1.0,
  bty="n",
  fill=rainbow(m)
);
