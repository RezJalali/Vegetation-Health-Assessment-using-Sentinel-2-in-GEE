import ee
import geemap
import numpy as np

# Getting an authorization token from Google Earth Engine
try:
    ee.Initialize('github-projects-464906')
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# 1. DEFINE YOUR AREA OF INTEREST (AOI) AND TIME FRAME
aoi = ee.Geometry.Rectangle([48.180, 30.859, 48.364, 31.080])
start_date = '2024-03-01'
end_date = '2024-10-31'


# 2. SELECT AND FILTER SENTINEL-2 IMAGERY
def get_sentinel2_collection(aoi, start_date, end_date):
    return ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(aoi) \
        .filterDate(start_date, end_date)


# 3. CLOUD MASKING
def mask_s2_clouds(image):
    # Check if the QA60 band exists.
    has_qa60 = image.bandNames().contains('QA60')

    # Define the two different masking methods as functions.
    def mask_with_qa(img):
        qa = img.select('QA60')
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(
            qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        return img.updateMask(mask)

    def mask_with_scl(img):
        scl = img.select('SCL')
        # Keep pixels classified as vegetation, bare soil, water, and unclassified.
        mask = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
        return img.updateMask(mask)

    # Use ee.Algorithms.If to conditionally apply the correct masking method.
    masked_image = ee.Image(ee.Algorithms.If(
        has_qa60,
        mask_with_qa(image),  # Apply QA60 mask if it exists
        mask_with_scl(image)  # Apply SCL mask if it does not
    ))

    # Scale the optical bands and copy properties.
    return masked_image.divide(10000) \
        .select("B.*") \
        .copyProperties(image, ["system:time_start"])


# 4. NDVI CALCULATION
def add_ndvi(image):
    # Sentinel-2 bands: B8 (NIR), B4 (Red)
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)


# Get the Sentinel-2 collection
s2_collection = get_sentinel2_collection(aoi, start_date, end_date)

# Apply cloud masking and add NDVI
s2_processed = s2_collection.map(mask_s2_clouds).map(add_ndvi).select('NDVI')

# 5. MONTHLY MAXIMUM VALUE COMPOSITE (MVC)
# Create a list of months
months = ee.List.sequence(1, 12)


def create_monthly_mvc(month):
    start = ee.Date(start_date).advance(ee.Number(month).subtract(1), 'month')
    end = start.advance(1, 'month')
    monthly_collection = s2_processed.filterDate(start, end)
    # Get the image with the highest NDVI value for each pixel
    return monthly_collection.qualityMosaic('NDVI').set('system:time_start', start.millis())


monthly_mvc_collection = ee.ImageCollection.fromImages(months.map(create_monthly_mvc))

# 6. MEAN OF ALL MVC PRODUCTS
# Calculate the mean of all monthly MVCs to get a single NDVI image for the year
mean_ndvi = monthly_mvc_collection.select('NDVI').mean()
mean_ndvi = mean_ndvi.reproject('EPSG:4326', None, 10)

# # Save the map to an HTML file
# output_file_path = "vegetation_health_map.html"
# m.to_html(output_file_path)
# print(f"\nSUCCESS: Interactive map has been saved to: {output_file_path}")
# print("You can open this file in your web browser.")


# --- Part 7: EXPORT THE FINAL IMAGE TO GOOGLE DRIVE ---

# The previous method of using sampleRectangle() is only for very small areas.
# For large areas like this, the standard workflow is to export the image.
# This process will create a task in your Google Earth Engine account.

# Define the export parameters.
export_params = {
    'image': mean_ndvi,
    'description': 'NDVI_Annual_Mean_Export',  # The name of the task
    'folder': 'GEE_Exports',  # A folder in your Google Drive
    'fileNamePrefix': 'NDVI_mean_2023',  # The name of the file
    'scale': 10,
    'region': aoi,
    'fileFormat': 'GeoTIFF',
    'maxPixels': 1e10  # Use a large number for maxPixels
}

# Start the export task.
task = ee.batch.Export.image.toDrive(**export_params)
task.start()

print("\n---------------------------------------------------------------------------")
print("SUCCESS: Export task started successfully!")
print(f"Task Name: {export_params['description']}")
print("The data is NOT downloaded yet. Please follow the steps below.")
print("---------------------------------------------------------------------------")

# --- Part 8: VISUALIZE THE FINAL IMAGE IN JUPYTER LAB ---

print("\nGenerating a map preview for your notebook...")
print("The full-resolution export is still running in the background.")

# Define visualization parameters for the NDVI layer.
ndvi_palette = [
    'FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718',
    '74A901', '66A000', '529400', '3E8601', '207401', '056201',
    '004C00', '023B01', '011D01', '011301'
]
ndvi_vis_params = {'min': 0.0, 'max': 0.8, 'palette': ndvi_palette}

# Calculate the center of your AOI to center the map.
map_center = aoi.centroid().coordinates().get(1).getInfo(), aoi.centroid().coordinates().get(0).getInfo()

# Create an interactive map object.
m = geemap.Map(center=map_center, zoom=11)
m.add_basemap('SATELLITE')

# Add your final NDVI image as a layer to the map.
# We .clip(aoi) to make the visualization clean and confined to our AOI.
m.addLayer(
    mean_ndvi.clip(aoi),
    ndvi_vis_params,
    'Mean Annual NDVI'
)

# Add a color bar legend and a layer control to the map.
m.add_colorbar(ndvi_vis_params, label="Mean Annual NDVI")
m.add_layer_control()

# Display the map in your Jupyter Lab output cell.
m