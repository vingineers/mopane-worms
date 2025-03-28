import geopandas as gpd
import eodag
import rasterio


#load mopane_points.gpkg
gdf = gpd.read_file("mopane_points.gpkg")
print(gdf.head())
# gdf.crs
# gdf['geometry'] = gdf['geometry'].buffer(0.005) #0.005 degrees is about 0.5 km

#lets temporarily keep this to just two values: 1 and 2
gdf = gdf.iloc[:2]

#now lets load the data from the eodag
# Create a EODataAccessGateway
dag = eodag.EODataAccessGateway()

# id=S2B_MSIL2A_20220101T075229_N0500_R135_T35KRP_20230221T183901
# search for the available products for each area in ghe gdf, generate a list of those products for each area
#use the dates range from the startdate to enddate
#use the latitude and longitude to search for the data  in the area
#search for the data in the area
#cloud cover less than 30%
#add the list of products to the gdf as a list for each area


# for each area in the gdf
for index, row in gdf.iterrows():
    #search for the data
    products = dag.search(
        productType="S2_MSI_L2A",
        start=row['startdate'].strftime('%Y-%m-%d'),
        end=row['enddate'].strftime('%Y-%m-%d'),
        geom=row['geometry'],
        cloudCover=30
    )

    #add the products to the gdf
    gdf.at[index, 'products'] = products

# #save productlist
# gdf.to_file("mopane_points_products.gpkg", driver="GPKG")

# #load the productlist
# gdf = gpd.read_file("mopane_points_products.gpkg")
# #convert the products which is a string containing a list definition to a list
# gdf['products'] = gdf['products'].apply(eval)


# download the products in the gdf products lists   
for index, row in gdf.iterrows():
    for product in row['products']:
        dag.download(product)




