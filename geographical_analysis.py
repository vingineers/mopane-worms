import requests
import datetime
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.plot import show
import pandas as pd
import time
from requests.exceptions import SSLError
import openeo
import os
from dotenv import load_dotenv
import json  # Add import for json

# Load environment variables
load_dotenv()

# Your client credentials
oauth_client_id = os.getenv('OAUTH_CLIENT_ID')
oauth_client_secret = os.getenv('OAUTH_CLIENT_SECRET')

mopanidatafile = 'Gonimbrasia_Outbreaks_7NovZN.xlsx'
data = pd.read_excel(mopanidatafile, dtype=str)
print("Data loaded successfully.")
required_columns = ['Latitude', 'Longitude', 'Year', 'Month']
formateddata = data[required_columns].copy()

# Convert Latitude and Longitude to float
formateddata.loc[:, 'Latitude'] = formateddata['Latitude'].astype(float)
formateddata.loc[:, 'Longitude'] = formateddata['Longitude'].astype(float)

# Create new columns for startdate and enddate
def parse_dates(row):
    year = row['Year']
    month = row['Month']
    start_day, end_day = month.split(' - ')
    start_date = datetime.datetime.strptime(f"{year} {start_day}", "%Y %d %b")
    end_date = datetime.datetime.strptime(f"{year} {end_day}", "%Y %d %b")
    return pd.Series([start_date, end_date])

formateddata[['startdate', 'enddate']] = formateddata.apply(parse_dates, axis=1)

# Function to search for openEO data with retry mechanism
def search_data(connection, start_date, end_date, latitude, longitude, retries=3, delay=5):
    for attempt in range(retries):
        try:
            collection = connection.load_collection(
                "SENTINEL2_L2A",
                spatial_extent={
                    "west": longitude - 0.1,
                    "east": longitude + 0.1,
                    "north": latitude + 0.1,
                    "south": latitude - 0.1
                },
                temporal_extent=[start_date, end_date]
            )
            return collection
        except Exception as e:
            print(f"Error occurred: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Max retries exceeded with error")

# Function to download data
def download_data(job, output_file):
    job.download_results(output_file)

# Function to visualize data
def visualize_data(file_path):
    with rasterio.open(file_path) as src:
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))
        show(src, ax=ax, title="Sentinel-2 Data")
        plt.show()

selectedval = 0

# Main function
def main():
    # Use selectedval to target one of the formateddata components
    target_data = formateddata.iloc[selectedval]
    latitude = target_data['Latitude']
    longitude = target_data['Longitude']
    start_date = (target_data['startdate'] - pd.DateOffset(months=1)).strftime('%Y-%m-%d')
    end_date = (target_data['enddate'] + pd.DateOffset(months=1)).strftime('%Y-%m-%d')

    # Connect to openEO backend
    # connection = openeo.connect("https://earthengine.openeo.org").authenticate_basic(oauth_client_id, oauth_client_secret)

    connection = openeo.connect("openeofed.dataspace.copernicus.eu").authenticate_oidc_client_credentials(oauth_client_id, oauth_client_secret)
    # collections = connection.list_collections()  # Get collections data

    # # Write collections data to a file in pretty JSON format
    # with open('collections_data.json', 'w') as file:
    #     json.dump(collections, file, indent=4)

    datacube = search_data(connection, start_date, end_date, latitude, longitude)
    datacube = datacube.process(
        process_id="ndvi", 
        arguments={
            "data": datacube, 
            "nir": "B8", 
            "red": "B4"}
    )
    
    result = datacube.save_result("GTiff")
    job = result.create_job()
    # Starts the job and waits until it finished to download the result.
    job.start_and_wait()
    job.get_results().download_files("output")




    visualize_data('data.tif')

    
if __name__ == "__main__":
    main()



