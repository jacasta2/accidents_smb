"""
model_prediction.py
    This script predicts prioritization clusters using the saved MinMax scaler and K-Prototypes model and new 3-year raw data
"""

import pandas as pd
import joblib
from data_creation import data_for_clustering

##### The methodology works by bringing 3-year data. Before running the script, the person who runs it can modify the date
    ##### information below (year, month, day) and the script would automatically bring the 3-year data up to such date
cluster_df = data_for_clustering(2022, 12, 31)
##### Alternatively, for illustrative purposes, we could simply load existing data
#cluster_df = pd.read_csv("raw_data_predict.csv")

#### We load the saved MinMax scaler and estimated K-Prototypes model
scaler = joblib.load("scaler.mod")
clusterer = joblib.load("kprototypes.mod")

##### We take the features we use for the prediction
data_cluster = cluster_df[["HORARIO", "accidentes", "muertes", "heridos", "vulnerables"]].copy()

##### We scale the continuous features
data_cluster[["accidentes", "muertes", "heridos"]] = scaler.fit_transform(data_cluster[["accidentes", "muertes", \
    "heridos"]])

##### We run the prediction    
clusters = clusterer.predict(data_cluster, categorical = [0, 4])

##### We append the predictions to the data
cluster_df = pd.concat((cluster_df, pd.DataFrame(clusters)), axis = 1)

##### When the labels are converted into a DataFrame, the column is called 0. We rename it
cluster_df.rename({0: "Prioridad"}, axis = 1, inplace = True)
##### From the analyses run when creating the model for the first time, we know what the labels in "clusters" represent.
    ##### However, if the K-Prototypes model is re-estimated, "dictp" must be revised
dictp = {0: "3 NA", 1: "2 Complementario", 2: "1 Priorizado"}
cluster_df.replace({"Prioridad": dictp}, inplace = True)
datap = cluster_df.sort_values(by = ["Prioridad", "vulnerables", "muertes", "muertes_vulnerables", "heridos_vulnerables"], \
    ascending = [True, False, False, False, False])
datap.to_csv("prioritized_corridors.csv", index = False)

del cluster_df, data_cluster, datap