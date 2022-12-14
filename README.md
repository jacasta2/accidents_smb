# accidents_smb

The following description corresponds to the **Clustering** and **Motorcycles and other vehicles** modules of this project. Among the many tasks the Secretary of Mobility of Bogotá (SMB) does, they implement road safety operations aiming at reducing accidents, especially from motorcyclists given their higher accident risk. Currently, the locations where such operations are implemented are determined manually crossing information from several Excel files. The clustering module pulls information on accidentes and the city's road grid to find highway corridors with different priority levels for implementing road safety operations.

The main challenge for developing this project is the lack of 'useful' information on highway corridors. The road grid available has either too long or too short corridors, which does not allow to locate sections of the corridors to focus on for implementing road safety operations. A future implementation should relate different geographical sources to locate each accident on shorter corridors within the long main corridors from the available road grid file.

Another challenge was the initial ETL process to pull accident data from an ArcGIS service and populate a local postgres database with such data. This is explained with some detail in the following section. A feature I hope to implement in the future would allow to pull data from this service every month to keep the database up to date.
 
## Clustering

### Getting started

The script `model_creation.py` provided in this module connects to a local postgres database created to develop this project. Such database is populated with accident data retrieved from a publicly available ArcGIS service with data from all the accidents reported in the city. The database was populated with data from 2015 to August 2022. The folder **initial_etl** contains the Jupyter notebooks that allowed to retrieve such data and populate the database. While this initial ETL process could be automatized for the *Siniestro*, *Con Muerto* and *Con Herido* layers or tables, the lack of date information in the remaining layers (*Vehiculo*, *Causa* and *Actor Vial*) and the impossibility of executing JOIN operations in the service make difficult to automatize such process for these layers. Instead, the process was done using the OBJECTID field of these layers in a somewhat manual process. 

Despite the issues mentioned above, the folder **initial_etl** provides the necessary shapefiles to populate the database with data from 2015 to August 2022. Please check the Jupyter notebook `4_database_creation.ipynb` to see how this was done. Make sure to create the database beforehand and adjust the database connection parameters in the notebook accordingly. 

### Using the scripts

The main scripts of this module are `model_creation.py` and `model_prediction.py`. These are stored in the folder **clustering**. Before running any of the scripts, please unrar the .rar file in the folder **clustering** and read the following sections.

#### model_creation.py

This script uses functions from `data_creation.py` to pull 3-year data on accidents and then fits the K-Prototypes clustering algorithm to such data using 3 clusters. The script saves the MinMaxScaler and K-Prototypes parameters in separate files that are later loaded by `model_prediction.py`. The files are named **scaler.mod** and **kprototypes.mod**, respectively.

The user can change the arguments of the function `data_for_clustering(2021, 12, 31)` to bring data for a specific 3-year period. Once they are modified, the user can run the script and it will automatically pull the 3-year data up to the modified date and fit the K-Prototypes algorithm. To run this script, open a terminal and run:

```
python model_creation.py
```

The clusters should be updated with certain periodicity. Every time this script is run to update the clusters, the user should manually inspect the results to properly label the data in `model_prediction.py`. The Jupyter notebook `model_creation.ipynb` provides code that plots several strip plots that can help in such inspection. The results of this inspection must be implemented in a dictionary, which is explained in the following section.

Ultimately, the clusters should indicate a 3-level priority scheme: (i) corridors that should be prioritized for road safety operations, (ii) complementary corridors on which road safety operations could be implemented and (iii) remaining corridors. While this could arguably be the ultimate purpose of this module (i.e., the SMB could already use the clusters generated by this script to prioritize corridors for road safety operations), these clusters are used in `model_prediction.py` to predict the clusters for more recent 3-year data and prioritize corridors for road safety operations based on these predicted clusters.

#### model_prediction.py

This script loads the following information:

* The MixManScaler parameters used to scale the data feeded to the K-Prototypes algorithm, which are contained in **scaler.mod**.
* The resulting K-Prototypes parameters, which are contained in **kprototypes.mod**.

The user can change the arguments of the function `data_for_clustering(2022, 3, 31)` to bring data for a specific 3-year period. Once they are modified, the user can run the script and it will automatically pull the 3-year data up to the modified date and predict its priority clusters. 

Before running this script, the user needs to inspect the clustering results from `model_creation.py` and modify the dictionary in the following line of code from `model_prediction.py` accordingly:

```
dictp = {0: "1 Priorizado", 1: "3 NA", 2: "2 Complementario"}
```

The line of code above assumes the label **0** generated by `model_creation.py` represents the corridors with the highest priority, label **2** the complementary corridors and label **3** the remaining corridors.

After inspecting the labels and implementing the necessary changes to the dictionary, the user can run the script to generate the file **prioritized_corridors.csv**, which will contain the corridors with their predicted priority levels. The SMB should load this file to the Power BI dashboard they were provided with. To run this script, open a terminal and run:

```
python model_prediction.py
``` 

This module is already provided with files that allow to run a test. These files are:

* **scaler_r.mod:** contains the MinMaxScaler parameters used when scaling the continuous features before fitting the clustering model.
* **kprototypes_r.mod:** contains the K-Prototypes model fitted with 3-year data from 2019 to 2021.
* **raw_data_predict_r.csv:** contains 3-year data up to March 31, 2022.

The test will predict the priority levels for the 3-year data from **raw_data_predict_r.csv**. It requires to run only `model_prediction.py` commenting line 12, uncommenting line 14 and changing the names of the scaler and model files in lines 17 and 18 by appending *_r* to them.

## Motorcycles and other vehicles

### Using the script

The main script of this module is `crosstab_heatmaps.py`. This is stored in the folder **motorcycle_accidents**. This folder also provides the corresponding Jupyter notebook to play with the implementation of this module. Before running the script, please make sure to create the database and adjust the database connection parameters in the script accordingly. The section **Clustering** provides details on this.

The script `crosstab_heatmaps.py` uses the function from `date_creation.py` to pull 3-year data on accidents where motorcycles were involved and generates crosstab heatmaps that show the degree to which each vehicle type was responsible for different combinations of severity and accident type. The user can change the arguments of the function `create_dates(2021, 12, 31)` to bring data for a specific 3-year period. Once they are modified, the user can run the script and it will automatically pull the 3-year data up to the modified date and generate the heatmaps. To run this script, open a terminal and run:

```
python crosstab_heatmaps.py
```

The script generates 2 heatmaps, all and row-normalized, and saves them in two png files named **crosstab_heatmap_all.png** and **crosstab_heatmap_rows.png**, respectively.

### Credits

**Team 185:** Andrés Felipe Jaramillo, Felipe De La Cruz, Jaime Andrés Castañeda, Jose Pestana, Nicolás Armando Cabrera and Santiago Forero.

**Sponsors:** Correlation One and the Colombian Ministry of Information Technologies and Communications (MinTIC).

We thank our **DS4A | Colombia 2022 TAs**, Julián Leonardo García and Juan José Rodríguez, for their valuable support. We also thank the Secretary of Mobility of Bogotá for providing access to data and subject-matter expertise to develop this project.