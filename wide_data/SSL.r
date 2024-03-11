library(parallel);library(foreach);library(doMC); library(readr);library(dplyr)

# whether to include covariates (age + birads), in addition to mmg; TRUE = exclude cov; FALSE = include cov
image.only = TRUE

# past history up to a landmark time
t_land = 3

#prediction horizon
delta_t = 5

long.df = read.csv('sample_long.csv')
wide.df = read.csv('sample_wide.csv')

long.df3 = data.frame(ID = long.df$group_id, visit_id = long.df$visit_id, event =long.df$event, 
                      ppid = long.df$group_id, since.bl.yr = long.df$since.bl.yr)

surv3 = data.frame(ID = wide.df$group_id, event = wide.df$event,
                   etime = wide.df$time, ppid = wide.df$group_id)

idx.LM.x = which(long.df3$since.bl.yr<=t_land)
long.df3 = long.df3[idx.LM.x,]

idx = which(long.df3$since.bl.yr<0)
if(length(idx)>0){long.df3 = long.df3[-idx,]}
length(unique(long.df3$ID))

idx.rm = which(!(surv3$ID %in% unique(long.df3$ID)))
if(length(idx.rm)>0){
  surv3 = surv3[-idx.rm,]
}

df.e = read.csv("output.csv")
ID = gsub('\t0', '', df.e$patient_exam_id)
df.e$patient_exam_id = ID

idx = which(!(long.df3$patient_id %in% df.e$patient_exam_id))
if(length(idx)>0){
  long.df3 = long.df3[-idx, ]
}

idx = which(!(df.e$patient_exam_id %in% long.df3$visit_id))
if(length(idx)>0){
  df.e = df.e[-idx,]
}

idx = which(!(surv3$ppid %in% unique(long.df3$ppid)))
if(length(idx)>0){
  surv3 = surv3[-idx,]
}
nrow(surv3)

# match the order of df to long.df (as long.df is sorted by time)
df.o.e = df.e[order(match(df.e$patient_exam_id, long.df3$visit_id)),]
dim(df.o.e)

long.df.sub1.e = long.df3
df.sub1.e = df.o.e

idx.rm = which(!(surv3$ppid %in% unique(long.df.sub1.e$ppid)))
if(length(idx.rm)>0){
  surv.sub1.e = surv3[-idx.rm,]
}else{
  surv.sub1.e = surv3
}

etime = LM_i.e = NULL
for(i in 1:nrow(surv.sub1.e)){
  idx = which(long.df.sub1.e$ppid %in% surv.sub1.e$ppid[i])
  idv.i = long.df.sub1.e[idx,]
  LM.i = max(idv.i$since.bl.yr)
  LM_i.e = c(LM_i.e, LM.i)
  etime = c(etime, (surv.sub1.e$etime[i]-LM.i) )
}

surv.sub1.e$etime = etime

idx = which(etime<0)

if(length(idx)>0){
  ppid.idx = surv.sub1.e[idx,]$ppid
  surv.sub1.e = surv.sub1.e[-idx,]
  LM_i.e = LM_i.e[-idx] # save later for age adjustment for SEER calibration
}

idx.rm = id.rm = NULL
for(i in ppid.idx){
  idx = which(long.df.sub1.e$ppid==i) 
  idx.rm = c(idx.rm, idx)
  id.rm = c(id.rm, long.df.sub1.e[idx,]$patient_id)
}
if(length(idx.rm)>0){
  long.df.sub1.e = long.df.sub1.e[-idx.rm,]
}

row.rm = NULL
for(i in id.rm){
  idx = which(df.sub1.e$patient_exam_id == i)
  row.rm = c(row.rm, idx)
}

if(length(row.rm)>0){
  df.sub1.e = df.sub1.e[-row.rm,]
}

df0.e = df.sub1.e

test.e <- as.matrix(df0.e)

Y.e <- matrix(as.numeric(as.matrix((surv.sub1.e[, c("etime", "event")]))), ncol=2)
colnames(Y.e) <- c("time", "status")

X.e <- matrix(as.numeric(as.matrix(test.e[, -1])), ncol=(512*4))

Xm = NULL
for(i in 1:ncol(X.e)){
  Xm = cbind(Xm, (X.e[,i]-col.mean[i])) # this is the col.mean from training
}

X.e = Xm

X.e <- X.e/max(svd.save$d) # this is the max(svd) from training

xtest <- X.e
Ytest <- Y.e

TuningParameters <- read.rds('TuningParameters')
EstimatorMatrix <- read.rds('EstimatorMatrix')

registerDoMC(20)
errs = foreach(sim = 1:dim(xtest)[1]) %dopar%{
  vecTime <- Ytest[sim, 1]
  status <- Ytest[sim, 2]
  
  cat("  -> Personalized calibration... ")
  tuneSelect <- PersonalizedLog(as.vector(xtest[sim, ]), 
                                TuningParameters, 
                                EstimatorMatrix)
  
  pCoxTune <- which(TuningParameters==tuneSelect)
  cat("done\n")
  
  cat("  -> Computing results... ")
  
  vec <- as.vector(xtest[sim, ])
  
  estimator <- EstimatorMatrix[, pCoxTune]
  cat("done\n")
    
  return(list(exp(vec%*%estimator)))
}


rscore = NULL
for(i in 1:dim(xtest)[1]){
  rscore = c(rscore, errs[[i]][[1]])
}









