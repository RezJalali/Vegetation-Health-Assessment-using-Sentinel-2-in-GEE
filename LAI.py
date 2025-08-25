import ee
import geemap
import pandas as pd
import matplotlib.pyplot as plt

# Getting an authorization token from Google Earth Engine
try:
    ee.Initialize('ee-rezajalali') # enter your defined cloud project to get access to GEE server
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

# 1. DEFINE YOUR AREA OF INTEREST (AOI) AND TIME FRAME
aoi = ee.Geometry.Rectangle([47.95, 29.55, 49.38, 32.43])
start_date = '2020-01-01'
end_date = '2025-01-01'
# Define a smaller region of a known cropland to visualize LAI time series dynamics 
time_series_aoi = ee.Geometry.Rectangle([48.180, 30.859, 48.364, 31.080])


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


# 4. LAI CALCULATION
def add_LAI(image):
  # Sentinel-2 bands: B8 (NIR), B4 (Red)
  # WDVI = Weighted difference vegetation index
  # WDVI = R_nir - 1.06*R_red
  wdvi = image.expression('NIR-1.06*Red', {'NIR':image.select('B8'),'Red':image.select('B4')})
  LAI = wdvi.expression('10.22*wdvi+0.4768', {'wdvi':wdvi})
  return LAI.copyProperties(image,['system:time_start'])



# Get the Sentinel-2 collection
s2_collection = get_sentinel2_collection(aoi, start_date, end_date)

# Apply cloud masking and add LAI
LAI_collection = s2_collection.map(mask_s2_clouds).map(add_LAI)

LAI_mean = LAI_collection.mean().clip(aoi)

# 7. Visualization and Exporting the final Results
print("\nGenerating a map preview for your notebook...")
# Define visualization parameters for the NDVI layer.
              # Blue  # Yellow    # Green
              # water # bare-ground # dense vegetation 
LAI_palette = ['2308ff','fffd1e','21cd12']
LAI_vis_params = {'min': -3, 'max': 4, 'palette': LAI_palette}

# Calculate the center of your AOI to center the map.
map_center = aoi.centroid().coordinates().get(1).getInfo(), aoi.centroid().coordinates().get(0).getInfo()

# Create an interactive map object.
vis_map = geemap.Map(center=map_center, zoom=7)
vis_map.add_basemap('SATELLITE')

# Add your final LAI image as a layer to the map.
vis_map.addLayer(
    LAI_mean,
    LAI_vis_params,
    'Mean LAI'
)

# Add a color bar legend and a layer control to the map.
vis_map.add_colorbar(LAI_vis_params, label="Mean LAI")
vis_map.add_layer_control()

# Display the map in your Jupyter Lab output cell.
display(vis_map)
#===========================================================================
# Time Series Visualization over a known crop land
#===========================================================================
def mean_region (image):
    mean_value = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=time_series_aoi,
        scale=10,
        maxPixels=1e10)
    # Return a new feature with the mean value and the image's timestamp.
    return ee.Feature(None, {
        'mean': mean_value.get('constant'),
        'system:time_start': image.get('system:time_start')
    })

mean_lai_series =  LAI_collection.map(mean_region)
timeseries_info = mean_lai_series.getInfo()

# Extract the properties from the feature collection
data = [{'time': f['properties']['system:time_start'], 'mean': f['properties']['mean']} for f in timeseries_info['features']]

df = pd.DataFrame(data)
# Remove any null values that might result from fully masked images
df.dropna(inplace=True)

# Convert 'time' column from milliseconds to datetime objects
df['time'] = pd.to_datetime(df['time'], unit='ms')
df = df.sort_values(by='time')


# Plot the time series
plt.figure(figsize=(12, 6))
plt.plot(df['time'], df['mean'], marker='.', linestyle='-')
plt.title('LAI Time Series')
plt.xlabel('Date')
plt.ylabel('Mean LAI')
plt.grid(True)
plt.show()


# Export to Drive
# Define the export parameters.
# This process will create a task in your Google Earth Engine account.
export_params = {
    'image': LAI_mean,
    'description': 'LAI_Mean_Export',  # The name of the task
    'folder': 'GEE_Exports',  # A folder in your Google Drive
    'fileNamePrefix': 'LAI_mean',  # The name of the file
    'scale': 10,
    'region': aoi,
    'fileFormat': 'GeoTIFF',
    'maxPixels': 1e10 
}

# Start the export task.
task = ee.batch.Export.image.toDrive(**export_params)
task.start()

print("\n---------------------------------------------------------------------------")
print("SUCCESS: Export task started successfully!")
print(f"Task Name: {export_params['description']}")
print("The data is NOT downloaded yet. Please check your Google Drive.")
print("---------------------------------------------------------------------------")

