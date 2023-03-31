import random
import statsmodels.api as sm
import numpy.polynomial.polynomial as poly
from database import *
import psycopg2
import logging
import os
import numpy as np
import string
import pandas as pd


# Predefined lists
states = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME',
          'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM',
          'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
          'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']
# Note, Remove ID col or add :
# df = df.loc[:, ~df.columns.duplicated()]

temp_avg_cols = ['id', 'tmp_avg_jan', 'tmp_avg_feb', 'tmp_avg_mar', 'tmp_avg_apr', 'tmp_avg_may', 'tmp_avg_jun',
                 'tmp_avg_jul',
                 'tmp_avg_aug', 'tmp_avg_sep', 'tmp_avg_oct', 'tmp_avg_nov', 'tmp_avg_dec']
temp_max_cols = ['id', 'tmp_max_jan', 'tmp_max_feb', 'tmp_max_mar', 'tmp_max_apr', 'tmp_max_may', 'tmp_max_jun',
                 'tmp_max_jul',
                 'tmp_max_aug', 'tmp_max_sep', 'tmp_max_oct', 'tmp_max_nov', 'tmp_max_dec']
temp_min_cols = ['id', 'tmp_min_jan', 'tmp_min_feb', 'tmp_min_mar', 'tmp_min_apr', 'tmp_min_may', 'tmp_min_jun',
                 'tmp_min_jul',
                 'tmp_min_aug', 'tmp_min_sep', 'tmp_min_oct', 'tmp_min_nov', 'tmp_min_dec']
precip_cols = ['id', 'precip_jan', 'precip_feb', 'precip_mar', 'precip_apr', 'precip_may', 'precip_jun', 'precip_jul',
               'precip_aug', 'precip_sep', 'precip_oct', 'precip_nov', 'precip_dec']
coeff_cols = list(string.ascii_lowercase)
months_dict = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10,
               'nov': 11, 'dec': 12}

''' Query to get list of ids, county codes, county names, states, and countries from DB'''


def get_county_codes_as_df():
    cols = ['id', 'county_code', 'fips_code', 'county_name', 'state', 'country']
    conn = psycopg2.connect(f"host=localhost dbname=postgres user=postgres password=PASSWORD")
    cur = conn.cursor()
    query = "SELECT * FROM county_codes"
    cur.execute(query)
    res = pd.DataFrame(cur.fetchall(), columns=cols)
    cur.close()
    conn.close()
    return res


''' Wrapper to get weather data split into their respective df (avg, max, min, precip) '''


def get_data_dfs(row):
    # Could use state from for loop...
    # However, want to stay consistent with state recorded in db record
    start_year = 1895
    end_year = 2021
    country = 'US'
    county = row['county_name']
    state = row['state']

    # DB call -> Returns pd.Dataframe
    avg_data_df = get_data_for_single_county(temp_avg_cols, county, state, country, start_year, end_year)
    max_data_df = get_data_for_single_county(temp_max_cols, county, state, country, start_year, end_year)
    min_data_df = get_data_for_single_county(temp_min_cols, county, state, country, start_year, end_year)
    precip_data_df = get_data_for_single_county(precip_cols, county, state, country, start_year, end_year)

    return [avg_data_df, max_data_df, min_data_df, precip_data_df]


''' Get data in x & y format per df '''


def get_xy_data(df):
    month = 12
    x_dates_format = []
    x_data = []
    start_year = int(str(df['id'].iloc[0])[6:])
    end_year = int(str(df['id'].iloc[-1])[6:])

    # range(start_year, end_year) == df.shape[0] (num of rows)
    # Append date formatted
    for i in range(start_year, end_year + 1):
        for j in range(1, month + 1):
            x_dates_format.append(str(i)[-4:] + '-' + str(j))
            x_data.append(int(str(i)[-4:]) + (j - 1) / 12)

    # Append temp/precip values
    y_data = []
    for i, row in df.iterrows():
        for j in row[1:month + 1]:
            y_data.append(j)

    return [x_data, y_data, x_dates_format]


def get_xy_data_for_months(df, month=12):
    x_dates_format = []
    x_data = []
    start_year = int(str(df['id'].iloc[0])[6:])
    end_year = int(str(df['id'].iloc[-1])[6:])

    # range(start_year, end_year) == df.shape[0] (num of rows)
    # Append date formatted
    for i in range(start_year, end_year + 1):
        x_data.append(int(str(i)[-4:]))

    # Append temp/precip values
    y_data = []
    for i, row in df.iterrows():
        y_data.append(row[month])

    return [x_data, y_data, x_dates_format]


''' Builds csv for county polynomial coefficents '''


