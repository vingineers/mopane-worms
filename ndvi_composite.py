import os
from pathlib import Path
from skimage.morphology import disk  # Updated import
import openeo
from dotenv import load_dotenv
import json  # Add import for json

# Load environment variables
load_dotenv()
# Your client credentials
oauth_client_id = os.getenv('OAUTH_CLIENT_ID')
oauth_client_secret = os.getenv('OAUTH_CLIENT_SECRET')

# First, we connect to the back-end and authenticate ourselves via Basic authentication. 
# con = openeo.connect("https://earthengine.openeo.org")
# con.authenticate_basic("group11", "test123")
con = openeo.connect("openeofed.dataspace.copernicus.eu").authenticate_oidc_client_credentials(oauth_client_id, oauth_client_secret)
# con = openeo.connect("earthengine.openeo.org").authenticate_oidc_client_credentials(oauth_client_id, oauth_client_secret)
connection = con

# connection = openeo.connect("https://openeo-dev.vito.be")
# connection = openeo.connect("https://earthengine.openeo.org")
bbox = {"west": 4.996033, "south": 51.258922, "east": 5.091603, "north": 51.282696}
# connection.authenticate_basic()


# sentinel2_data_cube = connection.load_collection("TERRASCOPE_S2_TOC_V2", bands=["B04", "B08"])
sentinel2_data_cube = connection.load_collection("SENTINEL2_L2A", bands=["B04", "B08"])
"SENTINEL3_OLCI_L1B"
sentinel2_data_cube = sentinel2_data_cube.filter_bbox(**bbox)

ndvi = sentinel2_data_cube.ndvi()

scl = connection.load_collection("SENTINEL2_L2A", bands=["SCL"]).filter_bbox(**bbox)
classification = scl.band("SCL")


#in openEO, 1 means mask (remove pixel) 0 means keep pixel

SCL_MASK_VALUES = [0, 1, 3, 8, 9, 10, 11]
#keep useful pixels, so set to 1 (remove) if smaller than threshold

#first erode, then dilate: removes noise, in this case small areas marked as cloud?
scl_mask = ~ ((classification == 0) | (classification == 1) | (classification == 3) | (classification == 8) | (classification == 9) | (classification == 10) | (classification == 11))
#scl_mask = ((classification == 3) | (classification == 8) | (classification == 9) )
#this is erosion: clouds (1's) get smaller
scl_mask = scl_mask.apply_kernel(disk(13))  # Updated method
#output of 2D convolution is non-binary, make it binary again, AND invert
scl_mask = scl_mask < 0.01
#now do dilation
scl_mask = scl_mask.apply_kernel(disk(13))  # Updated method
scl_mask = scl_mask.add_dimension(name="bands",label="scl",type="bands")

def test_mask():
    scl_mask.filter_temporal("2018-05-06","2018-05-06").download("mask.tiff",format="GTIFF")

masked = ndvi.mask(scl_mask)

#I'm using pytest methods here: PyCharm allows these methods to be started individually, which is more convenient
# otherwise my script would be doing multiple downloads on each test, or I would have to comment out these lines

#takes a few seconds to download
def test_only_ndvi():
    masked.filter_temporal("2018-05-06","2018-05-06").download("ndvi_composite.tiff", format="GTiff")

#client side logic is needed to construct input intervals and output labels
#this gives you the flexibility to do all kinds of compositing
start_date = "2018-04-21"
end_date = "2018-05-31"
#TODO: flat list for intervals is maybe a bit weird?
#EP-3616 support median reducer
composited_ndvi = masked.aggregate_temporal(intervals=[start_date,"2018-05-21","2018-05-01",end_date],labels=["2018-05-01","2018-05-11"],reducer=lambda d:d.mean(),dimension='t')

def test_masked_netcdf():
    composited_ndvi.filter_temporal(start_date,end_date).download("masked.nc",format="NetCDF")

def test_composite_netcdf():
    composited_ndvi.filter_temporal(start_date,end_date).download("composite.nc",format="NetCDF")

def test_composite_geotiff():
    composited_ndvi.filter_temporal(start_date,end_date).download("composite.tiff",format="GTIFF")


def get_test_resource(relative_path):
    dir = Path(os.path.dirname(os.path.realpath(__file__)))
    return str(dir / relative_path)

compositing_udf = openeo.UDF.from_file('udf/median_composite.py')

def test_composite_by_udf():
    masked.apply_dimension(process=compositing_udf, dimension='t').filter_temporal(start_date,end_date).download("composite_udf.nc",format="NetCDF")

from openeo.rest.datacube import DataCube


def test_debug_udf():
    """
    Shows how to run your UDF locally for testing. This method uses the same code as the backend, and can be used to check validity of your UDF.
    https://open-eo.github.io/openeo-python-client/udf.html#example-downloading-a-datacube-and-executing-an-udf-locally
    depends on composite.nc file created in earlier function!
    """

    DataCube.execute_local_udf(compositing_udf, 'masked.nc', fmt='netcdf')

from examples.udf.median_composite import apply_datacube


def test_debug_udf_direct_invoke():
    """
    Shows how to run your UDF locally for testing, by invoking the function directly, breakpoints work.
    https://open-eo.github.io/openeo-python-client/udf.html#example-downloading-a-datacube-and-executing-an-udf-locally
    depends on composite.nc file created in earlier function!
    """
    from openeo.udf import XarrayDataCube
    udf_cube = XarrayDataCube.from_file('masked.nc', fmt='netcdf')

    apply_datacube(udf_cube,context={})


# TERRASCOPE_S2_NDVI_V2
# SENTINEL2_L2A

latitude = -23.694734
longitude = 30.971842



cube = connection.load_collection(
    "SENTINEL2_L2A",
    # spatial_extent={"west": 5.05, "south": 51.21, "east": 5.1, "north": 51.23},
        spatial_extent={
            "west": longitude - 0.01,
            "east": longitude + 0.01,
            "north": latitude + 0.01,
            "south": latitude - 0.01
        },
    temporal_extent=["2022-05-01", "2022-05-30"],
    bands=['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B11', 'B12', 'WVP', 'AOT', 'SCL', 'sunAzimuthAngles', 'sunZenithAngles', 'viewAzimuthMean', 'viewZenithMean'],
)
# Rescale digital number to physical values and take temporal maximum.
cube = cube.apply(lambda x: 0.004 * x - 0.08).max_time()
filelocation ="output/ndvi-max.tiff"
cube.download(filelocation, format="GTiff")

#now view ndvi-max.tiff with matplotlib
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt


ndvi_max_image = rasterio.open(filelocation)
fig, ax = plt.subplots(1, 1, figsize=(12, 12))
show(ndvi_max_image, ax=ax, title="NDVI Max")
plt.show()


