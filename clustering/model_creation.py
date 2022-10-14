"""
model_creation.py
    This scripts generates the MinMax scaler and the K-Prototypes model used for the prioritization clustering.
    
    Every time this script is run the results must be checked to make sure the labels are properly assigned in
    prioritized_corridors.csv, which is the data used in Power BI (this file is created in model_prediction.py).
    
    Please check the corresponding notebook to explore some code that allows to check the results
"""

import pandas as pd
from sklearn import preprocessing
from kmodes.kprototypes import KPrototypes
import joblib
from data_creation import data_for_clustering

##### The methodology works by bringing 3-year data. Before running the script, the person who runs it can modify the date
    ##### information below (year, month, day) and the script would automatically bring the 3-year data up to such date
cluster_df = data_for_clustering(2021, 12, 31)

##### We remove the corridors and the number of killed and injured vulnerable people to perform the clustering (the basic EDA
    ##### mentioned in data_creation.py revealed the number of killed and injured vulnerable people were redundant)
##### We normalize the continuous data 
cluster_df_norm = cluster_df[["HORARIO", "accidentes", "muertes", "heridos", "vulnerables"]].copy()

del cluster_df

scaler = preprocessing.MinMaxScaler()
cluster_df_norm[["accidentes", "muertes", "heridos"]] = scaler.fit_transform(cluster_df_norm[["accidentes", "muertes", \
    "heridos"]])

##### We save the scaler
joblib.dump(scaler, "scaler.mod")

##### We apply the clustering
kproto = KPrototypes(n_clusters = 3, init = "Cao")
clusters = kproto.fit_predict(cluster_df_norm, categorical = [0, 4])

##### We save the model
joblib.dump(kproto, "kprototypes.mod")