import tempfile
import unittest
from osgeo import gdal
import numpy as np
from werkzeug.exceptions import NotFound
from app import create_app
import os.path
from shutil import copyfile
from .test_client import TestClient


if os.environ.get("LOCAL", False):
    UPLOAD_DIRECTORY = os.path.join(
        tempfile.gettempdir(), "hotmaps", "cm_files_uploaded"
    )
else:
    UPLOAD_DIRECTORY = "/var/hotmaps/cm_files_uploaded"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
    os.chmod(UPLOAD_DIRECTORY, 0o777)


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app(os.environ.get("FLASK_CONFIG", "development"))
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.client = TestClient(self.app,)

    def tearDown(self):

        self.ctx.pop()

    def test_compute(self):
        raster_file_path = "tests/data/raster_for_test.tif"

        ds = gdal.Open(raster_file_path)
        ds_band = ds.GetRasterBand(1)
        pixel_values = np.nan_to_num(ds.ReadAsArray())
        orig_sum = pixel_values.sum()

        # simulate copy from HTAPI to CM
        save_path = UPLOAD_DIRECTORY + "/raster_for_test.tif"
        copyfile(raster_file_path, save_path)

        inputs_raster_selection = {}
        inputs_parameter_selection = {}
        inputs_vector_selection = {}
        inputs_raster_selection["solar_radiation"] = save_path
        inputs_parameter_selection["system_efficiency"] = 0.5

        # register the calculation module a
        payload = {
            "inputs_raster_selection": inputs_raster_selection,
            "inputs_parameter_selection": inputs_parameter_selection,
            "inputs_vector_selection": inputs_vector_selection,
        }

        rv, json = self.client.post("computation-module/compute/", data=payload)
        # {'result': {'graphics': [],
        #     'indicator': [{'name': 'Total irradiation   0.50',
        #                    'unit': 'kWh',
        #                    'value': '3517502.5'}],
        #     'name': 'CM - Scale solar radiation',
        #     'raster_layers': [{'name': 'layers of irradiation  0.50',
        #                        'path': '/var/tmp/addb5243-5d58-44b4-8c16-55773f5c0404.tif',
        #                        'type': 'solar_radiation'}],
        #     'vector_layers': []}}

        self.assertTrue(rv.status_code == 200)
        indicators = json["result"]["indicator"]
        self.assertTrue(len(indicators) == 1)
        self.assertTrue(
            round(float(indicators[0]["value"]), 6)
            - round(orig_sum * inputs_parameter_selection["system_efficiency"], 6)
            < 10 ** -8
        )
