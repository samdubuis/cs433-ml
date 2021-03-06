import datetime
time = datetime.datetime.now()
print("launched at : ", time)
import pandas as pd
import numpy as np

#!pip3 install surprise
from surprise import Reader
from surprise import Dataset
from surprise import SVD               # importer ici les algo qu'on testera
from surprise import model_selection
from surprise import dump

from sklearn.model_selection import train_test_split 

print("IMPORT DONE")

############
df = pd.read_csv("Datasets/data_train.csv")

df[["user", "item"]] = df.Id.str.split("_", expand=True)

df.user = df.user.str.replace("r", "")
df.item = df.item.str.replace("c", "")

#########
df2 = pd.read_csv("Datasets/sample_submission.csv")

df2[["user", "item"]] = df2.Id.str.split("_", expand=True)

df2.user = df2.user.str.replace("r", "")
df2.item = df2.item.str.replace("c", "")

df.Prediction.value_counts().plot.bar()


df_tenth, test = train_test_split(df, test_size=0.9, random_state=1)
df_quarter, test = train_test_split(df, test_size=0.75, random_state=1)


reader = Reader(rating_scale=(1,5)) 
data = Dataset.load_from_df(df[["user","item","Prediction"]], reader)
data_tenth = Dataset.load_from_df(df_tenth[["user","item","Prediction"]], reader)
data_quarter = Dataset.load_from_df(df_quarter[["user","item","Prediction"]], reader)



del df #freeing memory
del df_tenth
del df_quarter
print("PANDAS DONE, DATA AND READER ARE READY")
print("")

########

n_factors = list(map(int, input('Enter values for n_factors separated by , without space: ').split(',')))
n_epochs = list(map(int, input('Enter values for n_epochs separated by , without space: ').split(',')))
lr_all = list(map(float, input('Enter values for learning rate lr_all separated by , without space: ').split(',')))
reg_all = list(map(float, input('Enter values for regularization term rg_all separated by , without space: ').split(',')))

f=open("results.txt", "a")
f.write("\n")
f.write("{}\n".format(time))
f.write("n_factors : {}\n" .format(n_factors))
f.write("n_epochs : {}\n" .format(n_epochs))
f.write("learning rate lr_all : {}\n" .format(lr_all))
f.write("regularization term rg_all : {}\n" .format(reg_all))

param_grid = {
    'n_factors' : n_factors,
    'n_epochs': n_epochs,
    'lr_all': lr_all,
    'reg_all': reg_all
} 
cv=5
algorithm = SVD

n_jobs = int(input("Value for how many processors to use : (-1 is all, -2 is all except one) "))
print("")

#définition du model selon les paramètres, attention a importer dans la première cell les autres algos

#  https://surprise.readthedocs.io/en/stable/model_selection.html#surprise.model_selection.search.GridSearchCV

gs = model_selection.GridSearchCV(algorithm, param_grid, measures=['rmse'], cv=cv, n_jobs=n_jobs, joblib_verbose=100)  #enlever mae car non utilisé dans le projet pour sauver du temps

tasks = 1
for i in param_grid:
    tasks *= len(param_grid.get(i))

tasks *= cv
print("Total number of tasks to compute : ",tasks)
print("")

print("BEGINNING OF FITTING GRIDSEARCH")
var = int(input("Full data (0), quarter of data (1), tenth of the data (2) : "))
print("")

if var == 0:
    f.write("Full data \n")
    gs.fit(data) # les calculs se font actuellement ici 
if var == 1:
    f.write("Quarter of data \n")
    gs.fit(data_quarter)
if var == 2:
    f.write("Tenth of data \n")
    gs.fit(data_tenth)


print("FITTING GRIDSEARCH DONE")
print("")



print(gs.best_params)
print(gs.best_score)
f.write("Best param : {}\n" .format(gs.best_params))
f.write("Best score : {}\n" .format(gs.best_score))
f.write("\n")
f.close()

algo = gs.best_estimator["rmse"] #choix de l'algo selon l'erreur, touuuut inclus

print("FITTING OF DATA ON BEST ALGO")
algo.fit(data.build_full_trainset()) # ici on va train notre algo sur le dataset complet, sans cv car les paramètres sont optimaux

dump_name = "dump/dump_SVD_{}".format(time.date())
dump.dump(dump_name, algo, verbose=1)

array = np.ones((df2.shape[0],1))
change_five=0
change_zero=0

print("ROUNDING")
for i in df2.iterrows():
    tmp = algo.estimate(int(i[1][2])-1, int(i[1][3])-1)
    tmp = round(tmp)
    if int(tmp)>5:
      tmp=5;
      change_five +=1
    if int(tmp)<1:
      tmp=1;
      change_zero +=1
    array[i[0]]= (int(tmp))
    if i[0]%100000==0:
        print(i[0])

print("Changement de zero : ", change_zero)
print("Changement de cinq : ", change_five)


df2.Prediction = array
df2 = df2.drop(columns=["user", "item"])

out = "Datasets/submission_{}.csv" .format(time)
df2.to_csv(out, index=False)
print("")

print("EVERYTHING DONE")












