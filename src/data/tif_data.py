import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.plot import show
from rasterio.mask import mask
from rasterio.crs import CRS
from rasterio.enums import Resampling
from osgeo import gdal
import os

# imported by 
class TifData:
    def __init__(self, data_name, file, merge_name=None, temp_path="data/temp/"):
        """
        Class which interacts directly with the GeoTiff Data files

        :param data_name: Name of input data (str)
        :param file: Path to input data file (str / list)
        :param merge_name: Name of merged data file - if input file is list (str)
        :param temp_path: Path to store temporary files (str)
        """
        self.data_name = data_name
        self.file = file
        if type(file) == str and (file.split('.')[-1] == "tif" or file.split('.')[-1] == "TIF"):
            self.file_type = "tif"
        elif type(file) == list:
            self.file_type = "tif_list"
        self.temp_path = temp_path
        self.clip_file_name = ""

        self.data = np.array([])
        self.clip_data = np.array([])
        self.match_data, self.match_transform = np.array([]), np.array([])
        self.reclassified_data = np.array([])
        self.merge_name = merge_name

        self.__make_data()

    def __make_data(self):
        """
        Extracts data from input file to self.data using self.__tif_file for single files, or self.__merge_tif_file
        for list of files
        :return: None
        """
        if self.file_type == "tif":
            self.__tif_file()
        elif self.file_type == "tif_list":
            self.__merge_tif_file()

    def __tif_file(self):
        """
        Opens file using Rasterio to rasterio object in self.data
        - If DEM layer is passed, it creates a slope and aspect based on data_name passed
        :return: None
        """
        if self.data_name in ["slope", "aspect"]:
            new_file = "".join([self.temp_path, self.data_name, ".tif"])
            gdal.DEMProcessing(new_file, self.file, self.data_name, computeEdges=True, scale=111120)
            self.file = new_file[:]
        self.data = rasterio.open(self.file)
        crs = self.data.crs
        if crs != CRS.from_epsg(4326):
            self.__change_espg()

    def __merge_tif_file(self):
        """
        Creates a new merged tif file from the list of tife file inputs, and gets data from new tif file
        - New merged tif file takes name from merge_name
        - New merged file will automatically be opened to self.data as a Rasterio object
        :return: None
        """
        output_name = "".join([self.temp_path, self.merge_name, ".tif"])
        # If the merged file does not exist (some files like DEM can share the same merged tif file)
        if not os.path.exists(output_name):
            merge_files_list = []
            for tif in self.file:
                tif_file = rasterio.open(tif)
                merge_files_list.append(tif_file)
            # Merges TIF files here
            merged_data, merged_transform = merge(merge_files_list)
            out_meta = tif_file.meta.copy()
            out_meta.update({"driver": "GTiff", "height": merged_data.shape[1], "width": merged_data.shape[2],
                            "transform": merged_transform, "crs": tif_file.crs})
            with rasterio.open(output_name, "w", **out_meta) as dest:
                dest.write(merged_data)
        self.file = output_name
        self.file_type = "tif"
        self.__make_data()

    def __change_espg(self):
        """
        Changes ESPG projection to WGS84 (or ESPG 4326) if needed
        - Changes current projection to world projection
        - New TIF file will automatically be opened to self.data as a Rasterio object
        :return: None
        """
        new_file_name = "".join([self.temp_path, self.data_name, "_espg.tif"])
        os.system('gdalwarp %s %s -t_srs "+proj=longlat +ellps=WGS84" -q' % (self.file, new_file_name))
        self.file = new_file_name
        self.data = rasterio.open(self.file)

    def clip_file(self, shapes):
        """
        Clips Tif file in self.data and creates new clip_data variable
        - Masks the clipped data and creates a new file to be analyzed
        :param shapes: Polygon stored in shp file (GeoJson)
        :return: None
        """
        clip_data, clip_trans = mask(self.data, shapes, crop=True)
        out_meta = self.data.meta.copy()
        out_meta.update({"driver": "GTiff", "height": clip_data.shape[1], "width": clip_data.shape[2],
                         "transform": clip_trans, "crs": self.data.crs})
        clip_file_name = "".join([self.temp_path, self.data_name, "_clip.tif"])
        with rasterio.open(clip_file_name, "w", **out_meta) as dest:
            dest.write(clip_data)
        self.clip_file_name = clip_file_name
        self.clip_data = rasterio.open(self.clip_file_name)

    def resample_data(self, new_width, new_height, clip=True):
        """
        Matches data dimensions and transform of input data to new_width and new_height

        Used to match various datasets (with different shapes) to 1 standard shape for ML analysis. Will require HPC
        for matching Tif data on regular datasets.

        Note: matched data is not of same type as self.data and self.clip_data, equivalent to self.data.read(1)
        :param new_width: new data width (int)
        :param new_height: new height width (int)
        :param clip: sets clip to be data to be resampled (bool)
        :return: None
        """
        # Currently this only works with clipped data, need to use HPC with enough ram for non-clipped data
        data_input = self.data
        if clip:
            data_input = self.clip_data

        # If data dimensions are the same as the new specified dimensions, don't do anything
        if data_input.width == new_width and data_input.height == new_height:
            self.match_data, self.match_transform = data_input.read(1), data_input.transform
        else:
            data = data_input.read(out_shape=(data_input.count, new_height, new_width), resampling=Resampling.bilinear)
            # scale image transform
            transform = data_input.transform * data_input.transform.scale(
                (data_input.width / data.shape[-1]),
                (data_input.height / data.shape[-2])
            )
            self.match_data, self.match_transform = data, transform
        if self.match_data.ndim == 3:
            self.match_data = self.match_data[0]

    def visualize(self, clip=False, cmap='terrain'):
        """
        Visualized the current data based on the data type
        :param clip: sets clip to be visualized (bool)
        :param cmap: Visualization map (cmap colour scheme)
        :return: None
        """
        if not clip:
            show(self.data, cmap=cmap)
        else:
            try:
                show(self.clip_data, cmap=cmap)
            except TypeError:
                print('Clip data does not exist')

    def get_data(self, data_type="input"):
        """
        Gets np array of data from data object
        :param data_type: Data type to get data from ["inpyt", "clip", "match"] (str)
        :return: np array of data (np array)
        """
        if data_type == "input":
            return self.data.read(1)
        elif data_type == "clip":
            return self.clip_data.read(1)
        elif data_type == "match":
            return self.match_data
        return None

    def get_dim(self, data_type="input"):
        """
        Returns dimensions of a given data type
        :param data_type: Data type to get data from ["inpyt", "clip", "match"] (str)
        :return: Width and Height of data type (tuple)
        """
        if data_type == "input":
            return self.data.width, self.data.height
        elif data_type == "clip":
            return self.clip_data.width, self.clip_data.height
        elif data_type == "match":
            match_shape = np.shape(self.match_data)
            return match_shape[1], match_shape[0]
        return None

    def get_transform(self, data_type="input"):
        """
        Gets transformation matrix of a given data type
        :param data_type: Data type to get data from ["inpyt", "clip", "match"] (str)
        :return: Transformation matrix for data type (Rasterio transformation object)
        """
        if data_type == "input":
            return self.data.transform
        elif data_type == "clip":
            return self.clip_data.transform
        elif data_type == "match":
            return self.match_transform
        return None

    def get_meta(self, data_type="input"):
        """
        Gets Meta data of a given data type
        :param data_type: Data type to get data from ["inpyt", "clip"] (str)
        :return: Meta data for data type (Dict)
        """
        if data_type == "input":
            return self.data.meta.copy()
        elif data_type == "clip":
            return self.clip_data.meta.copy()
        else:
            return None