def build_poly_coeffs_for_county_csv(deg, deriv=0):
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Dynamically create column headers from 'a' ... deg
    cols = None
    if deriv > 0:
        cols = np.hstack(['State', 'County', coeff_cols[:deg + 1], [letter + "'" for letter in coeff_cols[:deg]]])
    else:
        cols = np.hstack(['State', 'County', coeff_cols[:deg + 1]])

    # Always init
    avg_data_rows = []
    max_data_rows = []
    min_data_rows = []
    precip_data_rows = []
    missed_counties = []

    for state in states:
        print(f"Storing sub-dataframe for state: {state}")

        # Get county codes, names, state, country etc..
        county_codes_df = get_county_codes_as_df()

        # Get df that matches current state
        state_df = county_codes_df[(county_codes_df['state'] == state)]
        state_df.reset_index()  # make sure indices pair with number of rows

        for index, row in state_df.iterrows():
            print(f"Building and storing coefficients for county: {row['county_name']}")
            [avg_df, max_df, min_df, precip_df] = get_data_dfs(row)

            # TODO not best conditional, but check if there was no weather data based on county passed in
            if avg_df.empty is True and max_df.empty is True and min_df.empty is True and precip_df.empty is True:
                logging.warning(f'Unable to get weather data for county: {row["county_name"]} state: {row["state"]}')
                missed_counties.append([row['state'], row['county_name'], row['county_code']])
                continue

            # Process data
            [x_avg, y_avg, x_avg_dates] = get_xy_data(avg_df)
            [x_max, y_max, x_max_dates] = get_xy_data(max_df)
            [x_min, y_min, x_min_dates] = get_xy_data(min_df)
            [x_precip, y_precip, x_precip_dates] = get_xy_data(precip_df)

            # Get polynomial coefficents
            avg_coeffs = poly.polyfit(x_avg, y_avg, deg)
            max_coeffs = poly.polyfit(x_max, y_max, deg)
            min_coeffs = poly.polyfit(x_min, y_min, deg)
            precip_coeffs = poly.polyfit(x_precip, y_precip, deg)

            # Dynamically add coefficients (any size)
            if deriv > 0:
                assert cols.size > deg + 3
                avg_deriv = np.polyder(avg_coeffs[::-1], deriv)
                max_deriv = np.polyder(max_coeffs[::-1], deriv)
                min_deriv = np.polyder(min_coeffs[::-1], deriv)
                precip_deriv = np.polyder(precip_coeffs[::-1], deriv)

                avg_data_rows.append(np.hstack([row['state'], row['county_name'], avg_coeffs[::-1], avg_deriv]))
                max_data_rows.append(np.hstack([row['state'], row['county_name'], max_coeffs[::-1], max_deriv]))
                min_data_rows.append(np.hstack([row['state'], row['county_name'], min_coeffs[::-1], min_deriv]))
                precip_data_rows.append(
                    np.hstack([row['state'], row['county_name'], precip_coeffs[::-1], precip_deriv]))
            else:
                avg_data_rows.append(np.hstack([row['state'], row['county_name'], avg_coeffs[::-1]]))
                max_data_rows.append(np.hstack([row['state'], row['county_name'], max_coeffs[::-1]]))
                min_data_rows.append(np.hstack([row['state'], row['county_name'], min_coeffs[::-1]]))
                precip_data_rows.append(np.hstack([row['state'], row['county_name'], precip_coeffs[::-1]]))

    # After data has been looped and appended to, create new dfs to write to csv
    avg_poly_df = pd.DataFrame(avg_data_rows, columns=cols)
    max_poly_df = pd.DataFrame(max_data_rows, columns=cols)
    min_poly_df = pd.DataFrame(min_data_rows, columns=cols)
    precip_poly_df = pd.DataFrame(precip_data_rows, columns=cols)

    # Write to csv
    avg_poly_df.to_csv(f"{deg}_avg_county_coeffs.csv", sep=',', encoding='utf-8', index=False)
    max_poly_df.to_csv(f"{deg}_max_poly_coeffs.csv", sep=',', encoding='utf-8', index=False)
    min_poly_df.to_csv(f"{deg}_min_poly_coeffs.csv", sep=',', encoding='utf-8', index=False)
    precip_poly_df.to_csv(f"{deg}_precip_poly_coeffs.csv", sep=',', encoding='utf-8', index=False)
    print(f'Successfully wrote polynomial coeffs to csv!')

    # Write all counties missed from line 114-117 check
    if not os.path.exists('missed_counties.txt'):
        print(f'Writing missed counties to text file!')
        with open(f'missed_counties.txt', 'w') as text_file:
            for line in missed_counties:
                text_file.write(
                    'state: ' + str(line[0]) + ', county: ' + str(line[1]) + ', county_code: ' + str(line[2]) + '\n')
        print(f'Successfully wrote missed counties to text file!')


