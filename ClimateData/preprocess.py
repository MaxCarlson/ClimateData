from io import StringIO
import os
import sys
import csv
from tracemalloc import start
import numpy as np
import pandas as pd
import urllib.request
import json
import datetime
import re
from preprocess_data import *

datadir = './data/raw/'
droughtDir = f'{datadir}drought/'
weatherDir = f'{datadir}weather/'
outputDir = './data/processed/'
order = ['min', 'avg', 'max', 'precip']
months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

weatherFileName = 'weather.csv'
droughtFileName = 'drought.csv'
countyCodesName = 'county_codes.csv'
countyCoordsName = 'county_coords.csv'


#
def download(url, save_path, skip_download_if_save_file_exists = False):

  delete_file = False
  download_contents = None

  # construct friendly name from path filename
  if save_path is not None:
    data_name = os.path.splitext(os.path.basename(save_path))[0]
    friendly_name = data_name.replace("-", " ") \
                            .replace("_", " ")
  else:
    friendly_name = 'data'
    delete_file = True
    save_path = 'download.temp'
  

  def report_hook(count, block_size, total_size):
    percent = int(count * block_size * 100 / total_size)
    print(f'downloading {friendly_name}.... {(count * block_size)/1024} KB', end='\r')

  if not skip_download_if_save_file_exists or not os.path.exists(save_path):
    print(f'downloading {friendly_name}....', end='\r')
    urllib.request.urlretrieve(url, save_path, reporthook=report_hook)
    print('')
  
  # read contents from file
  with open(save_path, 'r') as f:
    download_contents = f.read()

  # delete file
  if delete_file:
    os.remove(save_path)
  
  return download_contents

def convert_countycodes(skip_download_if_save_file_exists):
  global allStatesCounties
  id = 1
  
  with open(f'{outputDir}{countyCodesName}', 'w') as w:
    # header
    w.write('id INTEGER PRIMARY KEY,county_code INTEGER,fips_code INTEGER,county_name VARCHAR(50),state VARCHAR(2),country VARCHAR(3)\n')

    for state_abbr in allStatesCounties:
      state = allStatesCounties[state_abbr]
      counties = state['Counties']
      for county in counties:

        fips_code = county['Fips']
        ncdc_code = county['Ncdc']
        state_name = state['FullName']
        county_name = county['Name']
        
        # prepend '01' to code, indicating county is from united states
        # add 'US' value for country column
        w.write(f'{id},01{ncdc_code},{fips_code},{county_name},{state_abbr},US\n')
        id += 1

def convert_county_coords(skip_download_if_save_file_exists):
  global allStatesCounties
  
  # download coordinate data
  county_boundaries = download('https://public.opendatasoft.com/explore/dataset/us-county-boundaries/download/?format=csv&timezone=America/Los_Angeles&lang=en&use_labels_for_header=true&csv_separator=%3B', f'{weatherDir}us-county-boundaries.csv', skip_download_if_save_file_exists)

  # converts county coords csv
  with open(f'{outputDir}{countyCoordsName}', 'w') as w:
    # this csv contains very large fields so
    # we must increase the field size limit to something larger
    csv.field_size_limit(0x1000000)
    reader = csv.reader(county_boundaries.split('\n'), delimiter=';')
    columns = next(reader)

    # header
    w.write('county_code INTEGER PRIMARY KEY,geo_point VARCHAR(50),geo_shape TEXT[][]\n')

    # iterate lines
    id = 1
    for row in reader:
      if len(row) > 8:
        geo_point = row[0]
        geo_shape = row[1]
        state = row[8]
        county_code = row[3]
        skip = False

        if state in allStatesCounties:
          county_code = f'{allStatesCounties[state]["StateCode"]}{county_code}'
        else:
          skip = True
          print(f'skipping county coord {row[2:]}')

        if not skip:
          # process geo shape into our db format
          shape_json = json.loads(geo_shape)
          shape_processed = '"{'
          for coord in shape_json["coordinates"][0]:
            shape_processed += f'{{""{coord[0]}"",""{coord[1]}""}},'
          shape_processed = shape_processed.strip(',') + '}"'

          # prepend '01' to code, indicating county is from united states
          w.write(f'01{county_code},"{geo_point}",{shape_processed}\n')
          id += 1

