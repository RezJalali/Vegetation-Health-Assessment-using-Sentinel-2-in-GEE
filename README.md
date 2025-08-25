# Vegetation-Health-Assessment-using-Sentinel-2-in-GEE
This repository provides a collection of Python scripts that leverage the Google Earth Engine (GEE) API to process Sentinel-2 satellite imagery for vegetation health analysis. The project offers scalable, cloud-based tools to calculate key vegetation indices like NDVI and Leaf Area Index (LAI), ideal for agricultural monitoring, environmental science, and land management applications.

The scripts are designed to be easily customizable and include automated export features for generating analysis-ready GeoTIFFs, along with interactive map previews for immediate visualization within a Jupyter environment.

Features ✨
Multi-Index Support: Includes ready-to-use scripts for calculating both NDVI and LAI.

Robust Cloud Masking: Automatically handles different Sentinel-2 processing baselines by using the QA60 band and falling back to the SCL (Scene Classification Layer) for robust cloud removal.

Advanced Compositing: Uses a Maximum Value Composite (MVC) approach for NDVI to capture peak vegetation greenness and minimize atmospheric interference.

Time-Series Analysis: The LAI script demonstrates how to generate and plot a time-series chart for a specific region, perfect for monitoring crop growth cycles.

Automated Export: Easily export the final, high-resolution raster data directly to your Google Drive.

Interactive Visualization: Instantly preview results on an interactive map within your Jupyter Notebook, complete with legends and layer controls.

# Included Methods
This repository currently includes the following vegetation analysis scripts:

1. NDVI.py - Annual Mean NDVI using MVC
This script calculates the annual mean Normalized Difference Vegetation Index (NDVI), a primary indicator of vegetation density and health. To create a robust, cloud-free annual summary, it uses a Maximum Value Composite (MVC) technique.

**Methodology:** For each month, the script creates a composite image by selecting the pixel with the highest NDVI value from all images captured during that month. These monthly composites are then averaged to produce a smooth and representative annual mean NDVI map.

**Use Case:** Ideal for assessing overall vegetation health for a year, identifying agricultural zones, and monitoring deforestation.
![1](https://github.com/user-attachments/assets/bb32ee3e-f093-4e7e-bae1-276a3f95947e)

2. LAI.py - Leaf Area Index Time Series
This script calculates the Leaf Area Index (LAI), which is a measure of the total leaf area per unit of ground area. It is a critical variable for understanding plant canopy structure and growth.

**Methodology:** LAI is derived from the Weighted Difference Vegetation Index (WDVI) using an empirical formula. The script processes an entire time series of images and calculates the mean LAI over a specific region of interest for each image.

**Use Case:** Perfect for monitoring crop phenology, tracking seasonal growth cycles, and estimating biomass. The script demonstrates how to generate and plot this data over time.
<img width="1237" height="637" alt="1" src="https://github.com/user-attachments/assets/7aed2820-818e-4998-9c3a-050c8ca4781f" />

<img width="1142" height="605" alt="ts" src="https://github.com/user-attachments/assets/a20dd731-b391-4314-aa5e-fb951163a0b6" />

# Interpreting the Output
**Export Task:** For scripts like NDVI.py, an export task will be started in your GEE account. You can monitor its progress in the GEE Code Editor Tasks tab. Once complete, the GeoTIFF file will appear in your Google Drive.

**Interactive Map:** A map will be generated in your Jupyter output, allowing you to visually inspect the results immediately.

**Time-Series Chart:** The LAI.py script will generate a plot showing how the LAI changes over your selected time period.