def build_coeffs_by_month_seperate_files(deg, deriv=0, months=None):
    # Default
    if months is None:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Dynamically create column headers from 'a' ... deg
    cols = None
    if deriv > 0:
        cols = np.hstack(['State', 'County', coeff_cols[:deg + 1], [letter + "'" for letter in coeff_cols[:deg]]])
    else:
        cols = np.hstack(['State', 'County', coeff_cols[:deg + 1]])

    # Always init
    avg_data_rows = []
    max_data_rows = []
    min_data_rows = []
    precip_data_rows = []
    missed_counties = []

    for month in months:
        for state in states:
            if state != 'OR':
                continue
            print(f"Storing sub-dataframe for state: {state}")

            # Get county codes, names, state, country etc..
            county_codes_df = get_county_codes_as_df()

            # Get df that matches current state
            state_df = county_codes_df[(county_codes_df['state'] == state)]
            state_df.reset_index()  # make sure indices pair with number of rows

            for index, row in state_df.iterrows():
                if row['county_name'] != 'Clackamas':
                    continue
                print(f"Building and storing coefficients for county: {row['county_name']}")
                [avg_df, max_df, min_df, precip_df] = get_data_dfs(row)

                # TODO not best conditional, but check if there was no weather data based on county passed in
                if avg_df.empty is True and max_df.empty is True and min_df.empty is True and precip_df.empty is True:
                    logging.warning(
                        f'Unable to get weather data for county: {row["county_name"]} state: {row["state"]}')
                    missed_counties.append([row['state'], row['county_name'], row['county_code']])
                    continue

                # Process data
                [x_avg, y_avg, x_avg_dates] = get_xy_data_for_months(avg_df, months_dict[month])
                [x_max, y_max, x_max_dates] = get_xy_data_for_months(max_df, months_dict[month])
                [x_min, y_min, x_min_dates] = get_xy_data_for_months(min_df, months_dict[month])
                [x_precip, y_precip, x_precip_dates] = get_xy_data_for_months(precip_df, months_dict[month])

                # Get polynomial coefficents
                avg_coeffs = poly.polyfit(x_avg, y_avg, deg)
                max_coeffs = poly.polyfit(x_max, y_max, deg)
                min_coeffs = poly.polyfit(x_min, y_min, deg)
                precip_coeffs = poly.polyfit(x_precip, y_precip, deg)

                # Dynamically add coefficients (any size)
                if deriv > 0:
                    assert cols.size > deg + 3
                    avg_deriv = np.polyder(avg_coeffs[::-1], deriv)
                    max_deriv = np.polyder(max_coeffs[::-1], deriv)
                    min_deriv = np.polyder(min_coeffs[::-1], deriv)
                    precip_deriv = np.polyder(precip_coeffs[::-1], deriv)

                    avg_data_rows.append(
                        np.hstack([row['state'], row['county_name'], avg_coeffs[::-1], avg_deriv]))
                    max_data_rows.append(
                        np.hstack([row['state'], row['county_name'], max_coeffs[::-1], max_deriv]))
                    min_data_rows.append(
                        np.hstack([row['state'], row['county_name'], min_coeffs[::-1], min_deriv]))
                    precip_data_rows.append(
                        np.hstack([row['state'], row['county_name'], precip_coeffs[::-1], precip_deriv]))
                else:
                    avg_data_rows.append(np.hstack([row['state'], row['county_name'], avg_coeffs[::-1]]))
                    max_data_rows.append(np.hstack([row['state'], row['county_name'], max_coeffs[::-1]]))
                    min_data_rows.append(np.hstack([row['state'], row['county_name'], min_coeffs[::-1]]))
                    precip_data_rows.append(np.hstack([row['state'], row['county_name'], precip_coeffs[::-1]]))
        # After data has been looped and appended to, create new dfs to write to csv
        avg_poly_df = pd.DataFrame(avg_data_rows, columns=cols)
        max_poly_df = pd.DataFrame(max_data_rows, columns=cols)
        min_poly_df = pd.DataFrame(min_data_rows, columns=cols)
        precip_poly_df = pd.DataFrame(precip_data_rows, columns=cols)

        # Write to csv
        avg_poly_df.to_csv(f"{month}_{deg}_avg_county_coeffs.csv", sep=',', encoding='utf-8', index=False)
        max_poly_df.to_csv(f"{month}_{deg}_max_poly_test.csv", sep=',', encoding='utf-8', index=False)
        min_poly_df.to_csv(f"{month}_{deg}_min_poly_test.csv", sep=',', encoding='utf-8', index=False)
        precip_poly_df.to_csv(f"{month}_{deg}_precip_poly_test.csv", sep=',', encoding='utf-8', index=False)
        print(f'Successfully wrote polynomial coeffs to csv!')


def build_coeffs_by_month_single_file(deg, deriv=0, months=None):
    # Default
    if months is None:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Dynamically create column headers from 'a' ... deg
    cols = None
    if deriv > 0:
        cols = np.hstack(['County', 'Month', coeff_cols[:deg + 1], [letter + "'" for letter in coeff_cols[:deg]]])
    else:
        cols = np.hstack(['County', 'Month', coeff_cols[:deg + 1]])

    # Always init
    avg_data_rows = []
    max_data_rows = []
    min_data_rows = []
    precip_data_rows = []
    missed_counties = []

    for month in months:
        for state in states:
            if state != 'OR':
                continue
            print(f"Storing sub-dataframe for state: {state}")

            # Get county codes, names, state, country etc..
            county_codes_df = get_county_codes_as_df()

            # Get df that matches current state
            state_df = county_codes_df[(county_codes_df['state'] == state)]
            state_df.reset_index()  # make sure indices pair with number of rows

            for index, row in state_df.iterrows():
                if row['county_name'] != 'Clackamas':
                    continue
                print(f"Building and storing coefficients for county: {row['county_name']}")
                [avg_df, max_df, min_df, precip_df] = get_data_dfs(row)

                # TODO not best conditional, but check if there was no weather data based on county passed in
                if avg_df.empty is True and max_df.empty is True and min_df.empty is True and precip_df.empty is True:
                    logging.warning(
                        f'Unable to get weather data for county: {row["county_name"]} state: {row["state"]}')
                    missed_counties.append([row['state'], row['county_name'], row['county_code']])
                    continue

                # Process data
                [x_avg, y_avg, x_avg_dates] = get_xy_data_for_months(avg_df, months_dict[month])
                [x_max, y_max, x_max_dates] = get_xy_data_for_months(max_df, months_dict[month])
                [x_min, y_min, x_min_dates] = get_xy_data_for_months(min_df, months_dict[month])
                [x_precip, y_precip, x_precip_dates] = get_xy_data_for_months(precip_df, months_dict[month])

                # Get polynomial coefficents
                avg_coeffs = poly.polyfit(x_avg, y_avg, deg)
                max_coeffs = poly.polyfit(x_max, y_max, deg)
                min_coeffs = poly.polyfit(x_min, y_min, deg)
                precip_coeffs = poly.polyfit(x_precip, y_precip, deg)

                # Dynamically add coefficients (any size)
                if deriv > 0:
                    assert cols.size > deg + 3
                    avg_deriv = np.polyder(avg_coeffs[::-1], deriv)
                    max_deriv = np.polyder(max_coeffs[::-1], deriv)
                    min_deriv = np.polyder(min_coeffs[::-1], deriv)
                    precip_deriv = np.polyder(precip_coeffs[::-1], deriv)

                    avg_data_rows.append(
                        np.hstack([row['county_name'], month, avg_coeffs[::-1], avg_deriv]))
                    max_data_rows.append(
                        np.hstack([row['county_name'], month, max_coeffs[::-1], max_deriv]))
                    min_data_rows.append(
                        np.hstack([row['county_name'], month, min_coeffs[::-1], min_deriv]))
                    precip_data_rows.append(
                        np.hstack([row['county_name'], month, precip_coeffs[::-1], precip_deriv]))
                else:
                    avg_data_rows.append(np.hstack([row['county_name'], month, avg_coeffs[::-1]]))
                    max_data_rows.append(np.hstack([row['county_name'], month, max_coeffs[::-1]]))
                    min_data_rows.append(np.hstack([row['county_name'], month, min_coeffs[::-1]]))
                    precip_data_rows.append(np.hstack([row['county_name'], month, precip_coeffs[::-1]]))

        # After data has been looped and appended to, create new dfs to write to csv
    avg_poly_df = pd.DataFrame(avg_data_rows, columns=cols)
    max_poly_df = pd.DataFrame(max_data_rows, columns=cols)
    min_poly_df = pd.DataFrame(min_data_rows, columns=cols)
    precip_poly_df = pd.DataFrame(precip_data_rows, columns=cols)

    # Write to csv
    avg_poly_df.to_csv(f"avg_county_coeffs_3.csv", sep=',', encoding='utf-8', index=False)
    max_poly_df.to_csv(f"max_poly_coeffs_3.csv", sep=',', encoding='utf-8', index=False)
    min_poly_df.to_csv(f"min_poly_coeffs_3.csv", sep=',', encoding='utf-8', index=False)
    precip_poly_df.to_csv(f"precip_poly_coeffs_3.csv", sep=',', encoding='utf-8', index=False)
    print(f'Successfully wrote polynomial coeffs to csv!')


