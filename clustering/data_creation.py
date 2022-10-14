"""
data_creation.py
    Functions used to engineer the data used in the prioritization clustering 
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import psycopg2

def vulnerable(muertesv, heridosv):
    """
    This function creates an indicator of the degree of severity of accidentes in a highway corridor.

    Args:
        muertesv: the number of vulnerable killed people.
        heridosv: the number of vulnerable injured people. 

    Returns:
        The degree of severity.
            0: neither killed nor injured vulnerable people
            1: injured vulnerable people but no killed vulnerable people
            2: killed vulnerable people
    """
    
    if muertesv == 0 and heridosv == 0:
        return 0 
    elif heridosv > 0 and muertesv == 0:
        return 1
    else:
        return 2

def data_for_clustering(year, month, day):
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

    db_conn = psycopg2.connect(
        database = "accidents_smb", user = "dev", password = "dev", host = "127.0.0.1", port = "5432"
    )

    ##### 1. Bring highway corridor grid with no CIV duplicates 
    ##### 2. Bring corridors with accidents (per day of week per hour)
    ##### 3. Append injured people from accidentes with only injured people (per corridor per day of week per hour)
    ##### 4. Append killed and injured people from accidents with killed people (per corridor per day of week per hour)
    ##### 5. Append other relevant info (per corridor per day of week per hour)

    ##################################################
    ###
    ### 1. Bring highway corridor grid with no CIV duplicates 
    ###
    ##################################################
    ### We bring the Malla Vial
    malla = gpd.read_file("Malla_Vial_Integral_Bogota_r2.geojson")
    ### We take relevant info from it
    malla_short = malla[["MVICIV", "MVINOMBRE"]].copy()
    ### We rename some columns so that they match with the columns from siniestros
    malla_short.rename(columns = {"MVICIV": "CIV"}, inplace = True)
    ### We perform some basic cleaning
    malla_short_nonan = malla_short[malla_short["CIV"].notna()]
    ### A highway corridor with a given CIV might have multiple records in Malla Vial. We must drop duplicates on CIV (caveat:
        ### we keep the first one with whatever info it has on PK_CALZADA) so that we can append MVINOMBRE to accidents
    malla_short_no_dup = malla_short_nonan.drop_duplicates("CIV")
    malla_short_clean = malla_short_no_dup[malla_short_no_dup["MVINOMBRE"].notna()].copy()

    ##### We delete intermediate info
    del malla
    del malla_short
    del malla_short_nonan
    del malla_short_no_dup

    ##################################################
    ###
    ### 2. Bring corridors with accidents (per day of week per hour)
    ###
    ##################################################
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

    ##### We bring info on accidents
    query = """
    SELECT FORMULARIO, CIV, DIA_OCURRENCIA_ACC, HORA_OCURRENCIA_ACC
    FROM siniestros
    WHERE substring(FECHA_ACC, 1, 10) > '""" + fecha2 + """' AND
        substring(FECHA_ACC, 1, 10) <= '""" + fecha + """'
    """
    accidentes = pd.read_sql(query, con = db_conn)
    accidentes.columns = accidentes.columns.str.upper()
    
    ##### We remove corridors with useless CIV (corridor) info
    accidentes["CIV"].replace({0: np.nan}, inplace = True)
    accidentes_nonan = accidentes[accidentes["CIV"].notna()].copy()
    ##### We groupby() accidents info to count the number of accidents
    cant_accidentes = accidentes_nonan.groupby(["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"]).size().\
        reset_index(name = "accidentes")

    ##################################################
    ###
    ### 3. Append injured people from accidentes with only injured people (per corridor per day of week per hour)
    ###
    ##################################################
    ##### We bring info on accidents with injured people (but not deaths)
    query = """
    SELECT siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC,
        COUNT(conheridos.FORMULARIO) AS heridos
    FROM siniestros
    JOIN conheridos ON conheridos.FORMULARIO = siniestros.FORMULARIO
    WHERE substring(siniestros.FECHA_ACC, 1, 10) > '""" + fecha2 + """' AND
        substring(siniestros.FECHA_ACC, 1, 10) <= '""" + fecha + """' AND
        siniestros.GRAVEDAD = 'CON HERIDOS'
    GROUP BY siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC
    ORDER BY heridos DESC
    """
    heridos = pd.read_sql(query, con = db_conn)
    heridos.columns = heridos.columns.str.upper()
    heridos.rename({"HERIDOS": "heridos"}, axis = 1, inplace = True)
    
    ##### We remove corridors with useless CIV (corridor) info
    heridos["CIV"].replace({0: np.nan}, inplace = True)
    heridos_nonan = heridos[heridos["CIV"].notna()].copy()
    ##### We groupby() injured people info to sum the number of injured people
    cant_heridos = heridos_nonan.groupby(["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"])["heridos"].sum().\
        reset_index(name = "heridos")

    ##################################################
    ###
    ### 4. Append killed and injured people from accidents with killed people (per corridor per day of week per hour)
    ###
    ##################################################
    ##### We bring info on accidents with killed people and append to them the number of injured people
    query = """
    WITH fallecidos AS (
        SELECT siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC,
            COUNT(confallecidos.FORMULARIO) AS muertes
        FROM siniestros
        JOIN confallecidos on confallecidos.FORMULARIO = siniestros.FORMULARIO
        WHERE substring(siniestros.FECHA_ACC, 1, 10) > '""" + fecha2 + """' AND
            substring(siniestros.FECHA_ACC, 1, 10) <= '""" + fecha + """'
        GROUP BY siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC
    )
    SELECT fallecidos.FORMULARIO, fallecidos.CIV, fallecidos.DIA_OCURRENCIA_ACC, fallecidos.HORA_OCURRENCIA_ACC,
        fallecidos.muertes, COUNT(conheridos.FORMULARIO) AS heridos
    FROM fallecidos
    LEFT JOIN conheridos ON conheridos.FORMULARIO = fallecidos.FORMULARIO
    GROUP BY fallecidos.FORMULARIO, fallecidos.CIV, fallecidos.DIA_OCURRENCIA_ACC, fallecidos.HORA_OCURRENCIA_ACC,
        fallecidos.muertes
    ORDER BY fallecidos.muertes DESC, heridos DESC
    """
    muertes = pd.read_sql(query, con = db_conn)
    muertes.columns = muertes.columns.str.upper()
    muertes.rename({"MUERTES": "muertes", "HERIDOS": "heridos"}, axis = 1, inplace = True)
    
    ##### We remove corridors with useless CIV (corridor) info
    muertes["CIV"].replace({0: np.nan}, inplace = True)
    muertes_nonan = muertes[muertes["CIV"].notna()].copy()
    ##### We groupby() killed and injured people info to sum the number of killed and injured people
    cant_muertes = muertes_nonan.groupby(["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"])[["muertes", "heridos"]].sum().\
        reset_index()

    ##################################################
    ###
    ### 5. Append other relevant info (per corridor per day of week per hour)
    ###
    ##################################################
    ##################################################
    ### Append injured vulnerable people from accidentes with only injured vulnerable people (per corridor per day of week per
    ### hour)
    ##################################################
    ##### We bring the number of vulnerable road actors injured in accidents
    query = """
    SELECT siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC, 
        COUNT(conheridos.FORMULARIO) FILTER (WHERE conheridos.CONDICION IN ('PEATON', 'CICLISTA', 'MOTOCICLISTA'))
            AS heridos_vulnerables 
    FROM siniestros
    JOIN conheridos ON conheridos.FORMULARIO = siniestros.FORMULARIO
    WHERE substring(siniestros.FECHA_ACC, 1, 10) > '""" + fecha2 + """' AND
        substring(siniestros.FECHA_ACC, 1, 10) <= '""" + fecha + """' AND
        siniestros.GRAVEDAD = 'CON HERIDOS'
    GROUP BY siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC
    ORDER BY heridos_vulnerables DESC
    """
    heridosv = pd.read_sql(query, con = db_conn)
    heridosv.columns = heridosv.columns.str.upper()
    heridosv.rename({"HERIDOS_VULNERABLES": "heridos_vulnerables"}, axis = 1, inplace = True)
    
    ##### We remove corridors with useless CIV (corridor) info
    heridosv["CIV"].replace({0: np.nan}, inplace = True)
    heridosv_nonan = heridosv[heridosv["CIV"].notna()].copy()
    ##### We groupby() injured vulnerable people info to sum the number of injured vulnerable people
    cant_heridosv = heridosv_nonan.groupby(["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"])["heridos_vulnerables"].sum().\
        reset_index()

    ##################################################
    ### Append killed and injured vulnerable people from accidentes with killed vulnerable people (per corridor per day of week
    ### per hour)
    ##################################################
    ##### We bring the number of vulnerable road actors killed and injured in accidents with killed vulnerable people
    query = """
    WITH fallecidos AS (
        SELECT siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC, 
            COUNT(confallecidos.FORMULARIO) FILTER (WHERE confallecidos.CONDICION IN ('PEATON', 'CICLISTA', 'MOTOCICLISTA'))
                AS muertes_vulnerables 
        FROM siniestros
        JOIN confallecidos ON confallecidos.FORMULARIO = siniestros.FORMULARIO
        WHERE substring(siniestros.FECHA_ACC, 1, 10) > '""" + fecha2 + """' AND
            substring(siniestros.FECHA_ACC, 1, 10) <= '""" + fecha + """'
        GROUP BY siniestros.FORMULARIO, siniestros.CIV, siniestros.DIA_OCURRENCIA_ACC, siniestros.HORA_OCURRENCIA_ACC
    )
    SELECT fallecidos.FORMULARIO, fallecidos.CIV, fallecidos.DIA_OCURRENCIA_ACC, fallecidos.HORA_OCURRENCIA_ACC,
        fallecidos.muertes_vulnerables,
        COUNT(conheridos.FORMULARIO) FILTER (WHERE conheridos.CONDICION IN ('PEATON', 'CICLISTA', 'MOTOCICLISTA'))
            AS heridos_vulnerables
    FROM fallecidos
    LEFT JOIN conheridos ON conheridos.FORMULARIO = fallecidos.FORMULARIO
    GROUP BY fallecidos.FORMULARIO, fallecidos.CIV, fallecidos.DIA_OCURRENCIA_ACC, fallecidos.HORA_OCURRENCIA_ACC,
        fallecidos.muertes_vulnerables
    ORDER BY fallecidos.muertes_vulnerables DESC, heridos_vulnerables DESC
    """
    muertesv = pd.read_sql(query, con = db_conn)
    db_conn.close()
    
    muertesv.columns = muertesv.columns.str.upper()
    muertesv.rename({"MUERTES_VULNERABLES": "muertes_vulnerables", "HERIDOS_VULNERABLES": "heridos_vulnerables"}, axis = 1, \
        inplace = True)
    
    ##### We remove corridors with useless CIV (corridor) info
    muertesv["CIV"].replace({0: np.nan}, inplace = True)
    muertesv_nonan = muertesv[muertesv["CIV"].notna()].copy()
    ##### We groupby() killed vulnerable people info to sum the number of killed vulnerable people
    cant_muertesv = muertesv_nonan.groupby(["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"])[["muertes_vulnerables", \
        "heridos_vulnerables"]].sum().reset_index()

    ##### We bring everything together, including the corridor names
    accidentes_malla = pd.merge(cant_accidentes, cant_heridos, how = "left", on = ["CIV", "DIA_OCURRENCIA_ACC", \
        "HORA_OCURRENCIA_ACC"]).merge(cant_muertes, how = "left", on = ["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"]).\
        merge(cant_heridosv, how = "left", on = ["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"]).\
        merge(cant_muertesv, how = "left", on = ["CIV", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"]).\
        merge(malla_short_clean, how = "left", on = "CIV")
    ##### We remove corridors with no name
    accidentes_malla_clean = accidentes_malla[accidentes_malla["MVINOMBRE"].notna()].copy()
    ##### We fill features with 0s when applicable 
    accidentes_malla_clean.fillna(value = 0, inplace = True)
    ##### We adjust some features 
    accidentes_malla_clean["heridos"] = accidentes_malla_clean["heridos_x"] + accidentes_malla_clean["heridos_y"]
    accidentes_malla_clean["heridos_vulnerables"] = accidentes_malla_clean["heridos_vulnerables_x"] + \
        accidentes_malla_clean["heridos_vulnerables_y"]
    accidentes_malla_clean.drop(columns = ["heridos_x", "heridos_y", "heridos_vulnerables_x", "heridos_vulnerables_y"], \
        axis = 1, inplace = True)
    accidentes_malla_clean["muertes"] = accidentes_malla_clean["muertes"].astype(int)
    accidentes_malla_clean["heridos"] = accidentes_malla_clean["heridos"].astype(int)
    accidentes_malla_clean["muertes_vulnerables"] = accidentes_malla_clean["muertes_vulnerables"].astype(int)
    accidentes_malla_clean["heridos_vulnerables"] = accidentes_malla_clean["heridos_vulnerables"].astype(int)

    ##### We groupby() to sum all the relevant features
    info_siniestros = accidentes_malla_clean.groupby(["MVINOMBRE", "DIA_OCURRENCIA_ACC", "HORA_OCURRENCIA_ACC"])\
        [["accidentes", "muertes", "heridos", "muertes_vulnerables", "heridos_vulnerables"]].sum().reset_index()

    ##### We delete intermediate info
    del accidentes
    del accidentes_malla
    del accidentes_malla_clean
    del heridos
    del heridos_nonan
    del heridosv
    del heridosv_nonan
    del muertes
    del muertes_nonan
    del muertesv
    del muertesv_nonan
    del cant_accidentes
    del cant_heridos
    del cant_heridosv
    del cant_muertes
    del cant_muertesv

    ##### We create the hour blocks (Lissett's version)
    d1 = {
        0: "Nocturno 22-2",
        1: "Nocturno 22-2",
        2: "Nocturno 2-5",
        3: "Nocturno 2-5",
        4: "Nocturno 2-5",
        5: "DiurnoMan 5-8",
        6: "DiurnoMan 5-8",
        7: "DiurnoMan 5-8",
        8: "DiurnoMan 8-12",
        9: "DiurnoMan 8-12",
        10: "DiurnoMan 8-12",
        11: "DiurnoMan 8-12",
        12: "DiurnoTarde 12-18",
        13: "DiurnoTarde 12-18",
        14: "DiurnoTarde 12-18",
        15: "DiurnoTarde 12-18",
        16: "DiurnoTarde 12-18",
        17: "DiurnoTarde 12-18",
        18: "NocturnoTarde 18-22",
        19: "NocturnoTarde 18-22",
        20: "NocturnoTarde 18-22",
        21: "NocturnoTarde 18-22",
        22: "Nocturno 22-2",
        23: "Nocturno 22-2",
    }
    info_siniestros["HORARIO"] = info_siniestros["HORA_OCURRENCIA_ACC"].map(d1)

    ##### We keep corridors with deaths 
    # Create list with corridors that had 0 deaths
    lstm = info_siniestros.groupby("MVINOMBRE")["muertes"].sum()[info_siniestros.groupby("MVINOMBRE")["muertes"].sum() == 0].\
        index.to_list()
    # Create df without such corridors
    info_siniestrosm = info_siniestros[~info_siniestros["MVINOMBRE"].isin(lstm)]

    ##### We groupby() using the corridors, days and time blocks
    info_siniestrosmh = info_siniestrosm.groupby(["MVINOMBRE", "DIA_OCURRENCIA_ACC", "HORARIO"])[["accidentes", "muertes", \
        "heridos", "muertes_vulnerables", "heridos_vulnerables"]].sum().reset_index()

    ##################################################
    ###
    ### Final preparation
    ###
    ##################################################
    ##### We create the data for the clustering prediction
    cluster_df = info_siniestrosmh.copy()

    ##### Day of week seems somewhat irrelevant according to a basic EDA not reported here. We get rid of it
    # We groupby() using the corridors and time blocks
    cluster_df = cluster_df.groupby(["MVINOMBRE", "HORARIO"])[["accidentes", "muertes", "heridos", "muertes_vulnerables", \
        "heridos_vulnerables"]].sum().reset_index()

    cluster_df["vulnerables"] = cluster_df.apply(lambda x: vulnerable(x["muertes_vulnerables"], x["heridos_vulnerables"]), \
        axis = 1)
    cluster_df["vulnerables"] = cluster_df["vulnerables"].astype("category")

    ##### We delete intermediate info
    del info_siniestros
    del info_siniestrosm
    del info_siniestrosmh

    return cluster_df