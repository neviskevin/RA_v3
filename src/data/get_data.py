import numpy as np
import json
import requests
import datetime
from tqdm import tqdm
from time import sleep
from collections import defaultdict
from usgs import api as usgs_api
from KEYS import USGS_USER, USGS_PASS


class DownloadData:
    def __init__(self, input_data_dict, shapes, filepath="data/temp/"):
        """
        Downloads Geographical data from USGS website
        - currently supports Landsat-8 downloads (B3-B6 layers), Digital Elevation Model
        :param input_data_dict: Input Data Dictionary containing data name and path to data files (dict)
                {data_name: ([data_file_list], "merged_name_file")}
        :param shapes: shape of area to be used for downloading data (dict)
        :param filepath: Path to where downloaded files should be stored (str)
        """
        usgs_api.logout()
        usgs_api.login(USGS_USER, USGS_PASS, save=True)

        self.shapes = shapes
        self.lower_left, self.upper_right = self.__get_shape_boundary()

        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=16)
        self.end_date = today.strftime("%Y-%m-%d")
        self.start_date = week_ago.strftime("%Y-%m-%d")

        self.filepath = filepath
        self.input_data_dict = input_data_dict

    def download_data(self):
        """
        Calls Class Methods which downloads the DEM and Landsat-8 Data
        :return: None
        """
        self.download_dem()
        self.download_landsat()
        self.logout()

    def __get_shape_boundary(self):
        """
        Gets the lat and long of the upper right and lower left coordinates of the geojson input file to download all
        files needed for Fire Risk analysis
        :return: Dicts of long and lat for bottom left and top right corner (tuple)
        """
        shapes = self.shapes[0]
        coords = np.array(shapes['coordinates'][0])
        bottom_left = {"longitude": np.min(coords[:, 0]), "latitude": np.min(coords[:, 1])}
        top_right = {"longitude": np.max(coords[:, 0]), "latitude": np.max(coords[:, 1])}
        return bottom_left, top_right

    def __download_files(self, download_file_dict, filename):
        """
        Downloads files from the USGS website using the list of entity and product ids
        :param download_file_dict: Dictionary mapping the data to be downloaded to dataset, entity id, and product id (dict)
        :param filename: Name of File to be downloaded (str)
        :return: List of paths to files downloaded (list)
        """
        file_name_list = []

        for file in tqdm(download_file_dict.keys(), desc=f'Downloading files: {filename}'):
            dataset, entity_id, product_id = download_file_dict[file]
            _ = usgs_api.download_request(dataset, entity_id, product_id)
            sleep(2)
            try:
                download_meta = usgs_api.download_request(dataset, entity_id, product_id)
                download_url = download_meta['data']['availableDownloads'][0]['url']
            except IndexError:
                sleep(3)
                download_meta = usgs_api.download_request(dataset, entity_id, product_id)
                download_url = download_meta['data']['availableDownloads'][0]['url']
            r = requests.get(download_url, allow_redirects=True)
            file_name = self.filepath + file + ".tif"
            file_name_list.append(file_name)
            open(file_name, 'wb').write(r.content)

        return file_name_list

    def download_dem(self):
        """
        Downloads Digital Elevation Model Data and adds the paths to downloaded files to self.input_data_dict
        :return: None
        """
        dem_dict = {}
        dataset = 'SRTM_V2'
        output_names = ["slope", "aspect", "elevation"]

        results = usgs_api.scene_search(dataset, ll=self.lower_left, ur=self.upper_right)

        entity_ids = []
        for scene in results['data']['results']:
            if 'SRTM1' in scene['entityId']:
                entity_ids.append(scene['entityId'])

        for eid in entity_ids:
            download_options = usgs_api.download_options(dataset, eid)
            for data_downloads in download_options['data']:
                if 'GeoTIFF 1 Arc-second' in data_downloads['productName']:
                    dem_dict[eid] = (dataset, data_downloads['entityId'], data_downloads['id'])

        dem_file_list = self.__download_files(dem_dict, 'DEM')
        for name in output_names:
            self.input_data_dict[name] = (dem_file_list, "merged_arc_dem")

    def download_landsat(self):
        """
        Downloads Landsat-8 (B3-B6) Data and adds the paths to downloaded files to self.input_data_dict
        :return: None
        """
        landsat_dict = defaultdict(dict)
        dataset = 'landsat_ot_c2_l2'
        b_files = ['B3', 'B4', 'B5', 'B6']

        results = usgs_api.scene_search(dataset, ll=self.lower_left, ur=self.upper_right,
                                        start_date=self.start_date, end_date=self.end_date)
        entity_ids = []
        for scene in results['data']['results']:
            entity_ids.append(scene['entityId'])
        for ii, entity in enumerate(entity_ids):
            download_options = usgs_api.download_options(dataset, entity)
            for data_downloads in download_options['data']:
                for secondary_downloads in data_downloads['secondaryDownloads']:
                    if secondary_downloads['downloadSystem'] == 'dds' and any(b_file in secondary_downloads['entityId'] for b_file in b_files):
                        for b_file in b_files:
                            if b_file in secondary_downloads['entityId']:
                                landsat_dict[b_file][b_file+str(ii)] = (dataset, secondary_downloads['entityId'], secondary_downloads['id'])
        for b_file in b_files:
            b_file_list = self.__download_files(landsat_dict[b_file], b_file)
            self.input_data_dict[b_file] = (b_file_list, b_file)

    @staticmethod
    def logout():
        """
        Log out of the usgs api
        :return: None
        """
        usgs_api.logout()