def build_all_coefficients(deg):
    start_year = 1895
    end_year = 2021
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Generate columns with year and label from start_year to end_year
    avg_cols_name = []
    max_cols_name = []
    min_cols_name = []
    precip_cols_name = []
    for i in range(start_year, end_year+1):
        avg_cols_name.append(f"Avg Temp {str(i)}")
        max_cols_name.append(f"Max Temp {str(i)}")
        min_cols_name.append(f"Min Temp {str(i)}")
        precip_cols_name.append(f"Precip Temp {str(i)}")

    # Generate columns with coefficient (a,b,...) and label from start_year to end_year
    avg_cols_coeffs_name = []
    max_cols_coeffs_name = []
    min_cols_coeffs_name = []
    precip_cols_coeffs_name = []
    for i in coeff_cols[:deg+1]:
        avg_cols_coeffs_name.append(f"Avg Temp {i.upper()}")
        max_cols_coeffs_name.append(f"Max Temp {i.upper()}")
        min_cols_coeffs_name.append(f"Min Temp {i.upper()}")
        precip_cols_coeffs_name.append(f"Precip Temp {i.upper()}")

    # Returning Df column names
    cols = np.hstack(['Counter', 'State', 'County', 'County Code', 'Month', avg_cols_name, min_cols_name, max_cols_name, precip_cols_name, avg_cols_coeffs_name, min_cols_coeffs_name, max_cols_coeffs_name, precip_cols_coeffs_name])

    # Row and counter row value
    missed_counties = []
    data_rows = []
    counter = 0

    # Loop through states
    for state in states:
        print(f"Storing sub-dataframe for state: {state}")

        # Get county codes, names, state, country etc..
        county_codes_df = get_county_codes_as_df()

        # Get df that matches current state
        state_df = county_codes_df[(county_codes_df['state'] == state)]
        state_df.reset_index()  # make sure indices pair with number of rows

        # Iterate rows within state dataframe
        for index, row in state_df.iterrows():
            for month in months:
                # Arrays for storing column data in row format
                avg_data_values = []
                max_data_values = []
                min_data_values = []
                precip_data_values = []

                # For counter column
                counter += 1

                print(f"Building and storing coefficients for county: {row['county_name']}")
                [avg_df, max_df, min_df, precip_df] = get_data_dfs(row)

                # Check for missing counties
                if avg_df.empty is True and max_df.empty is True and min_df.empty is True and precip_df.empty is True:
                    logging.warning(
                        f'Unable to get weather data for county: {row["county_name"]} state: {row["state"]}')
                    missed_counties.append([row['state'], row['county_name'], row['county_code']])
                    continue

                # Build row of temperature data
                # Using avg_cols_name. Any of them should work tho
                index = 0
                for yearStr in avg_cols_name:
                    year = yearStr[len(yearStr) - 4:]
                    id_year = avg_df.at[index, 'id']
                    if year in id_year:
                        avg_data_values.append(avg_df.iat[index, months_dict[month]])
                        max_data_values.append(max_df.iat[index, months_dict[month]])
                        min_data_values.append(min_df.iat[index, months_dict[month]])
                        precip_data_values.append(precip_df.iat[index, months_dict[month]])
                        index += 1
                    else:
                        avg_data_values.append(np.nan)
                        max_data_values.append(np.nan)
                        min_data_values.append(np.nan)
                        precip_data_values.append(np.nan)

                # Process data
                [x_avg, y_avg, x_avg_dates] = get_xy_data_for_months(avg_df, months_dict[month])
                [x_max, y_max, x_max_dates] = get_xy_data_for_months(max_df, months_dict[month])
                [x_min, y_min, x_min_dates] = get_xy_data_for_months(min_df, months_dict[month])
                [x_precip, y_precip, x_precip_dates] = get_xy_data_for_months(precip_df, months_dict[month])

                # Get polynomial coefficents
                avg_coeffs = poly.polyfit(x_avg, y_avg, deg)
                max_coeffs = poly.polyfit(x_max, y_max, deg)
                min_coeffs = poly.polyfit(x_min, y_min, deg)
                precip_coeffs = poly.polyfit(x_precip, y_precip, deg)

                # Append all data to single row
                data_rows.append(np.hstack([str(counter), row['state'], row['county_name'], row['county_code'], month,
                                            avg_data_values, min_data_values, max_data_values, precip_data_values,
                                            avg_coeffs, min_coeffs, max_coeffs, precip_coeffs]))

    # Create dataframe after loop terminates
    data_poly_df = pd.DataFrame(data_rows, columns=cols)
    data_poly_df.to_csv(f"US_poly_3_reversed.csv", sep=',', encoding='utf-8', index=False)
    print(f'Successfully wrote polynomial coeffs to csv!')


    # Write all counties missed
    if not os.path.exists('missed_counties.txt'):
        print(f'Writing missed counties to text file!')
        with open(f'missed_counties.txt', 'w') as text_file:
            for line in missed_counties:
                text_file.write(
                    'state: ' + str(line[0]) + ', county: ' + str(line[1]) + ', county_code: ' + str(line[2]) + '\n')
        print(f'Successfully wrote missed counties to text file!')


