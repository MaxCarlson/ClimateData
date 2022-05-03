import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)
import matplotlib.dates as mdates
import numpy.polynomial.polynomial as poly
import pandas as pd
import mplcursors
from string import ascii_lowercase
from tkinter import *
from matplotlib.pyplot import cm
import math
import datetime as dt

matplotlib.use("TkAgg", force= False)
'''
TODO
functions to implement
- Plot per county data
- Plot per state data
- Plot per country data (Eventually)

'''
csv_path = './data/raw/climdiv-avgtmp.csv'
headers = ['Codes', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def to_date(x_data):
    x_data_formatted = []
    decimal_map = {'0': 1, '083': 2, '166': 3, '25': 4, '333': 5, '416': 6, '5': 7, '583': 8, '666': 9, '75': 10, '833': 11, '916': 12}
    for i in x_data:
        remainder, year = math.modf(i)
        if len(str(remainder)[2:]) <= 2:
            month = decimal_map[str(remainder)[2:]]
            x_data_formatted.append(dt.datetime(year=int(year), month=month, day=1))
        else:
            month = decimal_map[str(remainder)[2:5]]
            x_data_formatted.append(dt.datetime(year=int(year), month=month, day=1))

    return mdates.num2date(x_data_formatted)


def plot(ptype, df_list, plot_vars_map):

    x_data_list, y_data_list, plot_vars_map = process_data(plot_vars_map, plot_vars_map['process_type'], df_list)

    if ptype == 'scatter':
        pass
    elif ptype == 'poly':
        pass
    elif ptype == 'poly_deriv':
        return plot_poly_deriv(x_data_list, y_data_list, plot_vars_map['degree'], plot_vars_map['deriv_degree'], 
                               plot_vars_map['plots_per_graph'], plot_vars_map['names'])
    elif ptype == 'scatter_poly':
        return scatter_poly(x_data_list, y_data_list, plot_vars_map['degree'], 
                            plot_vars_map['plots_per_graph'], plot_vars_map['names'],
                            plot_vars_map['plot_points'])
    elif ptype == 'connected':
        return connected_scatter(x_data_list, y_data_list, plot_vars_map['degree'], plot_vars_map['plots_per_graph'], 
                                 plot_vars_map['names'], plot_vars_map['plot_points'], plot_vars_map['connected_curve'])
    else:
        print('Invalid plot type!')

def process_data(plot_vars_map, process_type, df_list):
    x_data_list = []
    y_data_list = []

    def pd_normal(df, beginMonth):
        x_data = []
        y_data = []

        for i in df.iloc[:,0]:
            for j in range(df.shape[1]-1):
                x_data.append(int(str(i)[-4:]) + (j + beginMonth) / 12)

        for i, row in df.iterrows():
            for j in row[1:]:
                y_data.append(j)

        return x_data, y_data

    def pd_monthly(df, beginMonth, endMonth):
        x_data = [[] for x in range(endMonth + 1 - beginMonth)]
        y_data = [[] for x in range(endMonth + 1 - beginMonth)]

        for i in df.iloc[:,0]:
            for j in range(df.shape[1]-1):
                x_data[j].append(float(str(i)[-4:]))
        for i, row in df.iterrows():
            for m, j in enumerate(row[1:]):
                y_data[m].append(j)
        return x_data, y_data

    year_size = df_list[0].shape[1] - 1
    if process_type == 'normal':
        for df in df_list:
            x_data, y_data = pd_normal(df, plot_vars_map['begin_month'])
            x_data_list.append(x_data)
            y_data_list.append(y_data)
    elif process_type == 'monthly':
        year_size = 1
        # Convert counties to months, since that's what we're plotting
        counties = plot_vars_map['names']
        newNames = []
        for i in range(len(counties)):
            for j in range(plot_vars_map['begin_month'], plot_vars_map['end_month']+1):
                name = headers[1:][j]
                if len(counties) > 1:
                    name = counties[i] + '-' + name
                newNames.append(name)
        plot_vars_map['names'] = newNames

        for df in df_list:
            x_data, y_data = pd_monthly(df, plot_vars_map['begin_month'], plot_vars_map['end_month'])
            x_data_list += x_data
            y_data_list += y_data


    # Duplicate all values but slice off 
    # diff number of years from duplicats
    if plot_vars_map['double_plot_diff'] != None:
        new_x_vals = []
        new_y_vals = []
        diff = plot_vars_map['double_plot_diff']
        vals_to_cut = diff * year_size

        for xarr, yarr in zip(x_data_list, y_data_list):
            new_x = xarr[:-vals_to_cut]
            new_y = yarr[:-vals_to_cut]
            new_x_vals.append(new_x)
            new_y_vals.append(new_y)

        x_data_list += new_x_vals
        y_data_list += new_y_vals

        # Add new names for these lines
        names = plot_vars_map['names']
        newNames = []
        for n in names:
            newNames.append(n + '_diff')
        plot_vars_map['names'] = names + newNames

    return x_data_list, y_data_list, plot_vars_map

def connected_scatter(x, y, deg, plots_per_graph, names, plot_points, connected_curve):
    fig, ax1 = plt.subplots()

    colors = cm.rainbow(np.linspace(0, 1, len(names)))
    for x, y, county, color in zip(x, y, names, colors):
        x_fit = np.array(x)
        if connected_curve:
            coeffs = poly.polyfit(x, y, deg)
            def fiteq(x, idx=0):
                if idx == deg:
                    return coeffs[idx] * x ** (idx)
                else:
                    return coeffs[idx] * x ** (idx) + fiteq(x, idx+1)
            lines = ax1.plot(x_fit, fiteq(x_fit), color=color, linestyle='-', alpha=0.5)
        

        lines = ax1.plot(x_fit, y, color=color, linestyle='-', alpha=0.5, label=county)
        if plot_points:
            ax1.scatter(x, y, s=4, color=color)

    ax1.set_title(f'Connected Plot')
    ax1.legend()
    cursor = mplcursors.cursor()
    return fig, x, y

def scatter_poly(x, y, deg, plots_per_graph, counties, plot_points):
    # Example of what coeffs and fiteq do, for a 3rd degree polynomial
    #d, c, b, a = poly.polyfit(x, y, 3)
    #fiteq = lambda x: a * x ** 3 + b * x ** 2 + c * x + d
    fig, ax1 = plt.subplots()

    colors = cm.rainbow(np.linspace(0, 1, len(counties)))
    for x, y, county, color in zip(x, y, counties, colors):
        coeffs = poly.polyfit(x, y, deg)
        def fiteq(x, idx=0):
            if idx == deg:
                return coeffs[idx] * x ** (idx)
            else:
                return coeffs[idx] * x ** (idx) + fiteq(x, idx+1)

        x_fit = np.array(x)
        y_fit = fiteq(x_fit)

        lines = ax1.plot(x_fit, y_fit, color=color, alpha=0.5, label=county)
        if plot_points:
            ax1.scatter(x, y, s=4, color=color)

    ax1.set_title(f'Polynomial fit deg={deg}')
    ax1.legend()
    #plt.subplots_adjust(right=0.8)
    #plt.table([['{:.10f}'.format(coeffs[x])[:9]] for x in range(len(coeffs)-1, -1, -1)], 
    #          rowLabels=[ascii_lowercase[x] for x in range(deg+1)], 
    #          colLabels=['Poly Coeffs'], loc='right', colWidths = [0.2])
    #plt.text(15, 3.4, 'Coefficients', size=12)
    cursor = mplcursors.cursor()
    #plt.show()
    return fig, x, y

def plot_poly_deriv(x, y, deg, deriv_deg, plots_per_graph, counties):
    
    new_x = []
    new_y = []
    fig, ax1 = plt.subplots()
    colors = cm.rainbow(np.linspace(0, 1, len(counties)))
    for x, y, county, color in zip(x, y, counties, colors):
        coeffs = poly.polyfit(x, y, deg)
        dcoeffs = poly.polyder(coeffs, deriv_deg)
        def fiteq(x, idx=0):
            if idx == deg - deriv_deg:
                return dcoeffs[idx] * x ** (idx)
            else:
                return dcoeffs[idx] * x ** (idx) + fiteq(x, idx+1)

        x_fit = np.array(x)
        y_fit = fiteq(x_fit)
        new_x.append(x_fit)
        new_y.append(y_fit)

        lines = ax1.plot(x_fit, y_fit, color=color, alpha=0.5, label=county)
        #ax1.scatter(x, y, s=4, color=color)
    
    ax1.set_title(f'Derivitive deg={deriv_deg} of polynomial fit deg={deg}')
    ax1.legend()
    cursor = mplcursors.cursor()
    return fig, new_x, new_y

def tkinter_scatter_poly(x, y, deg):
    coeffs = poly.polyfit(x, y, deg)
    def fiteq(x, idx=0):
        if idx == deg:
            return coeffs[idx] * x ** (idx)
        else:
            return coeffs[idx] * x ** (idx) + fiteq(x, idx+1)

    x_fit = np.array(x)
    y_fit = fiteq(x_fit)

    fig, ax1 = plt.subplots()
    lines = ax1.plot(x_fit, y_fit, color='r', alpha=0.5, label='Polynomial fit')
    scatter = ax1.scatter(x, y, s=4, color='b', label='Data points')
    ax1.set_title(f'Polynomial fit example deg={deg}')
    ax1.legend()
    plt.subplots_adjust(right=0.8)
    plt.table([['{:.10f}'.format(coeffs[x])[:9]] for x in range(len(coeffs)-1, -1, -1)],
              rowLabels=[ascii_lowercase[x] for x in range(deg+1)],
              colLabels=['Poly Coeffs'], loc='right', colWidths = [0.2])

    canvas = FigureCanvasTkAgg(fig, master=window) # window is main tkinter window
    canvas.get_tk_widget().pack()

    # creating the Matplotlib toolbar
    toolbar = NavigationToolbar2Tk(canvas,
                                   window)
    toolbar.update()

    # placing the toolbar on the Tkinter window
    canvas.get_tk_widget().pack()


if __name__ == '__main__':

    # TODO: Add plot color preferences to the input map
    #plot('scatter_poly', get_test_data_raw(), {'process_type': 'months', 'range': range(0,12), 'degree': 3})
    plot('poly_deriv', get_test_data_raw(), {'process_type': 'months', 'range': range(0,12), 'degree': 5, 'deriv_degree' : 2})
