# Run with:
#   R --no-save --slave [path/to/data] [out] < cost.r

args <- commandArgs();
dpth <- args[4];
opth <- args[5];
data <- read.table(dpth, header=FALSE, skip=0, sep='\t')

pdf(file=opth, height=5, width=10);
options(scipen=5)
# Bottom, Left, Top, Right
par(mai=c(0.9,0.9,0.1,0.1))

plot(
  data,
  type='l',
  xlab='Iteration',
  ylab='Cost')