def build_all_coefficients_with_deriv(deg, deriv=0):
    start_year = 1895
    end_year = 2021
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Generate columns with year and label from start_year to end_year
    avg_cols_name = []
    max_cols_name = []
    min_cols_name = []
    precip_cols_name = []
    for i in range(start_year, end_year+1):
        avg_cols_name.append(f"Avg Temp {str(i)}")
        max_cols_name.append(f"Max Temp {str(i)}")
        min_cols_name.append(f"Min Temp {str(i)}")
        precip_cols_name.append(f"Precip Temp {str(i)}")

    # Generate columns with coefficient (a,b,...) and label from start_year to end_year
    avg_cols_coeffs_name = []
    max_cols_coeffs_name = []
    min_cols_coeffs_name = []
    precip_cols_coeffs_name = []
    for i in coeff_cols[:deg+1]:
        avg_cols_coeffs_name.append(f"Avg Temp {i.upper()}")
        max_cols_coeffs_name.append(f"Max Temp {i.upper()}")
        min_cols_coeffs_name.append(f"Min Temp {i.upper()}")
        precip_cols_coeffs_name.append(f"Precip Temp {i.upper()}")

    # Returning Df column names
    if deriv > 0:
        cols = np.hstack(
            ['Counter', 'State', 'County', 'County Code', 'Month', avg_cols_name, min_cols_name, max_cols_name,
             precip_cols_name, avg_cols_coeffs_name, [string + "'" for string in avg_cols_coeffs_name[:deg]],
             min_cols_coeffs_name, [letter + "'" for letter in min_cols_coeffs_name[:deg]], max_cols_coeffs_name,
             [letter + "'" for letter in max_cols_coeffs_name[:deg]], precip_cols_coeffs_name,
             [letter + "'" for letter in precip_cols_coeffs_name[:deg]]])
    else:
        cols = np.hstack(
            ['Counter', 'State', 'County', 'County Code', 'Month', avg_cols_name, min_cols_name, max_cols_name,
             precip_cols_name, avg_cols_coeffs_name, min_cols_coeffs_name, max_cols_coeffs_name,
             precip_cols_coeffs_name])

    # Row and counter row value
    missed_counties = []
    data_rows = []
    counter = 0

    # Loop through states
    for state in states:
        print(f"Storing sub-dataframe for state: {state}")

        # Get county codes, names, state, country etc..
        county_codes_df = get_county_codes_as_df()

        # Get df that matches current state
        state_df = county_codes_df[(county_codes_df['state'] == state)]
        state_df.reset_index()  # make sure indices pair with number of rows

        # Iterate rows within state dataframe
        for index, row in state_df.iterrows():
            for month in months:
                # Arrays for storing column data in row format
                avg_data_values = []
                max_data_values = []
                min_data_values = []
                precip_data_values = []

                # For counter column
                counter += 1

                print(f"Building and storing coefficients for county: {row['county_name']}")
                [avg_df, max_df, min_df, precip_df] = get_data_dfs(row)

                # Check for missing counties
                if avg_df.empty is True and max_df.empty is True and min_df.empty is True and precip_df.empty is True:
                    logging.warning(
                        f'Unable to get weather data for county: {row["county_name"]} state: {row["state"]}')
                    missed_counties.append([row['state'], row['county_name'], row['county_code']])
                    continue

                # Build row of temperature data
                # Using avg_cols_name. Any of them should work tho
                index = 0
                for yearStr in avg_cols_name:
                    year = yearStr[len(yearStr) - 4:]
                    id_year = avg_df.at[index, 'id']
                    if year in id_year:
                        avg_data_values.append(avg_df.iat[index, months_dict[month]])
                        max_data_values.append(max_df.iat[index, months_dict[month]])
                        min_data_values.append(min_df.iat[index, months_dict[month]])
                        precip_data_values.append(precip_df.iat[index, months_dict[month]])
                        index += 1
                    else:
                        avg_data_values.append(np.nan)
                        max_data_values.append(np.nan)
                        min_data_values.append(np.nan)
                        precip_data_values.append(np.nan)

                # Process data
                [x_avg, y_avg, x_avg_dates] = get_xy_data_for_months(avg_df, months_dict[month])
                [x_max, y_max, x_max_dates] = get_xy_data_for_months(max_df, months_dict[month])
                [x_min, y_min, x_min_dates] = get_xy_data_for_months(min_df, months_dict[month])
                [x_precip, y_precip, x_precip_dates] = get_xy_data_for_months(precip_df, months_dict[month])

                # Get polynomial coefficents
                avg_coeffs = poly.polyfit(x_avg, y_avg, deg)
                max_coeffs = poly.polyfit(x_max, y_max, deg)
                min_coeffs = poly.polyfit(x_min, y_min, deg)
                precip_coeffs = poly.polyfit(x_precip, y_precip, deg)

                if deriv > 0:
                    avg_deriv = np.polyder(avg_coeffs[::-1], deriv)
                    max_deriv = np.polyder(max_coeffs[::-1], deriv)
                    min_deriv = np.polyder(min_coeffs[::-1], deriv)
                    precip_deriv = np.polyder(precip_coeffs[::-1], deriv)
                    data_rows.append(np.hstack([str(counter), row['state'], row['county_name'], row['county_code'], month,
                                                avg_data_values, min_data_values, max_data_values, precip_data_values,
                                                avg_coeffs[::-1], avg_deriv, min_coeffs[::-1], min_deriv, max_coeffs[::-1],
                                                max_deriv, precip_coeffs[::-1], precip_deriv]))
                else:
                    data_rows.append(
                        np.hstack([str(counter), row['state'], row['county_name'], row['county_code'], month,
                                   avg_data_values, min_data_values, max_data_values, precip_data_values,
                                   avg_coeffs, min_coeffs, max_coeffs, precip_coeffs]))

    # Create dataframe after loop terminates
    data_poly_df = pd.DataFrame(data_rows, columns=cols)
    data_poly_df.to_csv(f"US_poly_3_reversed.csv", sep=',', encoding='utf-8', index=False)
    print(f'Successfully wrote polynomial coeffs to csv!')


