"""
crosstab_heatmaps.py
    This script takes accidents where motorcycles were involved and generate crosstab heatmaps that show the degree to
    which each vehicle type was responsible for different combinations Severity-Accident type   
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
from date_creation import create_dates

##### The methodology works by bringing 3-year data. Before running the script, the person who runs it can modify the date
    ##### information below (year, month, day) and the script would automatically bring the 3-year data up to such date
date_interval = create_dates(2022, 12, 31)

# We connect to the database
db_conn = psycopg2.connect(
   database = "accidents_smb", user = "dev", password = "dev", host = "127.0.0.1", port = "5432"
)

##################################################
###
### For every vehicle involved in an accident with a motorcycle (except for motorcycles), we append the type and
### severity of the accident
###
##################################################
# 1. Select accidents where a motorcycle was involved
# 2. Select the vehicles (different from the motorcycle) involved in the accident
query = """
WITH moto_accidents AS (
    SELECT DISTINCT vehiculos.FORMULARIO FROM
    vehiculos
    JOIN siniestros ON siniestros.FORMULARIO = vehiculos.FORMULARIO
    WHERE substring(siniestros.FECHA_ACC, 1, 10) > '""" + date_interval[1] + """' AND
        substring(siniestros.FECHA_ACC, 1, 10) <= '""" + date_interval[0] + """' AND
        vehiculos.CLASE LIKE 'MOTOCICLETA'
)
SELECT siniestros.FORMULARIO, siniestros.CLASE_ACC, siniestros.GRAVEDAD, vehiculos.CLASE AS CLASE_VEH
FROM siniestros
JOIN moto_accidents ON moto_accidents.FORMULARIO = siniestros.FORMULARIO
JOIN vehiculos ON vehiculos.FORMULARIO = siniestros.FORMULARIO
WHERE vehiculos.CLASE NOT LIKE 'MOTOCICLETA'
"""
accidents1 = pd.read_sql(query, con = db_conn)

##################################################
###
### For every motorcycle involved with other motorcycles in an accident, we append the type and
### severity of the accident
###
##################################################
# 1. Select accidents where more than 1 motorcycle was involved
# 2. Select the motorcycles involved in the accident
query = """
WITH moto_accidents AS (
    SELECT vehiculos.FORMULARIO, COUNT(vehiculos.FORMULARIO) FROM
    vehiculos
    JOIN siniestros ON siniestros.FORMULARIO = vehiculos.FORMULARIO
    WHERE substring(siniestros.FECHA_ACC, 1, 10) > '""" + date_interval[1] + """' AND
        substring(siniestros.FECHA_ACC, 1, 10) <= '""" + date_interval[0] + """' AND
        vehiculos.CLASE LIKE 'MOTOCICLETA'
    GROUP BY vehiculos.FORMULARIO
    HAVING COUNT(vehiculos.FORMULARIO) > 1 
)
SELECT siniestros.FORMULARIO, siniestros.CLASE_ACC, siniestros.GRAVEDAD, vehiculos.CLASE AS CLASE_VEH
FROM siniestros
JOIN moto_accidents ON moto_accidents.FORMULARIO = siniestros.FORMULARIO
JOIN vehiculos ON vehiculos.FORMULARIO = siniestros.FORMULARIO
WHERE vehiculos.CLASE LIKE 'MOTOCICLETA'
"""
accidents2 = pd.read_sql(query, con = db_conn)

# We close the database connection
db_conn.close()

# We concatenate the results from both queries above
accidents3 = pd.concat(objs = [accidents1, accidents2], axis = 0)

##### We delete intermediate info
del accidents1
del accidents2

# For accidents where a motorcycle was involved, we generate a heatmap from a crosstab that shows the interaction
# between the vehicles involved and the accident severity and type. The crosstab is all-normalized, i.e., across all
# combinations Severity-Accident type, the heatmap shows the degree to which each vehicle type was responsible for each
# combination. We save the heatmap in a png image 
accidents_crosstab = pd.crosstab(index = [accidents3["gravedad"], accidents3["clase_acc"]], \
    columns = accidents3["clase_veh"], normalize = "all")*100
plt.figure(figsize = (12, 5))
sns.heatmap(accidents_crosstab, cmap = "Reds", cbar_kws = {"label": "Total %"})
plt.title("Vehicles involved and severity and type of accidents for motorcycle accidents: " + date_interval[1] + \
    " to " + date_interval[0], fontsize = 16, y = 1.05)
plt.xlabel("Vehicle type", fontsize = 13)
plt.ylabel("Severity and accident type", fontsize = 13)
plt.savefig("crosstab_heatmap_all.png", bbox_inches = "tight")

# For accidents where a motorcycle was involved, we generate a heatmap from a crosstab that shows the interaction
# between the vehicles involved and the accident severity and type. The crosstab is row-normalized, i.e., for each
# combination Severity-Accident type, the heatmap shows the degree to which each vehicle type was responsible for such
# combination. We save the heatmap in a png image 
accidents_crosstab = pd.crosstab(index = [accidents3["gravedad"], accidents3["clase_acc"]], \
    columns = accidents3["clase_veh"], normalize = "index")*100
plt.figure(figsize = (12, 5))
sns.heatmap(accidents_crosstab, cmap = "Reds", cbar_kws= {"label": "Row %"})
plt.title("Vehicles involved and severity and type of accidents for motorcycle accidents: " + date_interval[1] + \
    " to " + date_interval[0], fontsize = 16, y = 1.05)
plt.xlabel("Vehicle type", fontsize = 13)
plt.ylabel("Severity and accident type", fontsize = 13)
plt.savefig("crosstab_heatmap_rows.png", bbox_inches = "tight")