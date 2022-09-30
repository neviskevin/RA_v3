import os
import shutil

import fiona
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import json
import geojson

from sklearn.linear_model import LinearRegression
from tqdm import tqdm
from .tif_data import TifData
from .get_data import DownloadData
from .ambee_data import AmbeeData


class MakeData:
    def __init__(self, coordinate_file, data_path, rule_list, feature_set={}, download_files=False, create_csv=True):
        """
        MakeData is used to create feature sets, conduct ML analysis, and export output as both csv and GeoTiff rasters.

        :param coordinate_file: Path to GeoJson or Shape file for cropping rasters to polygon shape (str)
        :param data_path: Path to all data files (str)
        :param rule_list: Rules mapping final feature data to classified data (dict: name of feature -> path to rule file)
        :param feature_set: All features used for Risk Assessment Model
                    (dict: name of feature -> tuple (path to raster, merged_file_name)
        :param create_csv: Whether to create output csv files (bool)
        """
        self.data_path = data_path
        self.temp_path = data_path + "C:\Users\Administrator\Desktop\risk_assesment_sum22\src\data\temp"
        try:
            os.mkdir(self.temp_path)
        except FileExistsError:
            pass

        self.coords_file = coordinate_file
        self.shapes = self.__make_shape()

        self.get_weather = False
        if len(feature_set) == 0:
            self.get_weather = True
            self.weather_data = {'temp': [], 'vapr': [], 'wind': [], 'prec': []}
            self.ambee = AmbeeData()
        if download_files:
            downloader = DownloadData(feature_set, self.shapes)
            downloader.download_data()

        self.input_data = {}
        for data_name in tqdm(feature_set.keys(), desc='Creating Data'):
            feature_file = feature_set[data_name][0]
            merge_name = feature_set[data_name][1]
            self.input_data[data_name] = TifData(data_name, feature_file, merge_name=merge_name)
        self.data_classification = self.__make_reclassifier_from_rules(rule_list)

        self.width, self.height = 0, 0
        self.transform = np.array([])
        self.meta = {}

        self.pd_data = None
        self.fire_np_arr = np.array([])

        self.create_csv = create_csv

    def __make_shape(self):
        """
        Creates shape features based on the polygon geometry in the shape file
        - Shape file generated is used to clip (or crop) geographical areas of other tif files
        :return: List of shape geometry (GeoJson)
        """
        filetype = self.coords_file.split(".")[-1]
        if filetype == "shp":
            with fiona.open(self.coords_file, "r") as shapefile:
                shapes = [feature["geometry"] for feature in shapefile]
                return shapes
        elif filetype == "json":
            geojson_file = open(self.coords_file)
            shapes = json.load(geojson_file)
            return [shapes]

    def process_data(self):
        """
        Processes data to create features and calculate fire risk
        - Calls other class methods
        :return: None
        """
        # Clip files to shape coordinates
        self.clip_files()
        # Match all data to have the same size
        self.resample_data()
        # Create pandas df
        self.create_clip_pd()
        # Calculate nd features
        self.calc_nd_data()
        # Reclassify data
        self.classify_data()
        # Calculate fire risk
        self.calc_fire_risk()

    def create_clip_pd(self):
        """
        Creates Pandas df object from all input data, matches data points to coordinates in real world
        - creates pandas df in self.pd_data
        - Creates data.csv if create_csv is True (bool)
        :return: None
        """
        risk_data = []

        for i in tqdm(range(self.height), desc='Creating Coordinates'):
            for j in range(self.width):
                coordinates = self.transform * (i, j)
                risk_data.append(coordinates)
                if self.get_weather:
                    #self.get_weather_ambee(coordinates[1], coordinates[0])
                    self.get_weather_ambee(coordinates[1], coordinates[0])

        risk_data = np.array(risk_data)
        columns = ['x', 'y']

        for feature_name in tqdm(self.input_data.keys(), desc='Creating Pandas DF'):
            columns.append(feature_name)
            data = self.input_data[feature_name].get_data(data_type="match")
            data = np.reshape(data, (self.height*self.width, 1))
            risk_data = np.hstack((risk_data, data))

        if self.get_weather:
            for feature_name in tqdm(self.weather_data, desc='Convering Weather data to Pandas DF'):
                columns.append(feature_name)
                weather_data = self.weather_data[feature_name]
                weather_data = np.transpose(np.array([weather_data]))
                risk_data = np.hstack((risk_data, weather_data))

        risk_pd = pd.DataFrame(risk_data, columns=columns)
        risk_pd.fillna(-9999, inplace=True)
        if self.create_csv:
            risk_pd.to_csv('data.csv')
        self.pd_data = risk_pd

    def classify_data(self):
        """
        Classifies all features in self.pd_data, replaces data in place
        - Creates reclassified_data.csv if create_csv is True (bool)
        :return: None
        """
        for feature_name in tqdm(self.data_classification.keys(), desc='Classifying Data'):
            feature_bins = self.data_classification[feature_name][0]
            feature_dict = self.data_classification[feature_name][1]
            try:
                np_feature = self.pd_data[feature_name].to_numpy()
            except KeyError as e:
                print(f"{e}, {feature_name} does not exist in dataset, cannot classify data")
                return None
            classified_feature = np.digitize(np_feature, feature_bins, right=False)
            if feature_dict:
                for k in feature_dict.keys():
                    classified_feature[classified_feature == k] = feature_dict[k]
            self.pd_data.drop(columns=[feature_name], inplace=True)
            self.pd_data[feature_name] = classified_feature
        if self.create_csv:
            self.pd_data.to_csv('reclassified_data.csv')

    def calc_fire_risk(self):
        """
        Calculates fire risk using pandas dataframe
        - Creates fire_risk.csv if create_csv is True (bool)
        :return: None
        """
        self.pd_data['fire_risk'] = 0.12 * self.pd_data['aspect'] + 0.0751 * self.pd_data['elevation'] + \
                                    0.03 * self.pd_data['vapr'] + 0.251 * self.pd_data['ndvi'] + \
                                    0.125 * self.pd_data['ndmi'] + 0.125 * self.pd_data['ndwi'] + \
                                    0.024 * self.pd_data['prec'] + 0.0749 * self.pd_data['slope'] + \
                                    0.154 * self.pd_data['temp'] + 0.021 * self.pd_data['wind']
        if self.create_csv:
            self.pd_data.to_csv('fire_risk.csv')
        fire_np_arr = self.pd_data['fire_risk'].to_numpy()
        self.fire_np_arr = np.reshape(fire_np_arr, (self.height, self.width))

        # X_features = self.pd_data[['aspect', 'elevation', 'vapr', 'ndvi', 'ndmi', 'ndwi', 'prec', 'slope', 'temp', 'wind']].to_numpy()
        # y_labels = self.pd_data['fire_risk'].to_numpy()
        # weights = [0.12, 0.0751, 0.03, 0.251, 0.125, 0.125, 0.024, 0.0749, 0.154, 0.021]
        # reg = LinearRegression().fit(X_features, y_labels)
        # score = reg.score(X_features, y_labels)

    def show_fire_risk(self):
        """
        Displays fire risk plot
        :return: None
        """
        plt.imshow(self.fire_np_arr, cmap='YlOrRd', vmin=0, vmax=9)
        plt.show()

    def clip_files(self):
        """
        Crops all files in features using shapes, creates feature.clip_data object

        Finds self.width and self.height which resembles maximum density of data in clip file
        :return: None
        """
        for feature in self.input_data.values():
            feature.clip_file(self.shapes)
            if feature.clip_data.width > self.width and feature.clip_data.height > self.height:
                self.width = feature.clip_data.width
                self.height = feature.clip_data.height
                self.transform = feature.get_transform("clip")
                self.meta = feature.get_meta("clip")
        self.meta.update({"driver": "GTiff", "height": self.height, "width": self.width, "transform": self.transform})

    def resample_data(self):
        """
        Resamples data to match data dimensions and transform of input data to self.width and self.height
        :return: None
        """
        for feature in self.input_data.values():
            feature.resample_data(self.width, self.height)

    def del_temp_files(self):
        """
        Deletes all temp files created
        :return: None
        """
        try:
            shutil.rmtree(self.temp_path)
        except OSError as e:
            print("Error: %s : %s" % (self.temp_path, e.strerror))

    @staticmethod
    def __make_reclassifier_from_rules(rule_list):
        """
        Creates data classification dictionary, mapping features to bins and classified
        :param rule_list: dict mapping features to rule.txt files (dict)
        :return: dict mapping features to bins, classification dictionary
        """
        data_classifier = {}
        for feature_name in rule_list.keys():
            classifier_rule_file = open(rule_list[feature_name], 'r')
            classifier_rules = classifier_rule_file.readlines()
            classifier_rules = [line.strip().replace(" ", "") for line in classifier_rules]
            classifier_rules = [line.split("=") for line in classifier_rules]

            classifier = dict()
            for i in range(len(classifier_rules)):
                classifier[i+1] = float(classifier_rules[i][1])

            classifier_rules = [line[0].split("to") for line in classifier_rules]
            bins = [float(classifier_rules[0][0])]
            for line in classifier_rules:
                bins.append(float(line[1]))
            data_classifier[feature_name] = (bins, classifier)
        return data_classifier

    def calc_nd_data(self):
        """
        Calculates ndvi, ndmi, ndwi features from B3, B4, B5, and B6 layers
        - Changed self.pd_data in place
        :return: None
        """
        self.pd_data["ndvi"] = (self.pd_data["B5"] - self.pd_data["B4"]) / (self.pd_data["B5"] + self.pd_data["B4"])
        self.pd_data["ndmi"] = (self.pd_data["B5"] - self.pd_data["B6"]) / (self.pd_data["B5"] + self.pd_data["B6"])
        self.pd_data["ndwi"] = (self.pd_data["B3"] - self.pd_data["B6"]) / (self.pd_data["B3"] + self.pd_data["B6"])
        self.pd_data.drop(columns=['B3', 'B4', 'B5', 'B6'], inplace=True)
        self.pd_data.fillna(-9999, inplace=True)

    def create_fire_risk_tif(self, output_name="fire_risk.tif"):
        """
        Creates output TIF file for fire_risk
        :param output_name: Name for fire risk output file (str)
        :return: None
        """
        output_meta = self.meta
        output_data = np.reshape(self.fire_np_arr, (1, np.shape(self.fire_np_arr)[0], np.shape(self.fire_np_arr)[1]))
        with rasterio.open(output_name, "w", **output_meta) as dest:
            dest.write(output_data)

    def get_feature_data(self, feature_name):
        """
        Gets data column for a specific data
        :param feature_name: Name of feature (str)
        :return: Column data (pd object)
        """
        try:
            return self.pd_data[feature_name]
        except KeyError:
            print("Key does not exist")

    def get_tif_data(self, data_name):
        """
        Gets TIF data object for a specific data
        :param data_name: Name of data (str)
        :return: TIF Data object (Rasterio Object)
        """
        try:
            return self.input_data[data_name]
        except KeyError:
            print("Key does not exist")

    def get_pd_dataframe(self):
        """
        Gets current pandas dataframe
        :return: pd dataframe
        """
        return self.pd_data

    def get_weather_ambee(self, lat, lng):
        """
        Gets current weather data using Ambee API given a latitude and longitude coordinate
        - Appends the updated weather in self.weather_data
        :param lat: Latitude coordinate (float)
        :param lng: Longitude coordinate (float)
        :return: None
        """
        weather_lat_lon = self.ambee.get_weather_lat_lon(lat, lng)
        for feature in self.weather_data:
            self.weather_data[feature].append(weather_lat_lon[feature])

    def create_fire_risk_geojson(self):
        """
        Converts output fire_risk values to a GeoJson file, mapping values to a long lat coordinate
        - Saves output as firerisk.geojson
        :return: None
        """
        features = []
        insert_features = lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X["x"],
                                                    X["y"])),
                            properties=dict(fire_risk=X["fire_risk"])))
        self.pd_data.apply(insert_features, axis=1)
        with open('firerisk.geojson', 'w', encoding='utf8') as fp:
            geojson.dump(geojson.FeatureCollection(features), fp, sort_keys=True, ensure_ascii=False)
