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
gdf_list = []
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
        gdf_list.append(gdf_line.to_crs(mopane_gdf.crs))

# mopane_gdf contains the points of interest, gdf_list contains the raster data
# We can now perform a spatial join between the two GeoDataFrames
# The result will be a GeoDataFrame with the points of interest and the raster data
# that intersects with them
gdf_final = gpd.sjoin(mopane_gdf, pd.concat(gdf_list), predicate='intersects', how='inner')

# Save the final GeoDataFrame to a GeoPackage file
gdf_final.to_file("mopane_ndvi.gpkg", driver="GPKG")

# # Now, we want to go through the GeoDataFrame and calculate the mean NDVI value from the raster data in a 0.5 km buffer around each point of interest
# buffer_size = 0.5  # Buffer size in kilometers
# # We will use rasterio to read the raster data and calculate the mean NDVI value
# # We will then add this mean NDVI value to the GeoDataFrame

# buffer_size_meters = buffer_size * 1000  # Convert buffer size to meters

# #add the column mean_ndvi to the gdf_final
# gdf_final['mean_ndvi'] = None

# for index, point in gdf_final.iterrows():
#     try:
#         # Open the raster file
#         with rasterio.open(point['filename']) as src:
#             # Ensure the point geometry is in the same CRS as the raster
#             if gdf_final.crs != src.crs:
#                 point_geom = gpd.GeoSeries([point.geometry], crs=gdf_final.crs).to_crs(src.crs).iloc[0]
#             else:
#                 point_geom = point.geometry

#             # Create a buffer around the point in the raster CRS
#             buffered_geom = point_geom.buffer(buffer_size_meters)

#             # Ensure the buffer geometry intersects the raster bounds
#             if not buffered_geom.intersects(box(*src.bounds)):
#                 print(f"Buffer does not intersect raster bounds for point {index}. Skipping...")
#                 continue

#             # Mask the raster with the buffered geometry
#             out_image, out_transform = mask(src, [buffered_geom], crop=True, nodata=src.nodata)
#             out_image = out_image[0]  # Extract the first band

#             # Calculate the mean NDVI value, ignoring nodata values, and add it to the GeoDataFrame
#             mean_ndvi = out_image[out_image != src.nodata].mean()
#             gdf_final.at[index, 'mean_ndvi'] = mean_ndvi

#     except Exception as e:
#         print(f"Error processing file {point['filename']} for point {index}: {e}")

# # Save the updated GeoDataFrame to a GeoPackage file
# mopane_gdf.to_file("mopane_ndvi_with_mean.gpkg", driver="GPKG")


# #plot the ara of interest from the raster data in each of the points in time.  Just open the file in filname with rasterio and then display the buffered area around the lat/long only
# # Ensure the CRS of gdf_final matches the CRS of the raster
# with rasterio.open(gdf_final['filename'].iloc[0]) as src:
#     if gdf_final.crs != src.crs:
#         gdf_final = gdf_final.to_crs(src.crs)

#     # Debug: Print the CRS of gdf_final and the raster
#     print(f"gdf_final CRS: {gdf_final.crs}")
#     print(f"Raster CRS: {src.crs}")

#     # Get the geometry of the first point
#     point_geom = gdf_final['geometry'].iloc[0]
#     point_x, point_y = point_geom.x, point_geom.y

#     # Create a square area of 500x500 meters centered on the point
#     square_bounds = box(
#         point_x - 250, point_y - 250,
#         point_x + 250, point_y + 250
#     )

#     # Clip the square bounds to the raster bounds
#     raster_bounds_geom = box(*src.bounds)
#     clipped_geom = square_bounds.intersection(raster_bounds_geom)

#     # Debug: Print the extents of the point, square bounds, and clipped geometry
#     print(f"Point geometry bounds: {point_geom.bounds}")
#     print(f"Square bounds: {square_bounds.bounds}")
#     print(f"Clipped geometry bounds: {clipped_geom.bounds}")
#     print(f"Raster bounds: {src.bounds}")

#     # Ensure the clipped geometry is valid
#     if clipped_geom.is_empty:
#         raise ValueError("Clipped geometry does not intersect raster bounds.")

#     # Mask the raster with the clipped geometry
#     out_image, out_transform = mask(src, [clipped_geom], crop=True, nodata=src.nodata)

#     # Adjust for potential one-pixel offset by ensuring alignment with the raster's transform
#     out_image = out_image[0]  # Extract the first band
#     row_offset, col_offset = ~out_transform * (clipped_geom.bounds[0], clipped_geom.bounds[1])
#     row_offset, col_offset = int(row_offset), int(col_offset)

#     # Debug: Print the offsets for verification
#     print(f"Row offset: {row_offset}, Column offset: {col_offset}")

#     # Replace NA values with 0 for plotting
#     out_image[out_image == src.nodata] = 0

#     # Debug: Check if the masked raster contains valid data
#     if out_image.size == 0 or (out_image == 0).all():
#         print("Masked raster contains no valid data.")
#         raise ValueError("Masked raster contains no valid data.")

