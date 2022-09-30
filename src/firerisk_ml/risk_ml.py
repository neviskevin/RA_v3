import time

from src.data import MakeData, AmbeeData
import pandas as pd
from datetime import datetime as dt
import numpy as np
import sklearn
from sklearn.linear_model import SGDClassifier, RidgeClassifier, LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import LinearSVC


class RiskAssesmentML:
    def __init__(self, fire_data, coordinate_file, data_path, rule_list, features={}, auto_download=False, classify=False,
                 accurate_weather=False, model='svm', sample_frac=0.002):
        """
        Creates Regression ML Models on feature data matched to fire history data for fire risk regression

        :param fire_data: Path to the fire history data csv (str)
        :param coordinate_file: Path to GeoJson or Shape file for cropping rasters to polygon shape (str)
        :param data_path: Path to all data files (str)
        :param rule_list: Rules mapping final feature data to classified data (dict: name of feature -> path to rule file)
        :param features: All features used for Risk Assessment Model
                            (dict: name of feature -> tuple (path to raster, merged_file_name)
        :param auto_download: Whether to auto-download feature data from USGS (bool)
        :param classify: Whether or not to use classified data for the model

        NOTE:
        - This function does not currently support the classified data with accurate weather. To integrate this
          functionality, you will need to use rules.txt to classify the new accurate weather when obtained
        """
        self.ambee = AmbeeData()

        self.feature_input = self.__make_feature_data(coordinate_file, data_path, rule_list, features, auto_download, classify)
        self.fire_data = self.__make_fire_data(fire_data)
        self.ml_data = None
        self.X, self.y = None, None
        self.sample_frac = sample_frac

        self.accurate_weather = accurate_weather

        self.model = model

    def run_ml_train(self):
        """
        Fits the input data self.X to the labels self.y and returns the score of the model, as well as the model parameters
        - self.model: Which scikit learn model to use ('log_reg', 'sgd', 'svm', 'ridge', 'gbc') (str)
        :return: Score of model and sk-learn model parameters (tuple)
        """
        self.__clean_data_for_ml()
        if self.model == 'log_reg':
            reg = LogisticRegression().fit(self.X, self.y)
        elif self.model == 'sgd':
            reg = SGDClassifier().fit(self.X, self.y)
        elif self.model == 'ridge':
            reg = RidgeClassifier().fit(self.X, self.y)
        elif self.model == 'svm':
            reg = LinearSVC().fit(self.X, self.y)
        elif self.model == 'gbc':
            reg = GradientBoostingClassifier(max_depth=5, min_weight_fraction_leaf=0.01).fit(self.X, self.y)
        else:
            return None, None, None
        score, params = reg.score(self.X, self.y), reg.get_params()
        return score, reg.coef_, reg.intercept_

    @staticmethod
    def __make_feature_data(coordinate_file, data_path, rule_list, features, auto_download, classify):
        """
        Creates a Pandas Dataframe of input features assigned to longitude and latitude coordinates
        - The shape (and size) of the data is based on the coordinate file provided
        - To expand the size of the training data for the ml model, change the size of the shape in the coordinate file
        - To auto-download the data, set auto_download to be True - DEM, Landsat-8 will automatically be downloaded
        :param coordinate_file: Path to GeoJson or Shape file for cropping rasters to polygon shape (str)
        :param data_path: Path to all data files (str)
        :param rule_list: Rules mapping final feature data to classified data (dict: name of feature -> path to rule file)
        :param features: All features used for Risk Assessment Model
                        (dict: name of feature -> tuple (path to raster, merged_file_name)
        :param auto_download: Whether to auto-download all DEM and weather data (bool)
        :return: Pandas Dataframe containing all feature data for the coordinate file range (df)
        """
        data = MakeData(coordinate_file, data_path, rule_list, feature_set=features, download_files=auto_download)
        data.clip_files()
        data.resample_data()
        data.create_clip_pd()
        data.calc_nd_data()
        if classify:
            data.classify_data()
        pd_data = data.get_pd_dataframe()
        return pd_data

    def __make_fire_data(self, fire_data_path):
        """
        Creates a pandas dataframe of the output data with various output labels - input data can be used to predict
        different outputs if needed

        - Currently the only columns used are defined in cols below
        - Crops data to the area defined in the coordinate input file and keeps only WildFire data

        data link can be found here:
        https://data-nifc.opendata.arcgis.com/datasets/nifc::wfigs-wildland-fire-locations-full-history/explore?location=37.759441%2C-118.096584%2C6.29

        :param fire_data_path: Path to the fire history data csv (str)
        :return: Pandas dataframe of the label data (df)
        """
        cols = ['X', 'Y', 'FireCause', 'FireDiscoveryDateTime', 'DailyAcres', 'CalculatedAcres', 'IncidentTypeCategory']
        fire_history_data = pd.read_csv(fire_data_path, usecols=cols)
        fire_history_data[['DailyAcres']] = fire_history_data[['DailyAcres']].fillna(value=0.001)

        x_clip, y_clip = self.__get_min_max_coords()
        filtered_data = fire_history_data[fire_history_data['X'] <= x_clip[0]]
        filtered_data = filtered_data[filtered_data['X'] >= x_clip[1]]
        filtered_data = filtered_data[filtered_data['Y'] <= y_clip[0]]
        filtered_data = filtered_data[filtered_data['Y'] >= y_clip[1]]
        filtered_data = filtered_data[filtered_data['IncidentTypeCategory'] == 'WF']

        return filtered_data

    def __combine_and_clean_data(self):
        """
        Combines the Feature input data and the Fire Data Labels to create one pandas df for ML training and testing
        Note:
        - The cleaned data will drop the columns defined in cols_to_drop, feel free to change this to learn different models
        - The cleaned data will drop any invalid numbers

        :return: Pandas df for ml modeling with features matched to fire labels (df)
        """
        xy_coords = self.fire_data[["X", "Y"]].apply(tuple, axis=1).tolist()
        closest_idxs = self.__find_closest_coord_idx(xy_coords)
        closest_input_data = self.feature_input.iloc[closest_idxs]

        sample_data = self.feature_input.copy()
        sample_data.drop(closest_idxs)
        sample_data = sample_data.sample(frac=self.sample_frac)
        closest_input_data['fire'] = 1
        sample_data['fire'] = 0
        ml_data = pd.concat([closest_input_data, sample_data], axis=0, ignore_index=True)
        """
        new_fire_data = self.fire_data.copy()
        cols_to_drop = ['X', 'Y', 'CalculatedAcres', 'IncidentTypeCategory', 'FireCause']
        new_fire_data.drop(columns=cols_to_drop, inplace=True)
        ml_data = pd.concat([closest_input_data.reset_index(drop=True), new_fire_data.reset_index(drop=True)], axis=1)
        """

        for column in ml_data:
            if ml_data[column].dtypes == 'float64':
                ml_data = ml_data.drop(ml_data[ml_data[column] <= -9999].index)
                ml_data = ml_data.drop(ml_data[ml_data[column] >= 99999].index)
        return ml_data

    def __get_min_max_coords(self):
        """
        Gets min and max latitude and longitude coordinates to crop dataframes using self.feature_input

        :return: Tuples of max longitude and max latitude (tuple)
        """
        max_x, min_x = max(self.feature_input['x']), min(self.feature_input['x'])
        max_y, min_y = max(self.feature_input['y']), min(self.feature_input['y'])
        return (max_x, min_x), (max_y, min_y)

    def __find_closest_coord_idx(self, xy_coords):
        """
        Finds and matches the closest coordinates from the fire history data to the feature input data
        :param xy_coords: longitude and latitude coordinates of all the fires that were in coordinate_file (list)
        :return: List of the indexes of the closest coordinates (list)
        """
        closest_idxs = []
        for x_coord, y_coord in xy_coords:
            find_xy = self.feature_input[['x', 'y']].sub([x_coord, y_coord], axis='columns').abs()
            find_xy["z"] = find_xy['x'] ** 2 + find_xy['y'] ** 2
            closest_idx = find_xy['z'].idxmin()
            closest_idxs.append(closest_idx)
        return closest_idxs

    def __clean_data_for_ml(self):
        """
        Cleans data for ML model and creates a feature array X and label array y from the ml_data
        :return: None
        """
        self.ml_data = self.__combine_and_clean_data()
        if self.accurate_weather:
            self.ml_data = self.__get_weather_from_date()
        X = self.ml_data[['temp', 'vapr', 'wind', 'prec', 'slope', 'aspect', 'elevation', 'ndvi', 'ndmi', 'ndwi']].to_numpy()
        y = self.ml_data['fire'].to_numpy()

        # y = self.ml_data['DailyAcres'].to_numpy()
        # y = y.reshape(-1, 1)
        # y = scaler.fit_transform(y)
        # y = np.transpose(y)[0]

        scaler = sklearn.preprocessing.MinMaxScaler()
        X = scaler.fit_transform(X)
        self.X, self.y = X, y

    def __get_weather_from_date(self):
        """
        Uses the Ambee API to get historical weather data for when the fire took place
        :return: Pandas Dataframe with updated weather data
        """
        def weather_helper(df):
            weather_hist = self.ambee.get_weather_history(df['y'], df['x'], df['FireDiscoveryDateTime'])
            return weather_hist

        ml_data = self.ml_data.copy()
        ml_data['FireDiscoveryDateTime'] = ml_data['FireDiscoveryDateTime'].apply(lambda x: x[:-3])
        ml_data['FireDiscoveryDateTime'] = ml_data['FireDiscoveryDateTime'].apply(lambda x: dt.strptime(x, '%Y/%m/%d %H:%M:%S').strftime('%Y-%m-%d'))
        new_weather = ml_data.apply(weather_helper, axis=1)
        new_weather = list(new_weather.to_numpy())
        ml_data['temp'] = [row['temp'] for row in new_weather]
        ml_data['vapr'] = [row['vapr'] for row in new_weather]
        ml_data['wind'] = [row['wind'] for row in new_weather]
        ml_data['prec'] = [row['prec'] for row in new_weather]
        return ml_data
