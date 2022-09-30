from src import RiskAssesmentML


def main():
    features = {
        "temp": ("data/wc2.1_30s_tavg_06.tif", None),
        "vapr": ("data/wc2.1_30s_vapr_06.tif", None),
        "wind": ("data/wc2.1_30s_wind_06.tif", None),
        "prec": ("data/wc2.1_30s_prec_06.tif", None),
        "B3": ("data/LC08_L2SP_044032_20210711_20210720_02_T1_SR_B3.TIF", None),
        "B4": ("data/LC08_L2SP_044032_20210711_20210720_02_T1_SR_B4.TIF", None),
        "B5": ("data/LC08_L2SP_044032_20210711_20210720_02_T1_SR_B5.TIF", None),
        "B6": ("data/LC08_L2SP_044032_20210711_20210720_02_T1_SR_B6.TIF", None),
        "slope": (["data/n40_w121_1arc_v2.tif", "data/n40_w122_1arc_v2.tif"], "merged_n40_arc_dem_data"),
        "aspect": (["data/n40_w121_1arc_v2.tif", "data/n40_w122_1arc_v2.tif"], "merged_n40_arc_dem_data"),
        "elevation": (["data/n40_w121_1arc_v2.tif", "data/n40_w122_1arc_v2.tif"], "merged_n40_arc_dem_data")
    }

    data_path = "data"

    coordinate_file = "data/collins_co_coordinates.json"

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

    fire_data_path = "/Users/ishaan/Documents/GitHub/risk_assesment_sum22/data/WFIGS_-_Wildland_Fire_Locations_Full_History.csv"

    fire_risk_ml = RiskAssesmentML(fire_data_path, coordinate_file, data_path, rule_list, features)
    fire_risk_ml.run_ml_train()


if __name__ == "__main__":
    main()
