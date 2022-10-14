"""
model_prediction.py
    This script predicts prioritization clusters using the saved MinMax scaler and K-Prototypes model and new 3-year raw data
"""

import pandas as pd
import joblib
from data_creation import data_for_clustering

##### The methodology works by bringing 3-year data. Before running the script, the person who runs it can modify the date
    ##### information below (year, month, day) and the script would automatically bring the 3-year data up to such date
cluster_df = data_for_clustering(2022, 3, 31)
##### Alternatively, for illustrative purposes, we could simply load existing data
#cluster_df = pd.read_csv("raw_data_predict_r.csv")

#### We load the saved MinMax scaler and estimated K-Prototypes model
scaler = joblib.load("scaler.mod")
clusterer = joblib.load("kprototypes.mod")

##### We take the features we use for the prediction
data_cluster = cluster_df[["HORARIO", "accidentes", "muertes", "heridos", "vulnerables"]].copy()

##### We scale the continuous features
cols = ["accidentes", "muertes", "heridos"]
maxv = scaler.data_max_.tolist()
minv = scaler.data_min_.tolist()
for i in range(0, len(cols)):
    data_cluster[cols[i]] = (data_cluster[cols[i]] - minv[i]) / (maxv[i] - minv[i])

##### We run the prediction    
clusters = clusterer.predict(data_cluster, categorical = [0, 4])

##### We append the predictions to the data
cluster_df = pd.concat((cluster_df, pd.DataFrame(clusters)), axis = 1)

##### When the labels are converted into a DataFrame, the column is called 0. We rename it
cluster_df.rename({0: "Prioridad"}, axis = 1, inplace = True)
##### From the analyses run when creating the model, we know what the labels in "clusters" represent. However, if the
    ##### K-Prototypes model is re-estimated, "dictp" must be revised
dictp = {0: "1 Priorizado", 1: "3 NA", 2: "2 Complementario"}
cluster_df.replace({"Prioridad": dictp}, inplace = True)
datap = cluster_df.sort_values(by = ["Prioridad", "vulnerables", "muertes", "muertes_vulnerables", "heridos_vulnerables"], \
    ascending = [True, False, False, False, False])
datap.to_csv("prioritized_corridors.csv", index = False)

del cluster_df
del data_cluster
del datap