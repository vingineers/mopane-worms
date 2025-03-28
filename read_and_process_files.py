import geopandas as gpd
import rasterio
import os
from shapely.geometry import box  # Import box from shapely.geometry
import pandas as pd
from rasterio.mask import mask  # Correct import for the mask function
from matplotlib import pyplot as plt
from rasterio.plot import show  # Import the show function
from rasterio.features import geometry_window

#load mopane_points.gpkg
mopane_gdf = gpd.read_file("mopane_points.gpkg")

#there is a series of raster data inside the eodag folder which we can now analyze:
fileloc = 'D:\eodag_data\qgis_mopane'
#scan the folder and subfolders for raster data and extract the ndvi file list
ndvi_files = []
for root, dirs, files in os.walk(fileloc):
    for file in files:
        if file.endswith('.tif'):
            ndvi_files.append(os.path.join(root, file))

#open each file and create a gpd file which contains the extent for each file
raster_list = []
for file in ndvi_files:
    with rasterio.open(file) as src:
        bounds = src.bounds
        filename = file.split('\\')[-1]
        gdf_line = gpd.GeoDataFrame(
            {
                'geometry': [box(*bounds)],
                'filename': file,
                'date': filename.split('_')[1],
                'tile': filename.split('_')[0]
            },
            crs=src.crs
        )
        # Transform to the CRS of mopane_gdf
        raster_list.append(gdf_line.to_crs(mopane_gdf.crs))

# mopane_gdf contains the points of interest, gdf_list contains the raster data
# We can now perform a spatial join between the two GeoDataFrames
# The result will be a GeoDataFrame with the points of interest and the raster data
# that intersects with them
mopane_raster_gdf = gpd.sjoin(mopane_gdf, pd.concat(raster_list), predicate='intersects', how='inner')

# Save the final GeoDataFrame to a GeoPackage file
mopane_raster_gdf.to_file("mopane_ndvi.gpkg", driver="GPKG")


# Refactor to open the raster file once and collect all information for all points
def process_raster_for_points(filename, points_gdf):
    with rasterio.open(filename) as src:
        raster = src.read(1)
        raster[raster == src.nodata] = 0
        transform = src.transform
        crs = src.crs
        bounds = src.bounds

        point_geom = points_gdf['geometry']
        point_geom = gpd.GeoSeries(point_geom, crs=points_gdf.crs).to_crs(crs)
        point_x = point_geom.x.iloc[0]
        point_y = point_geom.y.iloc[0]

        square_bounds = box(
            point_x - 250, point_y - 250,
            point_x + 250, point_y + 250
        )

        aoi_window = geometry_window(src, [square_bounds])
        aoi_bounds = rasterio.windows.bounds(aoi_window, transform)
        snapped_aoi = box(*aoi_bounds)

        clipped_raster, _ = mask(src, [snapped_aoi], crop=True, nodata=src.nodata)

        return clipped_raster

# add columns to mopane_raster_gdf for mean_ndvi and rasterdata
mopane_raster_gdf['mean_ndvi'] = None
mopane_raster_gdf['rasterdata'] = None

# Iterate through gdf_final, process each point, plot the clipped raster, and calculate mean NDVI
for index, row in mopane_raster_gdf.iterrows():
    filename = row['filename']
    points_gdf = mopane_raster_gdf.iloc[[index]]
    shortfilename = filename.split('\\')[-1]
    try:
        # Process the raster for the current point
        clipped_raster = process_raster_for_points(filename, points_gdf)
        # Calculate the mean NDVI value, ignoring nodata values (assumed to be 0)
        mean_ndvi = clipped_raster[clipped_raster != 0].mean()
        mopane_raster_gdf.at[index, 'mean_ndvi'] = mean_ndvi
        print(f"File: {shortfilename}, Point Index: {index}, Mean NDVI: {mean_ndvi}, rastershape: {clipped_raster.shape}")

        # Debugging: Print the type and shape of clipped_raster before assignment
        # print(f"Debug: clipped_raster type: {type(clipped_raster)}, shape: {clipped_raster.shape}")
        # Convert the clipped raster to a string representation before assignment
        mopane_raster_gdf.at[index, 'rasterdata'] = str(clipped_raster.tolist())

    except Exception as e:
        print(f"Error processing file {shortfilename} for point {index}: {e}")   


fig, ax = plt.subplots(1, 1)
show(clipped_raster, ax=ax, title=f"Clipped Raster Data for Point {index}")
plt.show()




# filename = gdf_final['filename'].iloc
# points_gdf = gdf_final.iloc[[curindex]]  # Adjust this to process multiple points if needed
# clipped_raster = process_raster_for_points(filename, points_gdf)
# #plot clipped_raster
# fig, ax = plt.subplots(1, 1)
# show(clipped_raster, ax=ax, title="Clipped Raster Data")
# plt.show()
