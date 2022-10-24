"""
date_creation.py
    Function used to engineer date strings used in the crosstab heatmaps 
"""

import pandas as pd

def create_dates(year, month, day):
    """
    This function returns date strings to retrieve 3-year data up to day defined by the date year-month-day. 

    Args:
        year: date argument
        month: date argument
        day: date argument
    
    Returns:
        list with end and start dates
    """

    if len(str(month)) == 1:
        month = str(0) + str(month)
    else:
        month = str(month)
    if len(str(day)) == 1:
        day = str(0) + str(day)
    else:
        day = str(day)

    fecha = str(year) + "-" + str(month) + "-" + str(day)
    fecha2 = str(pd.to_datetime(fecha) - pd.DateOffset(years = 3))[0:10]

    return [fecha, fecha2]