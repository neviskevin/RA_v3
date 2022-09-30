from . import MakeData


def run_firerisk(coordinate_file):
    """
    Function to run the risk assessment model using the MakeData class
    :param: coordinate_file: Path to GeoJson or Shape file for cropping rasters to polygon shape (str)
    :return: None
    """
    # Path to the data folder
    data_path = "data"

    # "FEATURE NAME": ("FEATURE FILE", "MERGE NAME FILE")
    # If you want to get up to date data using the Ambee API, use the following
    features = {}
    
   # features = {
   #     "temp": ("data/wc2.1_30s_tavg_06.tif", None),
   #     "vapr": ("data/wc2.1_30s_vapr_06.tif", None),
   #     "wind": ("data/wc2.1_30s_wind_06.tif", None),
   #     "prec": ("data/wc2.1_30s_prec_06.tif", None),
   # }
    
    rule_list = {
        "temp": "rules/temp_rules.txt",
        "vapr": "rules/vapr_rules.txt",
        "wind": "rules/wind_rules.txt",
        "prec": "rules/prec_rules.txt",
        "aspect": "rules/aspect_rules.txt",
        "slope": "rules/slope_rules.txt",
        "elevation": "rules/elevation_rules.txt",
        "ndmi": "rules/ndmi_rules.txt",
        "ndvi": "rules/ndvi_rules.txt",
        "ndwi": "rules/ndwi_rules.txt"
    }

    data = MakeData(coordinate_file, data_path, rule_list, feature_set=features)

    # Processing data - calculates fire risk given input data
    data.process_data()

    # Shows fire risk map
    data.show_fire_risk()

    # Create fire risk tif file
    data.create_fire_risk_tif()
    data.create_fire_risk_geojson()

    # Deletes all temp data
    data.del_temp_files()

    print("Success!")
    return 0
