""" Entry point of the calculation module function"""
import numpy as np
from osgeo import gdal

from ..constant import CM_NAME
from ..helper import generate_output_file_tif


# TODO: CM provider must "change this code"
# TODO: CM provider must "not change input_raster_selection,output_raster  1 raster input => 1 raster output"
# TODO: CM provider can "add all the parameters he needs to run his CM
# TODO: CM provider can "return as many indicators as he wants"
def calculation(
    output_directory,
    inputs_raster_selection,
    inputs_vector_selection,
    inputs_parameter_selection,
):
    # TODO the folowing code must be changed by the code of the calculation module

    # generate the output raster file
    output_raster1 = generate_output_file_tif(output_directory)

    # retrieve the inputs layes
    input_raster_selection = inputs_raster_selection["solar_radiation"]

    # retrieve the inputs layes
    # input_vector_selection = inputs_vector_selection["heating_technologies_eu28"]

    # retrieve the inputs all input defined in the signature
    efficiency = float(inputs_parameter_selection["system_efficiency"])

    # TODO this part bellow must be change by the CM provider
    ds = gdal.Open(input_raster_selection)
    ds_band = ds.GetRasterBand(1)

    # ----------------------------------------------------
    pixel_values = np.nan_to_num(ds.ReadAsArray())
    # ----------Reduction factor----------------

    pixel_values_modified = pixel_values * efficiency
    irr_sum = pixel_values_modified.sum()

    gtiff_driver = gdal.GetDriverByName("GTiff")
    # print ()
    out_ds = gtiff_driver.Create(
        output_raster1,
        ds_band.XSize,
        ds_band.YSize,
        1,
        gdal.GDT_Float32,
        ["compress=DEFLATE", "TILED=YES", "TFW=YES", "ZLEVEL=9", "PREDICTOR=1"],
    )
    out_ds.SetProjection(ds.GetProjection())
    out_ds.SetGeoTransform(ds.GetGeoTransform())

    # SetColorTable() only supported for Byte or UInt16 bands in TIFF format.
    # ct = gdal.ColorTable()
    # ct.SetColorEntry(0, (0, 0, 0, 255))
    # ct.SetColorEntry(1, (110, 220, 110, 255))
    # out_ds.GetRasterBand(1).SetColorTable(ct)

    out_ds_band = out_ds.GetRasterBand(1)
    out_ds_band.SetNoDataValue(0)
    out_ds_band.WriteArray(pixel_values_modified)

    del out_ds
    # output geneneration of the output
    graphics = []

    # TODO to create zip from shapefile use create_zip_shapefiles from the helper before sending result
    # TODO exemple  output_shpapefile_zipped = create_zip_shapefiles(output_directory, output_shpapefile)
    result = dict()
    result["name"] = CM_NAME
    result["indicator"] = [
        {
            "unit": "kWh",
            "name": "Total irradiation  {:5.2f}".format(efficiency),
            "value": str(irr_sum),
        }
    ]
    result["graphics"] = graphics
    result["vector_layers"] = []
    result["raster_layers"] = [
        {
            "name": "layers of irradiation {:5.2f}".format(efficiency),
            "path": output_raster1,
            "type": "solar_radiation",
        }
    ]
    print("result", result)
    return result


def colorizeMyOutputRaster(out_ds):
    ct = gdal.ColorTable()
    ct.SetColorEntry(0, (0, 0, 0, 255))
    ct.SetColorEntry(1, (110, 220, 110, 255))
    out_ds.SetColorTable(ct)
    return out_ds