# fig = plotting.plot(plot_type, df_list, {'process_type': 'months', 'begin_month': monthsIdx[begin_month],
#                                          'degree': polynomial_degree, 'deriv_degree': derivitive_degree,
#                                          'plots_per_graph': len(df_list), 'counties': counties})
def kelvin_eq(temp):
    return (((5 * (float(temp) - 32)) / 9) + 273)


def build_all_coefficients_kelvin(deg):
    start_year = 1895
    end_year = 2021
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Don't use these column name. Rather, hold the year value for appending temperature data
    temp_avg_cols_name = []
    temp_max_cols_name = []
    temp_min_cols_name = []
    temp_precip_cols_name = []

    # Generate columns with year and label from start_year to end_year
    avg_cols_name = []
    max_cols_name = []
    min_cols_name = []
    precip_cols_name = []
    for i in range(start_year, end_year+1):
        # Store actual year
        temp_avg_cols_name.append(f"Avg Temp {str(i)}")
        temp_max_cols_name.append(f"Max Temp {str(i)}")
        temp_min_cols_name.append(f"Min Temp {str(i)}")
        temp_precip_cols_name.append(f"Precip Temp {str(i)}")

        # Store calculated year
        avg_cols_name.append(f"Avg Temp {str(i/1950)}")
        max_cols_name.append(f"Max Temp {str(i/1950)}")
        min_cols_name.append(f"Min Temp {str(i/1950)}")
        precip_cols_name.append(f"Precip Temp {str(i/1950)}")

    # Generate columns with coefficient (a,b,...) and label from start_year to end_year
    avg_cols_coeffs_name = []
    max_cols_coeffs_name = []
    min_cols_coeffs_name = []
    precip_cols_coeffs_name = []
    for i in coeff_cols[:deg+1]:
        avg_cols_coeffs_name.append(f"Avg Temp {i.upper()}")
        max_cols_coeffs_name.append(f"Max Temp {i.upper()}")
        min_cols_coeffs_name.append(f"Min Temp {i.upper()}")
        precip_cols_coeffs_name.append(f"Precip Temp {i.upper()}")

    # Returning Df column names
    cols = np.hstack(['Counter', 'State', 'County', 'County Code', 'Month', avg_cols_name, min_cols_name, max_cols_name, precip_cols_name, avg_cols_coeffs_name, min_cols_coeffs_name, max_cols_coeffs_name, precip_cols_coeffs_name])

    # Row and counter row value
    missed_counties = []
    data_rows = []
    counter = 0

    # Loop through states
    for state in states:
        print(f"Storing sub-dataframe for state: {state}")

        # Get county codes, names, state, country etc..
        county_codes_df = get_county_codes_as_df()

        # Get df that matches current state
        state_df = county_codes_df[(county_codes_df['state'] == state)]
        state_df.reset_index()  # make sure indices pair with number of rows

        # Iterate rows within state dataframe
        for index, row in state_df.iterrows():
            for month in months:
                # Arrays for storing column data in row format
                avg_data_values = []
                max_data_values = []
                min_data_values = []
                precip_data_values = []

                # For counter column
                counter += 1

                print(f"Building and storing coefficients for county: {row['county_name']}")
                [avg_df, max_df, min_df, precip_df] = get_data_dfs(row)

                # Check for missing counties
                if avg_df.empty is True and max_df.empty is True and min_df.empty is True and precip_df.empty is True:
                    logging.warning(
                        f'Unable to get weather data for county: {row["county_name"]} state: {row["state"]}')
                    missed_counties.append([row['state'], row['county_name'], row['county_code']])
                    continue

                # Perform lamda on all cells to format data
                temp_col = avg_df.pop('id')
                avg_df = avg_df.applymap(kelvin_eq)
                avg_df.insert(0, 'id', temp_col)
                temp_col = max_df.pop('id')
                max_df = max_df.applymap(kelvin_eq)
                max_df.insert(0, 'id', temp_col)
                temp_col = min_df.pop('id')
                min_df = min_df.applymap(kelvin_eq)
                min_df.insert(0, 'id', temp_col)
                temp_col = precip_df.pop('id')
                precip_df = precip_df.applymap(kelvin_eq)
                precip_df.insert(0, 'id', temp_col)

                # Build row of temperature data
                # Using avg_cols_name. Any of them should work tho
                index = 0
                # for yearStr in avg_cols_name:
                for yearStr in temp_avg_cols_name:
                    year = yearStr[len(yearStr) - 4:]
                    id_year = avg_df.at[index, 'id']
                    if year in id_year:
                        avg_data_values.append(avg_df.iat[index, months_dict[month]])
                        max_data_values.append(max_df.iat[index, months_dict[month]])
                        min_data_values.append(min_df.iat[index, months_dict[month]])
                        precip_data_values.append(precip_df.iat[index, months_dict[month]])
                        index += 1
                    else:
                        avg_data_values.append(np.nan)
                        max_data_values.append(np.nan)
                        min_data_values.append(np.nan)
                        precip_data_values.append(np.nan)

                # Process data
                [x_avg, y_avg, x_avg_dates] = get_xy_data_for_months(avg_df, months_dict[month])
                [x_max, y_max, x_max_dates] = get_xy_data_for_months(max_df, months_dict[month])
                [x_min, y_min, x_min_dates] = get_xy_data_for_months(min_df, months_dict[month])
                [x_precip, y_precip, x_precip_dates] = get_xy_data_for_months(precip_df, months_dict[month])

                # Get polynomial coefficents
                avg_coeffs = poly.polyfit(x_avg, y_avg, deg)
                max_coeffs = poly.polyfit(x_max, y_max, deg)
                min_coeffs = poly.polyfit(x_min, y_min, deg)
                precip_coeffs = poly.polyfit(x_precip, y_precip, deg)

                # Append all data to single row
                data_rows.append(np.hstack([str(counter), row['state'], row['county_name'], row['county_code'], month,
                                            avg_data_values, min_data_values, max_data_values, precip_data_values,
                                            avg_coeffs, min_coeffs, max_coeffs, precip_coeffs]))

    # Create dataframe after loop terminates
    data_poly_df = pd.DataFrame(data_rows, columns=cols)
    data_poly_df.to_csv(f"US_poly_3_kelvin.csv", sep=',', encoding='utf-8', index=False)
    print(f'Successfully wrote polynomial coeffs to csv!')


    # Write all counties missed
    if not os.path.exists('missed_counties.txt'):
        print(f'Writing missed counties to text file!')
        with open(f'missed_counties.txt', 'w') as text_file:
            for line in missed_counties:
                text_file.write(
                    'state: ' + str(line[0]) + ', county: ' + str(line[1]) + ', county_code: ' + str(line[2]) + '\n')
        print(f'Successfully wrote missed counties to text file!')