#     # Plot the masked raster and the clipped geometry
#     fig, ax = plt.subplots(1, 1, figsize=(6, 6))
#     show(out_image, transform=out_transform, ax=ax, title="Sentinel-2 Data")
#     gpd.GeoSeries([clipped_geom], crs=src.crs).plot(ax=ax, color='red', alpha=0.5)
#     plt.show()




#take the gdf_final and plot the entire raster from the file in the filename column, then 
# add a red box around the lat/long point in the gdf_final, make sure to correct for going over the edge of the raster
# and ensure that the raster is displayed correctly

# curindex = 0
# with rasterio.open(gdf_final['filename'].iloc[curindex]) as src:
#     # Take the raster of interest and set all null values to 0
#     raster = src.read(1)
#     raster[raster == src.nodata] = 0
#     #draw the raster
#     fig, ax = plt.subplots(1, 1, figsize=(6, 6))
#     show(raster, ax=ax, title="Sentinel-2 Data")
#     plt.show()


# curindex = 0
# #seperate this so that it doesn't load the raster every time for no reason.
# def load_raster(filename):
#     with rasterio.open(filename) as src:
#         raster = src.read(1)
#         raster[raster == src.nodata] = 0
#         transform = src.transform  # Capture the transform
#         crs = src.crs  # Capture the CRS
#         bounds = src.bounds  # Capture the bounds
#     return raster, transform, crs, bounds

# raster, transform, crs, bounds = load_raster(gdf_final['filename'].iloc[curindex])
# #draw the raster
# fig, ax = plt.subplots(1, 1, figsize=(6, 6))
# show(raster, transform=transform, ax=ax, title="Sentinel-2 Data")  # Use the correct transform

# # Get the geometry of the first point
# point_geom = gdf_final['geometry'].iloc[curindex]
# point_geom = gpd.GeoSeries([point_geom], crs=gdf_final.crs).to_crs(crs).iloc[curindex]
# point_x, point_y = point_geom.x, point_geom.y

# square_bounds = box(
#     point_x - 250, point_y - 250,
#     point_x + 250, point_y + 250
# )
# gpd.GeoSeries([square_bounds], crs=crs).plot(ax=ax, edgecolor='red', facecolor='none', linewidth=2)
# plt.show()

# #ok so that worked well, so now lets extract the data from the raster for the area of interest
# #using the same raster and square_bounds we created above, we can extract the data from the raster
# # Ensure the area of interest (aoi) aligns with the raster grid
# 

# # Ensure the area of interest (aoi) aligns with the raster grid
# aoi = square_bounds
# with rasterio.open(gdf_final['filename'].iloc[curindex]) as src:
#     # Reopen the raster to use its metadata
#     if not aoi.intersects(box(*src.bounds)):
#         raise ValueError("AOI does not intersect the raster bounds.")

#     # Snap the aoi to the raster grid
#     aoi_window = geometry_window(src, [aoi])
#     aoi_bounds = rasterio.windows.bounds(aoi_window, src.transform)
#     snapped_aoi = box(*aoi_bounds)

#     # Clip the raster using the snapped area of interest
#     clipped_raster, transform = mask(src, [snapped_aoi], crop=True, nodata=src.nodata)

# # Extract the first band of the clipped raster
# clipped_raster = clipped_raster[0]

# # Replace nodata values with 0 to avoid issues during plotting
# clipped_raster[clipped_raster == src.nodata] = 0

# # Check if the clipped raster contains valid data
# if clipped_raster.size == 0 or (clipped_raster == 0).all():
#     raise ValueError("Clipped raster contains no valid data.")

# # Plot the clipped raster
# fig, ax = plt.subplots(1, 1)
# show(clipped_raster, transform=transform, ax=ax, title="Clipped Raster Data")
# plt.show()

# # Calculate the mean NDVI value, ignoring nodata values
# mean_ndvi = clipped_raster[clipped_raster != 0].mean()
# print(f"Mean NDVI value for the area of interest: {mean_ndvi}")


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

# Iterate through gdf_final, process each point, plot the clipped raster, and calculate mean NDVI
for index, row in gdf_final.iterrows():
    filename = row['filename']
    points_gdf = gdf_final.iloc[[index]]

    try:
        # Process the raster for the current point
        clipped_raster = process_raster_for_points(filename, points_gdf)

        # Plot the clipped raster
        fig, ax = plt.subplots(1, 1)
        show(clipped_raster, ax=ax, title=f"Clipped Raster Data for Point {index}")
        plt.show()
    except Exception as e:
        print(f"Error processing file {filename} for point {index}: {e}")   




# filename = gdf_final['filename'].iloc
# points_gdf = gdf_final.iloc[[curindex]]  # Adjust this to process multiple points if needed
# clipped_raster = process_raster_for_points(filename, points_gdf)
# #plot clipped_raster
# fig, ax = plt.subplots(1, 1)
# show(clipped_raster, ax=ax, title="Clipped Raster Data")
# plt.show()
