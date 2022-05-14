from io import StringIO
import os
import sys
import csv
from tracemalloc import start
import numpy as np
import pandas as pd
import urllib.request
import urllib.error
import json
import datetime
import re
import zipfile
import shutil
from preprocess_data import *

datadir = './data/raw/'
droughtDir = f'{datadir}drought/'
weatherDir = f'{datadir}weather/'
featuresDir = f'{datadir}features/'
outputDir = './data/processed/'
order = ['min', 'avg', 'max', 'precip']
months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

weatherFileName = 'weather.csv'
droughtFileName = 'drought.csv'
countyCodesName = 'county_codes.csv'
countyCoordsName = 'county_coords.csv'
populationName = 'population.csv'
featuresName = 'features.csv'

outputFileNames = [
  weatherFileName,
  droughtFileName,
  countyCodesName,
  countyCoordsName,
  populationName,
  featuresName,
]


#
def download(url, save_path, skip_download_if_save_file_exists = False, read = True):

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
  if read:
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

def build_population_table(skip_download_if_save_file_exists):
  global allStatesCounties

  # https://data.nber.org/census/pop/cencounts.csv 1900-1990
  # https://api.census.gov/data/2000/dec/sf1?get=P001001,NAME&for=county:*

  # get historical data
  pop_1900_to_1990 = download("https://data.nber.org/census/pop/cencounts.csv", f'{datadir}pop-1900-1990.csv', skip_download_if_save_file_exists= skip_download_if_save_file_exists)

  # generates population csv
  with open(f'{outputDir}{populationName}', 'w') as w:
    reader = csv.reader(pop_1900_to_1990.split('\n'), delimiter=',')
    columns = next(reader)
    us_total_pop = next(reader)
    id = 1

    # header
    w.write('id INTEGER PRIMARY KEY,county_code INTEGER,year INTEGER,population INTEGER\n')

    # iterate historical data
    for row in reader:
      if len(row) == 12:

        # name is state code then name
        # some rows are aggregate state data
        # valid county name is "AL Autauga County"
        # agg state name is "AL Alabama"
        name = row[11]
        state_code = name[:2]
        name = name[3:]
        fips = row[10]
        county = None
        skip = False

        if fips[2:] == '000':
          # fips code of 000 means its the state/country
          # not the county
          skip = True
        elif state_code in allStatesCounties:
          counties = allStatesCounties[state_code]["Counties"]
          filtered_counties = list(filter(lambda x: x["Fips"] == fips, counties))
          if len(filtered_counties) == 1:
            county = filtered_counties[0]
          else:
            skip = True
            print(f'skipping 1900-1990 population for {state_code} {name} {fips}')
        else:
          skip = True
          print(f'skipping 1900-1990 population for {state_code} {name} {fips}')

        if not skip:
          
          for i in range(10):
            # prepend '01' to code, indicating county is from united states
            value = row[i]
            if value == '.':
              value = '-1'
            w.write(f'{id},01{county["Ncdc"]},{1900 + (i * 10)},{value}\n')
            id += 1

    # iterate new data until we can't
    year = 2000
    while True:

      # try and download data
      # download will throw exception on 404
      # which happens when we reach the end of the available data
      pop_data = None
      try:
        pop_data_json = download(f"https://api.census.gov/data/{year}/dec/sf1?get=P001001,NAME&for=county:*", f'{datadir}pop-{year}.csv', skip_download_if_save_file_exists= skip_download_if_save_file_exists)
        pop_data = json.loads(pop_data_json)
      except:
        break
      

      # first row is header
      for row in pop_data[1:]:
        population = row[0]
        name = row[1] # "county name, state name"
        state_id = row[2]
        county_fips = row[3] # just county fips, no state id
        fips = f'{state_id}{county_fips}'
        state_name = name.split(',')[1].strip()
        skip = False
        county = None
        
        state_code = next((s for s in allStatesCounties if allStatesCounties[s]["FullName"] == state_name), None)
        if state_code is None:
          skip = True
          print(f'skipping {year} population for {name} {state_id} {county_fips}')
        else:
          state = allStatesCounties[state_code]
          county = next((c for c in state["Counties"] if c["Fips"] == fips), None)
          if county is None:
            skip = True
            print(f'skipping {year} population for {name} {state_id} {county_fips}')

        if not skip:
        
          # prepend '01' to code, indicating county is from united states
          w.write(f'{id},01{county["Ncdc"]},{year},{population}\n')
          id += 1


      year += 10

def build_features_table(skip_download_if_save_file_exists):
  # https://geonames.usgs.gov/docs/stategaz/NationalFile.zip

  # get dataset
  download("https://geonames.usgs.gov/docs/stategaz/NationalFile.zip", f'{datadir}features.zip', read= False, skip_download_if_save_file_exists= skip_download_if_save_file_exists)

  # delete existing zip extraction
  if os.path.exists(featuresDir):
    shutil.rmtree(featuresDir)

  # unzip dataset
  with zipfile.ZipFile(f'{datadir}features.zip', 'r') as zip_ref:
    zip_ref.extractall(featuresDir)

  # get extracted filename
  dataset_file = os.listdir(featuresDir)[0]
  
  # converts features csv
  with open(f'{featuresDir}{dataset_file}', 'r', encoding='utf-8') as r:
    lines = r.readlines()
    
    with open(f'{outputDir}{featuresName}', 'w', encoding='utf-8') as w:
      # this csv contains very large fields so
      # we must increase the field size limit to something larger
      csv.field_size_limit(0x1000000)
      reader = csv.reader(lines, delimiter='|')
      columns = next(reader)

      # header
      w.write('id INTEGER PRIMARY KEY,county_code INTEGER,feature_type VARCHAR(50),feature_name VARCHAR(200),elevation_ft INTEGER\n')

      # iterate lines
      id = 1

      for row in reader:
        if len(row) == 20:
          name = row[1]
          name = name.replace(",","")
          feature_type = row[2]
          state_code = row[3]
          fips = f'{row[4]}{row[6]}'
          elevation = row[16]
          ncdc = None
          skip = False

          if state_code in allStatesCounties:
            ncdc = f'{allStatesCounties[state_code]["StateCode"]}{row[6]}'
          else:
            skip = True
            print(f'skipping feature {name} {feature_type} {state_code} {fips}')

          if not elevation:
            skip = True
            print(f'skipping feature {name} {feature_type} {state_code} {fips} FOR MISSING ELEVATION')

          if not skip:
            # prepend '01' to code, indicating county is from united states
            w.write(f'{id},01{ncdc},{feature_type},{name},{elevation}\n')

def has_processed_files():
  for outputFileName in outputFileNames:
    if not os.path.exists(f'{outputDir}{outputFileName}'):
      return False
  
  return True

def process_files(force_data_redownload = True):
  # if not forced redownload and we've already processed everything
  # exit
  if not force_data_redownload:
    if has_processed_files():
      return

  # process county codes and test the output
  try:
    build_drought_table(not force_data_redownload)
  except Exception as error:
    print(error)

  try:
    build_weather_table(not force_data_redownload)
  except Exception as error:
    print(error)

  try:
    convert_countycodes(not force_data_redownload)
  except Exception as error:
    print(error)

  try:
    convert_county_coords(not force_data_redownload)
  except Exception as error:
    print(error)

  try:
    build_population_table(not force_data_redownload)
  except Exception as error:
    print(error)

  try:
    build_features_table(not force_data_redownload)
  except Exception as error:
    print(error)

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