# TODO still work in progress
def build_all_coefficients_with_sd_se(deg, deriv=0):
    start_year = 1895
    end_year = 2021
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Generate columns with year and label from start_year to end_year
    avg_cols_name = []
    max_cols_name = []
    min_cols_name = []
    precip_cols_name = []
    for i in range(start_year, end_year+1):
        avg_cols_name.append(f"Avg Temp {str(i)}")
        max_cols_name.append(f"Max Temp {str(i)}")
        min_cols_name.append(f"Min Temp {str(i)}")
        precip_cols_name.append(f"Precip Temp {str(i)}")

    # Generate columns with coefficient (a,b,...) and label from start_year to end_year
    avg_cols_coeffs_name = []
    max_cols_coeffs_name = []
    min_cols_coeffs_name = []
    precip_cols_coeffs_name = []
    for i in coeff_cols[:deg+1]:
        avg_cols_coeffs_name.append(f"Avg Temp {i.upper()}")
        max_cols_coeffs_name.append(f"Max Temp {i.upper()}")
        min_cols_coeffs_name.append(f"Min Temp {i.upper()}")
        precip_cols_coeffs_name.append(f"Precip Temp {i.upper()}")

    # Returning Df column names
    if deriv > 0:
        cols = np.hstack(
            ['Counter', 'State', 'County', 'County Code', 'Month', avg_cols_name, min_cols_name, max_cols_name,
             precip_cols_name, avg_cols_coeffs_name, [string + "'" for string in avg_cols_coeffs_name[:deg]],
             min_cols_coeffs_name, [letter + "'" for letter in min_cols_coeffs_name[:deg]], max_cols_coeffs_name,
             [letter + "'" for letter in max_cols_coeffs_name[:deg]], precip_cols_coeffs_name,
             [letter + "'" for letter in precip_cols_coeffs_name[:deg]]])
    else:
        cols = np.hstack(
            ['Counter', 'State', 'County', 'County Code', 'Month', avg_cols_name, min_cols_name, max_cols_name,
             precip_cols_name, avg_cols_coeffs_name, min_cols_coeffs_name, max_cols_coeffs_name,
             precip_cols_coeffs_name])

    # Row and counter row value
    missed_counties = []
    data_rows = []
    counter = 0

    # Loop through states
    for state in states:
        print(f"Storing sub-dataframe for state: {state}")

        # Get county codes, names, state, country etc..
        county_codes_df = get_county_codes_as_df()

        # Get df that matches current state
        state_df = county_codes_df[(county_codes_df['state'] == state)]
        state_df.reset_index()  # make sure indices pair with number of rows

        # Iterate rows within state dataframe
        for index, row in state_df.iterrows():
            for month in months:
                # Arrays for storing column data in row format
                avg_data_values = []
                max_data_values = []
                min_data_values = []
                precip_data_values = []

                # For counter column
                counter += 1

                print(f"Building and storing coefficients for county: {row['county_name']}")
                [avg_df, max_df, min_df, precip_df] = get_data_dfs(row)

                # Check for missing counties
                if avg_df.empty is True and max_df.empty is True and min_df.empty is True and precip_df.empty is True:
                    logging.warning(
                        f'Unable to get weather data for county: {row["county_name"]} state: {row["state"]}')
                    missed_counties.append([row['state'], row['county_name'], row['county_code']])
                    continue

                # Build row of temperature data
                # Using avg_cols_name. Any of them should work tho
                index = 0
                for yearStr in avg_cols_name:
                    year = yearStr[len(yearStr) - 4:]
                    id_year = avg_df.at[index, 'id']
                    if year in id_year:
                        avg_data_values.append(avg_df.iat[index, months_dict[month]])
                        max_data_values.append(max_df.iat[index, months_dict[month]])
                        min_data_values.append(min_df.iat[index, months_dict[month]])
                        precip_data_values.append(precip_df.iat[index, months_dict[month]])
                        index += 1
                    else:
                        avg_data_values.append(np.nan)
                        max_data_values.append(np.nan)
                        min_data_values.append(np.nan)
                        precip_data_values.append(np.nan)

                # Process data
                [x_avg, y_avg, x_avg_dates] = get_xy_data_for_months(avg_df, months_dict[month])
                [x_max, y_max, x_max_dates] = get_xy_data_for_months(max_df, months_dict[month])
                [x_min, y_min, x_min_dates] = get_xy_data_for_months(min_df, months_dict[month])
                [x_precip, y_precip, x_precip_dates] = get_xy_data_for_months(precip_df, months_dict[month])

                # Get polynomial coefficents
                avg_coeffs = poly.polyfit(x_avg, y_avg, deg)
                max_coeffs = poly.polyfit(x_max, y_max, deg)
                min_coeffs = poly.polyfit(x_min, y_min, deg)
                precip_coeffs = poly.polyfit(x_precip, y_precip, deg)

                if deriv > 0:
                    avg_deriv = np.polyder(avg_coeffs[::-1], deriv)
                    max_deriv = np.polyder(max_coeffs[::-1], deriv)
                    min_deriv = np.polyder(min_coeffs[::-1], deriv)
                    precip_deriv = np.polyder(precip_coeffs[::-1], deriv)
                    data_rows.append(np.hstack([str(counter), row['state'], row['county_name'], row['county_code'], month,
                                                avg_data_values, min_data_values, max_data_values, precip_data_values,
                                                avg_coeffs[::-1], avg_deriv, min_coeffs[::-1], min_deriv, max_coeffs[::-1],
                                                max_deriv, precip_coeffs[::-1], precip_deriv]))
                else:
                    data_rows.append(
                        np.hstack([str(counter), row['state'], row['county_name'], row['county_code'], month,
                                   avg_data_values, min_data_values, max_data_values, precip_data_values,
                                   avg_coeffs, min_coeffs, max_coeffs, precip_coeffs]))

    # Create dataframe after loop terminates
    data_poly_df = pd.DataFrame(data_rows, columns=cols)
    data_poly_df.to_csv(f"US_poly_3_reversed.csv", sep=',', encoding='utf-8', index=False)
    print(f'Successfully wrote polynomial coeffs to csv!')