def build_weather_table(skip_download_if_save_file_exists):
    filesToStrip = ['avgtmp', 'maxtmp', 'mintmp', 'precip']
    urlPaths = ['climdiv-tmpccy', 'climdiv-tmaxcy', 'climdiv-tmincy', 'climdiv-pcpncy']
    colsPrefix = ['tmp_avg', 'tmp_max', 'tmp_min', 'precip']
    dataFiles = {}

    icols = [i for i in range(len(months) + 1)]
    dtypes = [str] + [str] * len(months)
    d = pd.DataFrame(np.vstack([icols, dtypes])).to_dict(orient='records')[1]
    dff = pd.DataFrame()
    
    # download weather data directory listing
    weather_directory = download('https://www1.ncdc.noaa.gov/pub/data/cirs/climdiv/', None)

    # download weather data
    for filename, url_path in zip(filesToStrip, urlPaths):
      url_path_idx = weather_directory.index(url_path)
      url_path_end_idx = weather_directory.index('"', url_path_idx)
      path = weather_directory[url_path_idx:url_path_end_idx]
      dataFiles[filename] = download(f'https://www1.ncdc.noaa.gov/pub/data/cirs/climdiv/{path}', f'{weatherDir}climdiv-{filename}.txt', skip_download_if_save_file_exists)


    for filename, prefix, i in zip(filesToStrip, colsPrefix, range(len(colsPrefix))):

        # Build column names
        cols = ['id INTEGER PRIMARY KEY']
        for m in months:
            cols.append(f'{prefix}_{m} FLOAT')

        s = re.sub('( |\t)+', ' ', dataFiles[filename])
        strio = StringIO(s)
        df = pd.read_csv(strio, delimiter=' ', header=None, index_col=False, usecols=icols, dtype=d)
        
        # Remove datatype field, since it's the same throughout the entirity of each file
        s = df.iloc[:,0]
        s = s.str[0:5] + s.str[7:]
        df.iloc[:,0] = s

        if i == 0:
            # Add USA Country code
            cc = pd.DataFrame(['01']*len(df), dtype=(str))
            df.iloc[:,0] = cc.iloc[:,0].str[:] + df.iloc[:,0].str[:]

            # Add columns (along with id column this first time)
            df.columns = cols
            dff = pd.DataFrame(df, columns=cols)
        else:
            # Add columns
            df.columns = cols
            # Insure id parity here! 
            for v1, v2 in zip(dff.iloc[:,0], df.iloc[:,0]):
                # Don't compare country code as it hasn't been added to anything but the primary id
                if v1[2:] != v2:
                    raise RuntimeError('Invalid Data Join')

            df = df.iloc[:,1:]
            dff = dff.join(df)

        print(dff)

        # Create individual files
        #df.to_csv(f'{datadir}{filename}.csv', header=False, index=False)

    # WARNING: If you open this file in Excel without specifying the first 
    # column is a string, it will remove all the first zeros in the ID column
    dff.to_csv(f'{outputDir}{weatherFileName}', index=False)
    print('Succesful merge!')

def build_drought_table(skip_download_if_save_file_exists):
  
    urlPaths = ['climdiv-pdsist', 'climdiv-phdist', 'climdiv-pmdist', 'climdiv-sp01st', 'climdiv-sp02st', 'climdiv-sp03st', 'climdiv-sp06st', 'climdiv-sp09st', 'climdiv-sp12st', 'climdiv-sp24st']
    dataFiles = {}

    icols = [i for i in range(len(months) + 1)]
    dtypes = [str] + [str] * len(months)
    d = pd.DataFrame(np.vstack([icols, dtypes])).to_dict(orient='records')[1]
    dff = pd.DataFrame()

    # download weather data directory listing
    weather_directory = download('https://www1.ncdc.noaa.gov/pub/data/cirs/climdiv/', None)

    # download weather data
    for url_path in urlPaths:
      url_path_idx = weather_directory.index(url_path)
      url_path_end_idx = weather_directory.index('"', url_path_idx)
      path = weather_directory[url_path_idx:url_path_end_idx]
      dataFiles[url_path] = download(f'https://www1.ncdc.noaa.gov/pub/data/cirs/climdiv/{path}', f'{droughtDir}{url_path}.txt', skip_download_if_save_file_exists)

    for i, path in enumerate(urlPaths):
        datatype = path[8:]
        cols = ['id INTEGER PRIMARY KEY']
        for m in months:
            cols.append(f'{datatype}_{m} FLOAT')

        newLines = []
        lines = dataFiles[path].split('\n')
        for line in lines:
            parts = line.split()
            if len(parts) > 0:

                # TODO: Add the years of 1895 & 1896 back in. It looks like the bad 
                # data comes from the rolling averages of 12 & 24 months respectively
                # (which makes sense) - but we'd need to handle this in the ui/db and 
                # not allow the user to select these two values for that date range
                if int(parts[0][0:3]) > 48 or int(parts[0][-4:]) < 1897:
                    continue
                parts[0] = parts[0][1:3] + parts[0][6:]
                newLines.append(parts)

        df = pd.DataFrame(newLines, columns=cols)

        if i == 0:
            # Add USA Country code
            cc = pd.DataFrame(['01']*len(df), dtype=(str))
            df.iloc[:,0] = cc.iloc[:,0].str[:] + df.iloc[:,0].str[:]

            # Add columns (along with id column this first time)
            df.columns = cols
            dff = pd.DataFrame(df, columns=cols)
        else:
            # Add columns
            df.columns = cols
            # Insure id parity here! 
            for v1, v2 in zip(dff.iloc[:,0], df.iloc[:,0]):
                # Don't compare country code as it hasn't been added to anything but the primary id
                if v1[2:] != v2:
                    raise RuntimeError('Invalid Data Join')

            df = df.iloc[:,1:]
            dff = dff.join(df)
        print(dff)
    dff.to_csv(f'{outputDir}{droughtFileName}', index=False)
    print('Succesful merge!')

def process_files(force_data_redownload = True):
    # process county codes and test the output
    build_drought_table(not force_data_redownload)
    build_weather_table(not force_data_redownload)
    convert_countycodes(not force_data_redownload)
    convert_county_coords(not force_data_redownload)

def create_working_directory():
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    if not os.path.exists(droughtDir):
        os.makedirs(droughtDir)
    if not os.path.exists(weatherDir):
        os.makedirs(weatherDir)

if __name__ == '__main__':
    create_working_directory()
    process_files()

