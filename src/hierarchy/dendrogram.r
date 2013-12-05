# Run with:
#   R --no-save --slave [path/to/data] [path/to/labels] [out] < dendrogram.r

args <- commandArgs();
dpth <- args[4];
lpth <- args[5];
opth <- args[6];
data <- read.table(dpth, header=FALSE, skip=0, sep=',')
lbls <- read.table(lpth, header=FALSE, skip=0, sep=',')

pdf(file=opth, height=5, width=10);
options(scipen=5)
# Bottom, Left, Top, Right
par(mai=c(0.1,0.1,0.1,0.1))

a <- list()
a$merge  <- as.matrix(data)
a$height <- 1:(length(lbls[,1])-1) * 1    # define merge heights
a$order  <- lbls[,1]
a$labels <- 0:(length(lbls[,1])-1)
class(a) <- "hclust"
# plot(a, hang=-1)
plot(
  a,
  axes=FALSE,
  main="")