if __name__ == '__main__':
    #build_all_coefficients_kelvin(3)
    # x = [1895, 1896, 1897, 1898, 1899, 1900, 1901, 1902, 1903, 1904, 1905]
    # y_real = [31.9, 36.1, 33.2, 33.3, 35.3, 37.6, 33.8, 33.0, 36.3, 36.3, 34.2]
    # y_calc = [34.3, 34.3, 34.2, 34.1, 34.0, 33.9, 33.9, 33.8, 33.7, 33.7, 33.6]
    # fit = np.polyfit(x, y_real, deg=1)
    # n = len(x)
    # m = fit[0]
    # c = fit[1]
    # y_pred = m*x+c
    # STEYX = (((y-y_pred)**2).sum()/(n-2))**0.5
    # print(STEYX)
    '''Stand error (Predictive, not working though)'''
    # X = sm.add_constant(x)
    # model = sm.OLS(y_calc, X)
    # fit = model.fit()
    # print(np.sqrt(fit.mse_resid))
    '''Standard error (non predicitive)'''
    # model = sm.OLS(y_calc, x)
    # results = model.fit()
    # print(results.scale**.5)

    # build_all_coefficients_with_deriv(3, 1)
    build_all_coefficients(3)
    # build_coeffs_by_month_single_file(3)
    pass
    # Ex) build_poly_coeffs_for_county_csv(degree, derivative order (optional))
    # build_poly_coeffs_for_county_csv(3, 1)
    # build_poly_coeffs_for_county_by_months_csv(3, 1)
