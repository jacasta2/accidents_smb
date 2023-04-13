"""
ml_api.py
    FastAPI app to predict prioritization clusters using the saved MinMax scaler and K-Prototypes model and
    new 3-year accident data
"""

import io
from calendar import isleap
from pydantic import BaseModel
import pandas as pd
from fastapi import FastAPI, Form, Depends
from fastapi.responses import StreamingResponse
from ml_functions import load_scaler, load_model, load_data

# Load the MinMaxScaler and the K-Prototypes model
scaler = load_scaler()
model = load_model()

# Define the input data model. The user only needs to input the date to retrieve 3-year data
# up to such date
class InputDate(BaseModel):
    """
    Class that defines the model input typing.
    """
    year: int = Form(ge = 2018, le = 2023)
    month: int = Form(ge = 1, le = 12)
    day: int = Form(ge = 1, le = 31)
    
# Create an instance of the FastAPI app
app = FastAPI()

# Define the endpoint to accept input data and return a prediction
@app.post("/predict/")
async def predict(input_data: InputDate = Depends()):
    """
    POST method to predict priority levels of highway corridors for implementing road safety operations
    using the clustering model K-Prototypes. Be aware the earliest date you can input is Jan 1 2018.
    
    Args:
        input_data: InputDate with the year, month and day information to load 3-year data up to such date
        
    Returns:
        .csv file with the highway corridors and their priority levels
    """

    if input_data.year == 2023 and input_data.month > 1:
        return {"Note:": "Be aware the database with accident data has info up to Jan 2023"}
    
    # Some months only have 30 days, so we make sure their last day is 30 in case the user inputs 31
    if input_data.month in (4, 6, 9, 11) and input_data.day == 31:
        input_data.day = 30
    # We do the same for Feb for non-leap years
    if input_data.month == 2 and not isleap(input_data.year) and input_data.day > 28:
        input_data.day = 28
    # We do the same for Feb for leap years
    if input_data.month == 2 and isleap(input_data.year) and input_data.day > 29:
        input_data.day = 29

    # We load the 3-year data for the prediction
    data = load_data(**dict(input_data))

    # We take the features we use for the prediction
    data_cluster = data[["HORARIO", "accidentes", "muertes", "heridos", "vulnerables"]].copy()

    # We scale the continuous features
    data_cluster[["accidentes", "muertes", "heridos"]] = scaler.fit_transform(data_cluster[["accidentes", "muertes", \
        "heridos"]])

    # We run the prediction
    clusters = model.predict(data_cluster, categorical = [0, 4])

    # We append the predictions to the data
    data = pd.concat((data, pd.DataFrame(clusters)), axis = 1)

    del data_cluster, clusters

    # When the labels are converted into a DataFrame, the column is called 0. We rename it
    data.rename({0: "Prioridad"}, axis = 1, inplace = True)
    
    # From the analyses run when creating the model, we know what the labels in "clusters" represent.
    # However, if the K-Prototypes model is re-estimated, "dictp" must be revised
    dictp = {0: "3 NA", 1: "2 Complementario", 2: "1 Priorizado"}
    data.replace({"Prioridad": dictp}, inplace = True)
    data.sort_values(by = ["Prioridad", "vulnerables", "muertes", "muertes_vulnerables", "heridos_vulnerables"], \
        ascending = [True, False, False, False, False], inplace = True)

    # Return the predictions as a dictionary
    #return data.to_dict("index")
    
    # Return the predictions as a .csv file for download
        # https://www.slingacademy.com/article/how-to-return-a-csv-file-in-fastapi/
    stream = io.StringIO()
    data.to_csv(stream, index = False)
    response = StreamingResponse(
        iter([stream.getvalue()]), media_type = "text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=prioritized_corridors.csv"
    return response
