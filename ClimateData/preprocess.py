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

datadir = './data/raw/'
droughtDir = f'{datadir}drought/'
outputDir = './data/processed/'
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

# ensures that each entry in complete.csv has a corresponding county mapping in county_codes.csv
def test_countycodes():
  missing_codes = []

  # read in county code mappings
  county_map = {}
  with open(f'{outputDir}{countyCodesName}', 'r') as f:
    # eat header
    f.readline()

    lines = f.readlines()
    for line in lines:
      line = line.strip()
      values = line.split(',')

      # store county code as key and uid as value
      county_map[values[1]] = values[0]

  # iterate over data set
  with open(f'{outputDir}{weatherFileName}', 'r') as f:
    # eat header
    f.readline()

    lines = f.readlines()
    for line in lines:
      line = line.strip()
      values = line.split(',')

      # read first 7 characters of id as county code
      code = values[0][:7]
      
      if not code in county_map and not code in missing_codes:
        missing_codes.append(code)
        print(f'missing {code}')

def convert_countycodes():
  state_map = {}
  with open(f'{datadir}county-state-codes.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
      line = line.strip()
      values = line.split(' ')
      state_map[values[1]] = values[0]


  # read in postal fips to ncdc fips from county-to-climdivs.txt
  county_map = {}
  with open(f'{datadir}county-to-climdivs.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
      line = line.strip()
      if len(line) == 16:
        values = line.split(' ')
        county_map[values[0]] = values[1]

  # converts tab-delimited county codes to comma delimited csv
  with open(f'{datadir}us-county-codes.txt', 'r') as f:
    with open(f'{outputDir}{countyCodesName}', 'w') as w:

      # header
      w.write('id INTEGER PRIMARY KEY,county_code INTEGER,fips_code INTEGER,county_name VARCHAR(50),state VARCHAR(2),country VARCHAR(3)\n')

      # eat header
      f.readline()

      # iterate lines
      lines = f.readlines()
      id = 1
      for line in lines:
        parts = line.split('\t')

        fips_code = parts[0]
        fips_state_code = int(fips_code[:2])
        state = parts[2].strip()
        name = parts[1]
        skip = False
        #if county_code in county_map:
        #  county_code = county_map[county_code]
        if state in state_map:
          county_code = f'{state_map[state]}{fips_code[2:]}'
        else:
          skip = True
          print(f'skipping {line.strip()}')

        if not skip:
          # prepend '01' to code, indicating county is from united states
          # add 'US' value for country column
          w.write(f'{id},01{county_code},{fips_code},{name},{state},US\n')
          id += 1

def convert_county_coords():
  # download coordinate data
  county_boundaries = download('https://public.opendatasoft.com/explore/dataset/us-county-boundaries/download/?format=csv&timezone=America/Los_Angeles&lang=en&use_labels_for_header=true&csv_separator=%3B', f'{datadir}us-county-boundaries.csv')

  state_map = {}
  with open(f'{datadir}county-state-codes.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
      line = line.strip()
      values = line.split(' ')
      state_map[values[1]] = values[0]


  # read in postal fips to ncdc fips from county-to-climdivs.txt
  county_map = {}
  with open(f'{datadir}county-to-climdivs.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
      line = line.strip()
      if len(line) == 16:
        values = line.split(' ')
        county_map[values[0]] = values[1]

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

        if state in state_map:
          county_code = f'{state_map[state]}{county_code}'
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

def build_weather_table():
    filesToStrip = ['avgtmp', 'mintmp', 'maxtmp', 'precip']
    urlPaths = ['climdiv-tmpccy', 'climdiv-tmincy', 'climdiv-tmaxcy', 'climdiv-pcpncy']
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
      dataFiles[filename] = download(f'https://www1.ncdc.noaa.gov/pub/data/cirs/climdiv/{path}', f'{datadir}climdiv-{filename}.txt')


    for filename, prefix, i in zip(filesToStrip, colsPrefix, range(len(colsPrefix))):

        # Build column names
        cols = ['id INTEGER PRIMARY KEY']
        for m in months:
            cols.append(f'{prefix}_{m} FLOAT')

        s = re.sub('[^\S\r\n]+', ' ', dataFiles[filename])
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

def build_drought_table():
  
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
      dataFiles[url_path] = download(f'https://www1.ncdc.noaa.gov/pub/data/cirs/climdiv/{path}', f'{droughtDir}{url_path}.txt')

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

def processFiles():
    # process county codes and test the output
    build_drought_table()
    build_weather_table()
    convert_countycodes()
    convert_county_coords()

    # TODO: Move this into a test suite
    test_countycodes()

def create_working_directory():
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    if not os.path.exists(droughtDir):
        os.makedirs(droughtDir)

if __name__ == '__main__':
    create_working_directory()
    processFiles()
