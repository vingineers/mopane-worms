import requests
import datetime
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
import pandas as pd
import openeo
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your client credentials
oauth_client_id = os.getenv('OAUTH_CLIENT_ID')
oauth_client_secret = os.getenv('OAUTH_CLIENT_SECRET')

# mopanidatafile = 'Gonimbrasia_Outbreaks_7NovZN.xlsx'
# data = pd.read_excel(mopanidatafile, dtype=str)
# print("Data loaded successfully.")
# required_columns = ['Latitude', 'Longitude', 'Year', 'Month']
# mopanedata = data[required_columns].copy()

# # Convert Latitude and Longitude to float
# mopanedata.loc[:, 'Latitude'] = mopanedata['Latitude'].astype(float)
# mopanedata.loc[:, 'Longitude'] = mopanedata['Longitude'].astype(float)

# # Create new columns for startdate and enddate
# def parse_dates(row):
#     year = row['Year']
#     month = row['Month']
#     start_day, end_day = month.split(' - ')
#     start_date = datetime.datetime.strptime(f"{year} {start_day}", "%Y %d %b")
#     end_date = datetime.datetime.strptime(f"{year} {end_day}", "%Y %d %b")
#     return pd.Series([start_date, end_date])

# mopanedata[['startdate', 'enddate']] = mopanedata.apply(parse_dates, axis=1)

import loadmopanedata
mopanedata = loadmopanedata.mopanedata

# Function to visualize data
def visualize_data(file_path):
    with rasterio.open(file_path) as src:
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))
        show(src, ax=ax, title="Sentinel-2 NDVI Composite")
        plt.show()

selectedval = 0
index = selectedval
Use selectedval to target one of the mopanedata components
target_data = mopanedata.iloc[selectedval]
latitude = target_data['Latitude']
longitude = target_data['Longitude']
start_date = (target_data['startdate'] - pd.DateOffset(months=1)).strftime('%Y-%m-%d')
end_date = (target_data['enddate'] + pd.DateOffset(months=1)).strftime('%Y-%m-%d')


# Function to download all bands for each date range as separate files
def download_all_bands_for_all_dates(connection, mopanedata):
    for index, row in mopanedata.iterrows():
        latitude = row['Latitude']
        longitude = row['Longitude']
        start_date = (row['startdate'] - pd.DateOffset(months=1)).strftime('%Y-%m-%d')
        end_date = (row['enddate'] + pd.DateOffset(months=1)).strftime('%Y-%m-%d')

        print(f"Processing index {index}: {start_date} to {end_date} at ({latitude}, {longitude})")

        # Load collection with all bands
        datacube = connection.load_collection(
            "SENTINEL2_L2A",
            spatial_extent={
                "west": longitude - 0.01,
                "east": longitude + 0.01,
                "north": latitude + 0.01,
                "south": latitude - 0.01
            },
            temporal_extent=[start_date, end_date],
            bands=['B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B11', 'B12', 'SCL',]
        )

        # Generate output file name
        output_file = f"output/datacube_{index}_{start_date}_to_{end_date}.tif"
        datacube.download(output_file, format="GTiff")
        print(f"Downloaded datacube with all bands to {output_file}")

# Main function
def main():


    # Connect to openEO backend
    connection = openeo.connect("openeofed.dataspace.copernicus.eu").authenticate_oidc_client_credentials(oauth_client_id, oauth_client_secret)

    # Download all bands for all date ranges
    download_all_bands_for_all_dates(connection, mopanedata)

    # Optionally visualize the first file
    first_file = "output/datacube_0_{start_date}_to_{end_date}.tif".format(
        start_date=(mopanedata.iloc[0]['startdate'] - pd.DateOffset(months=1)).strftime('%Y-%m-%d'),
        end_date=(mopanedata.iloc[0]['enddate'] + pd.DateOffset(months=1)).strftime('%Y-%m-%d')
    )
    visualize_data(first_file)

if __name__ == "__main__":
    main()
