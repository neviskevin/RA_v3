from src import run_firerisk
import sys

def main():
    """
    Runs the Fire Risk Assessment given the coordinates of the geographical area in a shape (.shp) or geojson (.json) file

    Note:
    If you would like to run your own coordinate file, place your coordinate file in the "data/" folder and change "file_name"
    accordingly below

    The output will be a GeoTiff file located in this folder, a GeoJson file with Fire Risk, and the image of the geographical
    area
    :return: None
    """
    file_name = "collins_co_coordinates.json"
    # file_name = "collins_co_coordinates-polygon.shp"
    coordinate_file = f"data/{file_name}"

    run_firerisk(coordinate_file)


if __name__ == "__main__":
    main()
