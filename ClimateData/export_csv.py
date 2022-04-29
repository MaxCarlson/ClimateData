import numpy.polynomial.polynomial as poly
import logging
import numpy as np
import string
import pandas as pd

# Predefined lists
coeff_cols = list(string.ascii_lowercase)
months_dict = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10,
               'nov': 11, 'dec': 12}

'''
FOR UI.py
Params
- type (avg, precip, max, min)
- eq: poly degree
- deriv=0
- date range
- df - state, county, county code, country
TODO at end make sure to rearrange alphabetically by state
'''

def get_xy_data_for_year(df):
    x_dates_format = []
    x_data = []
    start_year = int(str(df['id'].iloc[0])[7:])
    end_year = int(str(df['id'].iloc[-1])[7:])
    month_cols = [col[-3:] for col in list(df.loc[:, df.columns != 'id'])]

    # range(start_year, end_year) == df.shape[0] (num of rows)
    # Append date formatted
    for i in range(start_year, end_year + 1):
        for month in month_cols:
            x_dates_format.append(str(i)[-4:] + '-' + month)
            x_data.append(int(str(i)[-4:]) + (months_dict.get(month) - 1) / 12)

    # Append temp/precip values
    y_data = []
    for i, row in df.iterrows():
        for j in row[1:len(month_cols) + 1]:
            y_data.append(j)

    return [x_data, y_data, x_dates_format]

def get_xy_data_for_months(df, start_year, end_year, month=12):
    x_dates_format = []
    x_data = []

    # range(start_year, end_year) == df.shape[0] (num of rows)
    # Append date formatted
    for i in range(start_year, end_year + 1):
        x_data.append(int(str(i)[-4:]))

    # Append temp/precip values
    y_data = []
    for i, row in df.iterrows():
        y_data.append(row[month])

    return [x_data, y_data, x_dates_format]

def export_csv_split_months(df_list, state_dict, date_range, data_type, deg, deriv):
    months_indicies = {'jan': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'may': 4, 'jun': 5, 'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9,
                       'nov': 10, 'dec': 11}
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    begin_year = int(date_range.get('begin_year'))
    begin_month_index = months_indicies.get(date_range.get('begin_month'))
    end_year = int(date_range.get('end_year'))
    end_month_index = months_indicies.get(date_range.get('end_month'))
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Build column names just for temp data
    data_cols_names = []
    for month_index in range(begin_year, end_year+1):
        data_cols_names.append(data_type + f" {str(month_index)}")

    # Concatenate all column names
    cols = []
    if deriv > 0:
        cols = np.hstack(['State', 'County', 'Month', data_cols_names, coeff_cols[:deg+1],
                          [letter + "'" for letter in coeff_cols[:deg]]])
    else:
        cols = np.hstack(['State', 'County', 'Month', data_cols_names, coeff_cols[:deg+1]])

    # Append line by line to transpose data
    data_rows = []
    county_index = 0
    for state, counties in state_dict.items():
        for county in counties:
            county_df = df_list[county_index]
            for month_index in range(begin_month_index, end_month_index+1):
                temperature_data_values = []
                month = months[month_index]

                # Appending temp data
                index = 0
                for yearStr in data_cols_names:
                    year = yearStr[len(yearStr) - 4:]
                    id_year = county_df.at[index, 'id']
                    if year in id_year:
                        temperature_data_values.append(county_df.iat[index, months_dict[month]])
                        index += 1
                    else:
                        temperature_data_values.append(np.nan)

                # Process data
                [x, y, x_dates] = get_xy_data_for_months(county_df, begin_year, end_year, month_index + 1)

                # Get polynomial coefficients
                # Format ax^deg + bx^deg-1 + cx^deg-2 + ... + z
                coeffs = poly.polyfit(x, y, deg)

                # Get deriv if exist, get derivative coefficients
                if deriv > 0:
                    deriv_coeffs = np.polyder(coeffs[::-1], deriv)
                    data_rows.append(np.hstack([state, county, month, temperature_data_values, coeffs[::-1], deriv_coeffs]))
                else:
                    data_rows.append(np.hstack([state, county, month, temperature_data_values, coeffs[::-1]]))

            # Iterate each county df from df_list
            county_index += 1

    # Create df
    df = pd.DataFrame(data_rows, columns=cols)
    return df

def export_csv_year(df_list, state_dict, deg, deriv):
    print(f'Degree {deg} Polynomial')

    if deg < 1:
        logging.error('Please enter polynomial degree greater than 0')
        quit(1)

    # Concatenate all column names
    cols = []
    if deriv > 0:
        cols = np.hstack(['State', 'County', coeff_cols[:deg+1], [letter + "'" for letter in coeff_cols[:deg]]])
    else:
        cols = np.hstack(['State', 'County', coeff_cols[:deg+1]])

    # cols = np.hstack(['State', 'County', coeff_cols[:deg + 1]])

    county_index = 0
    county_df_list = []
    for state, counties in state_dict.items():
        for county in counties:
            county_df = df_list[county_index]

            # Get data sorted
            [x, y, x_dates] = get_xy_data_for_year(county_df)

            # Drop Id
            county_df['id'] = county_df['id'].str[7:]

            # Get polynomial coefficients
            # Format ax^deg + bx^deg-1 + cx^deg-2 + ... + z
            coeffs = poly.polyfit(x, y, deg)

            # Check deriv
            coeffs_df = None
            if deriv > 0:
                deriv_coeffs = np.polyder(coeffs[::-1], deriv)
                coeffs_df = pd.DataFrame([np.hstack([state, county, coeffs[::-1], deriv_coeffs])], columns=cols)
            else:
                coeffs_df = pd.DataFrame([np.hstack([state, county, coeffs[::-1]])], columns=cols)

            # Concat
            temp_full_df = pd.concat([coeffs_df, county_df])

            # Get rid of first rows NaNs, then drop new last Nan
            temp_full_df.loc[:,'id':] = temp_full_df.loc[:,'id':].shift(-1)
            temp_full_df.drop(temp_full_df.tail(1).index, inplace=True)

            # Drop id, rename year and put in different place
            year_column = temp_full_df.pop('id')
            temp_full_df.insert(2, 'Year', year_column)
            county_df_list.append(temp_full_df)
            county_index += 1

    df = pd.concat(county_df_list)
    df = df.replace(np.nan, '', regex=True)
    return df

def export_csv(process_type, df_list, state_dict, date_range, data_type, deg, deriv):
    if process_type == 'monthly':
        return export_csv_split_months(df_list, state_dict, date_range, data_type, deg, deriv)
    else: # Only else condition currently
        return export_csv_year(df_list, state_dict, deg, deriv)

if __name__ == '__main__':
    pass