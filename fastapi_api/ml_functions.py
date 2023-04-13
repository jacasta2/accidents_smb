"""
ml_functions.py
    Supporting functions for the FastAPI app
"""

import joblib
from data_creation import data_for_clustering

def load_scaler():
    """
    This function returns the MinMaxScaler.

    Returns:
        Loaded MinMaxScaler
    """
    return joblib.load("../clustering/scaler.mod")

def load_model():
    """
    This function returns the K-Prototypes model.

    Returns:
        Loaded K-Prototypes model
    """
    return joblib.load("../clustering/kprototypes.mod")

def load_data(year, month, day):
    """
    This function creates the DataFrame used for the prioritization clustering. The DataFrame includes 3-year data up
    to the day defined by the date year-month-day. 

    Args:
        year: date argument
        month: date argument
        day: date argument
    
    Returns:
        DataFrame
    """
    return data_for_clustering(year, month, day)
