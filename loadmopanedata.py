#this script reads in the mopani data and converts it to a format that can be used in the next script

import datetime
import pandas as pd
import os

mopanidatafile = 'Gonimbrasia_Outbreaks_7NovZN.xlsx'
data = pd.read_excel(mopanidatafile, dtype=str)
print("Data loaded successfully.")
required_columns = ['Latitude', 'Longitude', 'Year', 'Month']
mopanedata = data[required_columns].copy()

# Convert Latitude and Longitude to float
mopanedata.loc[:, 'Latitude'] = mopanedata['Latitude'].astype(float)
mopanedata.loc[:, 'Longitude'] = mopanedata['Longitude'].astype(float)

# Create new columns for startdate and enddate
def parse_dates(row):
    year = row['Year']
    month = row['Month']
    start_day, end_day = month.split(' - ')
    start_date = datetime.datetime.strptime(f"{year} {start_day}", "%Y %d %b")
    end_date = datetime.datetime.strptime(f"{year} {end_day}", "%Y %d %b")
    return pd.Series([start_date, end_date])

mopanedata[['startdate', 'enddate']] = mopanedata.apply(parse_dates, axis=1)

#save the data to a file
mopanedata.to_csv('mopanedata.csv', index=False)

#let us also create shape files around each of the points in the list.
import geopandas as gpd
from shapely.geometry import Point

# The points will be in WGS84 and we will want 0.5 km x 0.5 km squares around them

# Create a GeoDataFrame from the data
geometry = [Point(xy) for xy in zip(mopanedata['Longitude'], mopanedata['Latitude'])]
gdf = gpd.GeoDataFrame(mopanedata, geometry=geometry, crs="EPSG:4326")

#now create the squares
gdf['geometry'] = gdf['geometry'].buffer(0.005) #0.005 degrees is about 0.5 km
# now save the geodataframe to a set of geopackage files
gdf.to_file("mopane_points.gpkg", layer='mopane_points', driver="GPKG")


