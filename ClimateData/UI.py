#!/usr/bin/env python3
import tkinter as tk
from tkinter import *
from tkinter import HORIZONTAL, LEFT, ttk, Canvas
import ttkbootstrap as tkboot
from ttkbootstrap import ttk as TTK
from ttkbootstrap import font as tkfont
from ttkbootstrap.constants import *
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askopenfilename, askopenfilenames          #Save State Code: used for import
import psycopg2
from database import *
import plotting
import re
from itertools import chain
import matplotlib
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import MapUI
from idlelib.tooltip import Hovertip
from PyQt5.QtWidgets import *                   #pip install PyQt5
from export_csv import export_csv
import numpy as np
import os
from datetime import date
import pickle       #Save State Code: pickle, used for import and export

# lets adjust the maximum size from a convenient spot
x_max = 4096
y_max = 2160

# Dictionaries
degree_dict = {
    "Linear"     : 1,
    "Quadratic"  : 2,
    "Cubic"      : 3
}

datatype_dict = {
    "Maximum temperature" : "tmp_max",
    "Minimum temperature" : "tmp_min",
    "Average temperature" : "tmp_avg",
    "Precipitation"       : "precip",
    "Palmer Drought Severity" : "pdsist",
    "Palmer Hydrological Drought" : "phdist",
    "Modified Palmer Drought Severity" : "pmdist",
    "1-month Standardized Precipitation" : "sp01st",
    "2-month Standardized Precipitation" : "sp02st",
    "3-month Standardized Precipitation" : "sp03st",
    "6-month Standardized Precipitation" : "sp06st",
    "9-month Standardized Precipitation" : "sp09st",
    "12-month Standardized Precipitation" : "sp12st",
    "24-month Standardized Precipitation" : "sp24st"
} 

month_dict = {
    "01" : "jan",
    "02" : "feb",
    "03" : "mar",
    "04" : "apr",
    "05" : "may",
    "06" : "jun",
    "07" : "jul",
    "08" : "aug",
    "09" : "sep",
    "10" : "oct",
    "11" : "nov",
    "12" : "dec"
}

#This dictionary makes months abbreviations look nicer in the UI
month_abbrev_to_whole = {
    "01" : "January",
    "02" : "February",
    "03" : "March",
    "04" : "April",
    "05" : "May",
    "06" : "June",
    "07" : "July",
    "08" : "August",
    "09" : "September",
    "10" : "October",
    "11" : "November",
    "12" : "December"
}

# Array for state only data
state_data_types = np.array(["pdsist", "phdist", "pmdist", "sp01st", "sp02st", "sp03st", "sp06st", "sp09st", "sp12st",
                              "sp24st"])

# Helper Functions --------------------------------------------------

def validate_dates(start, end):
    #check that date is in correct format (month/year)
    if bool(re.match("\d+\/\d{4}", start)) == False or bool(re.match("\d+\/\d{4}", end)) == False:
        print("Dates were not in correct format") 
        return False
   
    begin_year = start.split('/')[1]
    end_year= end.split('/')[1]

    #check that first year occurs before second year
    if bool(begin_year < end_year) == False:
        print("First year was not before last year")
        return False
   
    begin_year = int(begin_year)
    end_year = int(end_year) 

    #Year before 1895
    if bool((begin_year < 1885) or (end_year < 1895)):
        print("Year(s) before 1895")
        return False

    return True


def validate_degree(degree):
   
    #check that the degree is a number 
    if bool(degree.isnumeric()) == False:
        return False

    return True


class App(tk.Tk):


    #Logic for generating a tab
    def gen_tab(self):
        self.tab_counter += 1
        tab = tk.Frame(self.container, width=x_max, height=y_max)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        self.container.add(tab, text=f'Tab {self.tab_counter}')
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        loop = 0 
        data = ["StartPage", "graphPage"]
        for F in (StartPage, graphPage):
            current_frame = F(parent=tab, controller=self, master=tab)
            current_frame.grid_columnconfigure(0, weight=1)
            current_frame.grid_rowconfigure(0, weight=1)
            #self.frame_list.append(current_frame)
            if loop == 0:
                self.frames.append({})
            self.frames[self.tab_counter - 1][data[loop]] = current_frame
            current_frame.grid(row=0, column=0)
            loop += 1

    #Logic for deleting a tab 
    def destroy_tab(self):
        for F in self.container.winfo_children():
            if str(F)==self.container.select():
                F.destroy()
                return


    def __init__(self, *args, **kwargs):
        self.tab_counter = 0
        self.tab_list = []
        self.frames = []

        tk.Tk.__init__(self, *args, **kwargs)
        self.title('Climate Data')
        self.geometry(str(x_max) + 'x' + str(y_max))
        self.state('zoomed')  # start maximized
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        tkboot.Style('darkly')

        self.app = QApplication([])
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.container = ttk.Notebook(self, width=x_max, height=y_max)  # the "notebook" needs to be assigned to fill the window

        self.container.grid(row=0, column=0)
        self.gen_tab()
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)


         #Button for generating a notebook tab
        self.new_tab = tkboot.Button(
           self,
           command=self.gen_tab,
           width="10",
           text="New tab",
           bootstyle=DEFAULT
        )
        self.new_tab.grid(row=0, column=0, padx=(0,150), pady=(0,0), sticky='ne')  # stick to top right corner
        self.new_tabTip = Hovertip(self.new_tab, 'Create a new notebook tab')
        
        #Delete button for a notebook tab
        self.delete_tab = tkboot.Button(
            self,
            command=self.destroy_tab,
            width="10",
            text="Delete tab",
            bootstyle=DEFAULT
        )
        self.delete_tab.grid(row=0, column=0, padx=(0, 50), pady=(0,0), sticky='ne')  # stick to top right corner
        self.delete_tabTip = Hovertip(self.delete_tab, 'Delete the current notebook tab')
        

       

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def open_map(self, df):
        window = MapUI.MapWindow(df)
        self.app.setStyleSheet("QHeaderView::section { background-color: #2F2F2F; color: white }")
        self.app.exec_()

class StartPage(tk.Frame):
    def __init__(self, parent, controller, master):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        button1 = TTK.Button(self, text = "Graph", width="15", bootstyle="secondary", command=lambda: controller.show_frame("graphPage"))
        button2 = TTK.Button(self, text = "Map", width="15", bootstyle="secondary", command=lambda: controller.open_map("TODO:"))
        button1.grid(row=0, column=1, padx=(100,0), pady=(100,500))
        button2.grid(row=0, column=2, padx=(10,0), pady=(100,500))


 
class graphPage(tk.Frame):
    def __init__(self, parent, controller, master):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.begin_year = tkboot.StringVar(value="")
        self.end_year = tkboot.StringVar(value="")
        self.begin_date = tkboot.StringVar(value="")
        self.end_date = tkboot.StringVar(value="")
        self.n_degree = tkboot.StringVar(value="")

        self.export_csv_df = None
        self.export_csv_button = None
        self.button_coeff = None

#Save State Code
        self.save_state_export_df = None
        self.save_state_export_button = None
        self.save_state_import_df = None
        self.save_state_import_button = None
        self.graph = None

#3/6: txt and table import
        self.table_export_df = None
        self.table_export_button = None
        self.table_import_df = None
        self.table_import_button = None
#End of Save State Code

        # Yearly Offset Input Selection
        self.ent3 = None
        self.year_offset = None

        # Degree inputs and labels
        self.ent = None
        self.degree_label = None
        self.ent2 = None
        self.deriv_label = None

        # Y-axis limit inputs
        self.y_lim = None
        self.y_min = None
        """""
        def on_submit():
            #user input is invalid, call validate_dates function
            if validate_dates(self.begin_year.get(), self.end_year.get()) == False:    
                tkboot.dialogs.Messagebox.show_error(f"Invalid date entry. \nEntry rules: \n- Entry must be in form: 'month/year' \n- Years must be in chronological order \n- Years must be four digits \n- Entry example: '06/1993'\n You entered: {self.begin_year.get()} || {self.end_year.get()}", title='Invalid date entry')

            else: 
                #user input is valid, parse it into two months and two years
                print("User entered this begin date: " + self.begin_year.get())
                print("User entered this ending date: " + self.end_year.get())
                print("parsing data into months/ years.....")
                [begin_month, begin_year] = self.begin_year.get().split('/')
                [end_month, end_year] = self.end_year.get().split('/')
                print("Begin month in correct format: " + begin_month)
                print("Begin year in correct format: " + begin_year)
                print("End month in correct format: " + end_month)
                print("End year in correct format: " + end_year)

        def on_submit_degree():
            if validate_degree(self.ent.get()) == False:
                tkboot.dialogs.Messagebox.show_error("Invalid degree entry. \nDegree must be a number.", title='Invalid degree entry')
            else:
                print("Degree is: ")
                print(self.ent.get())

        """

        #The data has been entered/ selected by the user. Here is it:
        def on_enter_data():
            fig_numbers = [x.num
                for x in matplotlib._pylab_helpers.Gcf.get_all_fig_managers()]
            print("FIG NUMBERS BEFORE: " , fig_numbers)

             #user input for dates is invalid, call validate_dates function and don't send data
            if validate_dates(self.begin_year.get(), self.end_year.get()) == False:
                tkboot.dialogs.Messagebox.show_error(f"Invalid date entry. \nEntry rules: \n- Entry must be in form: 'month/year' \n- Years must be in chronological order \n- Years must be four digits \n- Entry example: '06/1993'\n", title='Invalid date entry')
                return 

            [begin_month_num, begin_year] = self.begin_year.get().split('/')
            [end_month_num, end_year] = self.end_year.get().split('/')
            begin_month = month_dict[begin_month_num]
            end_month = month_dict[end_month_num]
            months = []
            for monthNum in range(int(begin_month_num), int(end_month_num)+1):
                month = str(monthNum).zfill(2)
                months.append(month_dict[month])

            drop_down       = self.dropdown_equations.get()
            plot_points     = self.plot_points_var.get()
            hide_legend     = self.plot_hide_legend_var.get()
            monthly_split   = self.monthly_check_var.get()
            y_max           = self.entry_ymax.get()
            y_min           = self.entry_ymin.get()
            plot_dropdown   = self.plot_type.get()
            graph_type      = self.dropdown_graphs.get()

            connected_curve = None
            derivitive_degree = None
            if 'Connected' in drop_down:
                plot_type = 'connected'
                polynomial_degree = None
                connected_curve = 'Curve' in drop_down
            else:
                derivitive_degree = None if self.ent2 == None else int(self.ent2.get())
                plot_type = 'scatter_poly'
                if derivitive_degree != None:
                    plot_type = 'poly_deriv'

            if connected_curve or not ('Connected' in drop_down):
                polynomial_degree = degree_dict[self.dropdown_equations.get()] if self.ent == None else int(self.ent.get())
            double_plot_diff = None if self.ent3 == None else int(self.ent3.get())

            process_type = 'normal'
            if monthly_split:
                process_type = 'monthly'


            data_type =  datatype_dict[self.dropdown_graphs.get()]
            # Intermediate Steps
            rows = self.data_table.get_children()
            states = []
            county_codes = []
            countries = []
            temp_dict = {}
            for line in rows:
                values = self.data_table.item(line)['values']

                if values[0] not in states:
                    states.append(values[0])
                county_codes.append(values[2])
                countries.append(values[3])
            
                print("printing states:")
                print(values[0])
                #make counties list of lists:
                if values[0] in temp_dict:
                    temp_dict[values[0]].append(values[1])
                    print(temp_dict[values[0]])
                else:
                    temp_dict[values[0]] = [values[1]]
                    print(temp_dict[values[0]])
            
            counties = []
            for key in temp_dict.keys():
                counties.append(temp_dict[key])

            monthsIdx = {'jan' : 0, 'feb' : 1, 'mar' : 2, 'apr': 3, 'may': 4, 'jun': 5, 
                         'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11}

            df_list = get_data_for_counties_dataset(states, counties, 'US', [data_type], months, int(begin_year), int(end_year))

            # Special case just for if Alaska is selected with drought data
            def remove_alaska(states_list):
                try:
                    states_list.remove('AK')
                except ValueError:
                    print("ValueError caught: Alaska was not defined in state list.")
                finally:
                    return states_list

            counties = list(chain(*counties))

            print('Testing dataframe:')
            print(temp_dict)

            fig, x_data, y_data = plotting.plot(plot_type, df_list, {'process_type': process_type, 'double_plot_diff': double_plot_diff,
                                                     'plot_points': plot_points, 'connected_curve': connected_curve,
                                                     'begin_month': monthsIdx[begin_month], 'end_month': monthsIdx[end_month],
                                                     'degree': polynomial_degree, 'deriv_degree': derivitive_degree,
                                                     'plots_per_graph' : len(df_list), 'names' : (remove_alaska(states) if data_type in state_data_types else counties),
                                                     'show_legend': not hide_legend, 'y_max': y_max, 'y_min': y_min})

#Save State Code: capture the data needed to be saved into the df on enter data. Instead of saving plot_vars_map, save what is needed to build plot_vars_map
            self.save_state_export_df = pd.DataFrame([{'plot_type':plot_type, 'df_list':df_list, 'process_type': process_type, 'double_plot_diff': double_plot_diff,
                                                     'plot_points': plot_points, 'connected_curve': connected_curve,
                                                     'begin_month': monthsIdx[begin_month], 'end_month': monthsIdx[end_month],
                                                     'degree': polynomial_degree, 'deriv_degree': derivitive_degree,
                                                     'plots_per_graph' : len(df_list), 'names' : (remove_alaska(states) if data_type in state_data_types else counties),
                                                     'show_legend': not hide_legend, 'y_max': y_max, 'y_min': y_min, 'table_list': temp_dict,
                                                      'equation': drop_down, 'monthly_split': monthly_split, 'plot_dropdown': plot_dropdown, 'graph_type': graph_type}],
                                                     columns = ('plot_type', 'df_list',
                                                     'process_type', 'double_plot_diff', 'plot_points', 
                                                     'connected_curve', 'begin_month', 'end_month',
                                                     'degree', 'deriv_degree', 'plots_per_graph', 'names',
                                                     'show_legend', 'y_max', 'y_min', 'table_list' , 'equation',
                                                      'monthly_split', 'plot_dropdown','graph_type'))
            
            print(f'printing tempg_dict: {temp_dict}')
            state_county_list = []
            for state, counties in temp_dict.items():
                for county in counties:
                    state_county_list.append({"state": state, "county": county})
            print(f'This is the df for state and county {state_county_list}')
            self.table_export_df = pd.DataFrame(state_county_list)

#End of Save State Code

            image_graph = FigureCanvasTkAgg(fig, master=self.tab)  # try and attach to the right element here
            image_graph.draw()
            image_graph.get_tk_widget().grid(row=2, column=0, sticky="nwes", rowspan=8, padx=(20,20), pady=(20,20))
            
            # Coefficient Button
            if drop_down == 'Connected':
                if self.button_coeff is not None:
                    self.button_coeff.destroy()
                    self.button_coeff = None
                if self.export_csv_button is not None:
                    self.export_csv_button.destroy()
                    self.export_csv_button = None
                    self.export_csv_df = None
            else:
                self.export_csv_df = export_csv(process_type=process_type, df_list=df_list,
                                                state_dict=(states if data_type in state_data_types else temp_dict),
                                                date_range={'begin_month': begin_month, 'begin_year': begin_year,
                                                'end_month': end_month, 'end_year': end_year}, data_type=data_type,
                                                deg=polynomial_degree, deriv=(0 if derivitive_degree is None else derivitive_degree),
                                                drought_data=(True if data_type in state_data_types else False),
                                                yearly_offset_diff=(None if isinstance(double_plot_diff, int) and
                                                                            double_plot_diff <= 0 else double_plot_diff))

                # Export CSV Button
                self.graph = image_graph
                self.export_csv_button = TTK.Button(self.tab, command=save_csv_file, width="19", text="Export data to CSV", bootstyle="blue")
                self.export_csv_button.grid(row=9, column=1, padx=(250,0), pady=(0, 0))

        # If Yearly offset is selected, imput box for Yearly Diff appears
        def yearly_offset(plot_type):
            if plot_type == "Yearly Offset":     
                self.ent3 = tkboot.Entry(self.tab, width="6", textvariable=plot_type)
                self.ent3.grid(row=3, column=1, padx=(260,0), pady=(0,0))
                self.year_offset = tk.Label(self.tab, font="10", text="Year Diff: ")
                self.year_offset.grid(row=3, column=1, padx=(120, 0), pady=(0,0))
            else:
                if self.ent3 is not None:
                    self.ent3.destroy()
                    self.ent3 = None
                    self.year_offset.destroy()
                    self.year_offset = None
   

        def gen_plot_type(event=None):
            plot_type = event.widget.get()
            yearly_offset(plot_type)
            """
            if event.widget.get() == 'Yearly Offset':
                self.ent3 = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                self.ent3.grid(row=3, column=1, padx=(240,0), pady=(30,0))
                self.year_offset = tk.Label(self.tab, font="10", text="Year Diff: ")
                self.year_offset.grid(row=3, column=1, padx=(100, 0), pady=(30,0))
            else:
                if self.ent3 is not None:
                    self.ent3.destroy()
                    self.ent3 = None
                    self.year_offset.destroy()
                    self.year_offset = None

                    """
                    

        def gen_equation(event=None):
            # Remove all degree / deriv boxes on click and repopulate if necessary
            if self.ent is not None:
                self.ent.destroy()
                self.ent = None
                self.degree_label.destroy()
                self.degree_label = None
            if self.ent2 is not None:
                self.ent2.destroy()
                self.ent2 = None
                self.deriv_label.destroy()
                self.deriv_label = None

            if event == None:
                degree = ''
            else:
                if event.widget.get() == "n-degree..":
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=4, column=1, padx=(230, 0), pady=(10,0))
                    self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    self.degree_label.grid(row=4, column=1, padx=(100, 0), pady=(10,0))
                elif event.widget.get() == 'n-degree derivative':
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=4, column=1, padx=(230, 0), pady=(10,0))
                    self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    self.degree_label.grid(row=4, column=1, padx=(100, 0), pady=(10,0))
                    self.ent2 = tkboot.Entry(self.tab, width="6")
                    self.ent2.grid(row=5, column=1, padx=(260, 0), pady=(10,0))
                    self.deriv_label = tk.Label(self.tab, font="10", text="Derivitive: ")
                    self.deriv_label.grid(row=5, column=1, padx=(110, 0), pady=(10,0))
                elif event.widget.get() == "Connected-Curve":
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=4, column=1, padx=(230, 0), pady=(10,0))
                    self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    self.degree_label.grid(row=4, column=1, padx=(100, 0), pady=(10,0))
                else:
                    degree = event.widget.get()
                    #print("Degree of equation is: ")
                    #print(degree_dict[degree])
            
        def gen_datatype_columns(event):
            print("User selected this data type: " + event.widget.get())
            print("parsing data type into correct format.... ")
            
            columns = event.widget.get()
            #Data type 'columns' for database function 'get_data_for_counties_dataset'
            print("Data type in correct format is: " + datatype_dict[columns])
            
        def delete_from_table():
            for row in self.data_table.selection():
                self.data_table.delete(row)

        def delete_all_from_table():
            for row in self.data_table.get_children():
                self.data_table.delete(row)
            
        def gen_counties(event=None):
            if event == None:
                state = ''
            else:
                state = event.widget.get()
            data = get_counties_for_state(state)
            if state == 'All States':
                print("All states selected")
                #logic for all states selection goes here
                #self.dropdown_county['values'] = all_counties
                #data = get_all_counties()

            print("Your query returned this data: ")
            data = [ x[0] for x in data ]
            data = ['All Counties'] + data
            print(data)
            self.dropdown_county['values'] = data
            self.dropdown_county.grid(row=1, column=1, padx=(290, 0), pady=(0, 0))

        #Fill the specific dates table
        def gen_specific_date_table(event=None):
            if event == None:
                #year = ''
                month = ''
            else:
                month = event.widget.get()
                #year = self.specific_years.get()
                print(month)
                #print(year)
            if month == 'All months':
                data = [('January'), ('February'), ('March'), ('April'), ('May'), ('June'), ('July'), ('August'), ('September'), ('October'), ('November'), ('December')]
            else:
                data = [(month)]
            for row in data:
                self.date_table.insert(parent='', index='end', values=row)
            self.date_table.grid(row=7, column=1, pady=(15,0), padx=(400,0))

        def gen_table(event=None):
            if event == None:
                county_name = ''
                state = ''
            else:
                county_name = event.widget.get()
                state = self.dropdown_state.get()
            if (county_name, state) in [(self.data_table.item(x)['values'][1],
                                         self.data_table.item(x)['values'][0])
                                        for x in self.data_table.get_children()]:
                return
            if state == 'All States':
                data = get_all_counties_all_data()
            elif county_name == 'All Counties':
                data = get_counties_for_state_all_data(state)
            else:
                data = get_selected_counties_for_state(state, county_name)
            print("Your query returned this data: ")
            print(data)
            for row in data:
                print(row)
                self.data_table.insert(parent='', index='end', values=row)
            self.data_table.grid(row=2, column=1, pady=(0,83), padx=(250, 235))
            print("This: ", self.data_table.get_children())


        def widgets(frame):
            self.tab = tk.Frame(frame, width=x_max, height=y_max)
            self.tab.grid_columnconfigure(0, weight=1, uniform="main_columns")  # need to set a uniform group to force equal width
            self.tab.grid_rowconfigure(0, weight=0)  # smush this one! might need it later tho

            self.tab.grid_columnconfigure(1, weight=1, uniform="main_columns") # set the second column, now they will be equal width

            # and set all the rows (there's eight!)
            self.tab.grid_rowconfigure(1, weight=1)
            self.tab.grid_rowconfigure(2, weight=1)
            self.tab.grid_rowconfigure(3, weight=1)
            self.tab.grid_rowconfigure(4, weight=1)
            self.tab.grid_rowconfigure(5, weight=1)
            self.tab.grid_rowconfigure(6, weight=1)
            self.tab.grid_rowconfigure(7, weight=1)
            self.tab.grid_rowconfigure(8, weight=1)
            self.tab.grid_rowconfigure(9, weight=1)

            # show where the graph will be even when it hasn't been generated yet
            self.empty_grid = tkboot.Label(self.tab, background="#181818")
            self.empty_grid.grid(row=2, column=0, sticky="nwes", rowspan=8, padx=(20,20), pady=(20,20))


            #Notebook   
            self.notebook_label = tk.Label(self.tab, font="12")
            self.notebook_label.grid(row=1, column=0, padx=(10, 500), pady=10)
            #Date range widgets
            self.begin_date_ent = tkboot.Entry(self.tab, textvariable=self.begin_year, width=10)
            self.begin_date_ent.insert(0, "01/1895")
            self.begin_date_ent.grid(row=2, column=1, padx=(0,0), pady=(150,30))

            self.end_date_ent = tkboot.Entry(self.tab, textvariable=self.end_year, width=10)
             #get_latest_date
            today = date.today()
            # Handles January case to shift back one year
            if(today.month == 1):
                endMonth = 12
                today = today.replace(year = int(today.year) -1)
            else:
                endMonth = today.month - 1
            nextMonth = str(int(endMonth))
            if(endMonth < 10):
                nextMonth = "0" + nextMonth
            latestDate = today.strftime("%d/%m/%Y")
            latestDate = nextMonth + latestDate[5:]
            self.end_date_ent.insert(0, latestDate)
            self.end_date_ent.grid(row=2, column=1, padx=(0, 0), pady=(200,30))

            self.begin_date_label = tkboot.Label(self.tab, font="10", text="Date range begin: ", bootstyle="inverse-dark")
            self.begin_date_label.grid(row=2, column=1, padx=(0, 250), pady=(150,30))

            self.end_date_label = tkboot.Label(self.tab, font="10", text="Date range end: ", bootstyle="inverse-dark")
            self.end_date_label.grid(row=2, column=1, padx=(0, 260), pady=(200,30))

            #Entry box for y-axis limits 
            self.entry_ymax = TTK.Entry(self.tab, font="Helvetica 12", width=4)
            self.entry_ymax.bind('<<ComboboxSelected>>', gen_equation)
            self.entry_ymax.grid(row=1, column=0, padx=(100,0), pady=(0,10))
            self.label_ymax = TTK.Label(self.tab, font="Helvetica 12", text="ymax", width=4)
            self.label_ymax.grid(row=1, column=0, padx=(0, 0), pady=(0, 10))
            
            self.entry_ymin = TTK.Entry(self.tab, font="Helvetica 12", width=4)
            self.entry_ymin.bind('<<ComboboxSelected>>', gen_equation)
            self.entry_ymin.grid(row=1, column=0, padx=(100,220), pady=(0,10))
            self.label_ymin = TTK.Label(self.tab, font="Helvetica 12", text="ymin", width=4)
            self.label_ymin.grid(row=1, column=0, padx=(0, 220), pady=(0, 10))

   

            # Initialize Table Widget
            self.data_table = TTK.Treeview(self.tab, height=7)
            self.data_table['columns'] = ('state', 'county_name', 'county_code', 'country')
            self.data_table.column('#0', width=0, stretch=tk.NO)
            self.data_table.column('state', width=110, anchor=CENTER)
            self.data_table.column('county_name', width=110, anchor=CENTER)
            self.data_table.column('county_code', width=110, anchor=CENTER)
            self.data_table.column('country', width=80, anchor=CENTER)
            self.data_table.heading('#0', text="", anchor=tk.CENTER)
            self.data_table.heading('state', text="State")
            self.data_table.heading('county_name', text="County Name")
            self.data_table.heading('county_code', text="County Code")
            self.data_table.heading('country', text="Country")

            #Delete selected rows from the table
            delete_btn = tkboot.Button(self.tab, text="Delete row(s)", command=delete_from_table)
            delete_btnTip = Hovertip(delete_btn, 'Delete selected row(s) from table')
            delete_btn.grid(row=2, column=1, padx=(560,0), pady=(0,210))

            #Delete every row from the table
            delete_all_rows = tkboot.Button(self.tab, text="Delete all", command=delete_all_from_table)
            delete_all_rows_tip = Hovertip(delete_all_rows, 'Delete all rows from table')
            delete_all_rows.grid(row=2, column=1, padx=(535,0), pady=(0,120))

            #Table widget for specific dates
            self.date_table = TTK.Treeview(self.tab, height=5)
            self.date_table['columns'] = ('Month')
            self.date_table.column('#0', width=0, stretch=tk.NO)
            self.date_table.column('Month', width=200)
            self.date_table.heading('#0', text="", anchor=tk.CENTER)
            self.date_table.heading('Month', text="Month")

            # Initialize State Dropdown Widget
            self.dropdown_state = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_state.set('Select state...')
            self.dropdown_state['state'] = 'readonly'
            self.dropdown_state['values'] = (['All States', 'AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY'])
            self.dropdown_state.bind('<<ComboboxSelected>>', gen_counties)
            self.dropdown_state.grid(row=1, column=1, padx=(0, 230))

            # Initialize Counties Dropdown Widget
            self.dropdown_county = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_county.set('Select county...')
            self.dropdown_county['state'] = 'readonly'
            self.dropdown_county['values'] = (['No state selected'])
            self.dropdown_county.bind('<<ComboboxSelected>>', gen_table)
            self.dropdown_county.grid(row=1, column=1, padx=(260, 0))

            self.button2 = TTK.Button(self.tab, text = "Open map", width="15", bootstyle="secondary", command=lambda: controller.open_map("TODO:"))
            self.button2.grid(row=2, column=1, padx=(610,0), pady=(0,300))
             #Dropdown for plot type  selection\
            
            self.plot_type = TTK.Combobox(self.tab, font="Helvetica 12")
            self.plot_type.set('Select plot type...')
            self.plot_type['state'] = 'readonly'
            self.plot_type['values'] = ['Line', 'Yearly Offset']
            self.plot_type.bind('<<ComboboxSelected>>', gen_plot_type)
            self.plot_type.grid(row=3, column=1,  padx=(0, 190),pady=(0,10))
            datatypeTip = Hovertip(self.plot_type, 'Select plot type')
    
            #Dropdown Widget for equation selection
            self.dropdown_equations = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_equations.set('Select equation...')
            self.dropdown_equations['state'] = 'readonly'
            self.dropdown_equations['values'] = ['Connected', 'Connected-Curve', 'Linear', 
                                                 'Quadratic', 'Cubic', 'n-degree..', 'n-degree derivative']
            self.dropdown_equations.bind('<<ComboboxSelected>>', gen_equation)
            self.dropdown_equations.grid(row=4, column=1,  padx=(0, 190),pady=(0,10))
            

            #Dropdown for datatype selection
            self.dropdown_graphs = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_graphs.set('Select data type...')
            self.dropdown_graphs['state'] = 'readonly'
            self.dropdown_graphs['values'] = ["Minimum temperature", "Maximum temperature", "Average temperature", "Precipitation", "Palmer Drought Severity", "Palmer Hydrological Drought", "Modified Palmer Drought Severity", "1-month Standardized Precipitation", "2-month Standardized Precipitation", "3-month Standardized Precipitation", "6-month Standardized Precipitation", "9-month Standardized Precipitation", "12-month Standardized Precipitation", "24-month Standardized Precipitation"]
            self.dropdown_graphs.bind('<<ComboboxSelected>>', gen_datatype_columns)
            self.dropdown_graphs.grid(row=5, column=1,  padx=(0, 190),pady=(0,10))
            datatypeTip = Hovertip(self.dropdown_graphs, 'Select which type of weather data to graph')

            #Button for submitting all that the user has entered
            self.data_submit = tkboot.Button(
                self.tab,
                command=on_enter_data,
                width="25",
                text="Graph it!",
                bootstyle=DEFAULT
            )
            self.data_submit.grid(row=9, column=1, padx=(0,185), pady=(0,0))

#Save State Code
            # Export Button
            self.save_state_export_button = TTK.Button(self.tab, command=save_state_export ,width="25", text="Save State Export", bootstyle=DEFAULT)
            self.save_state_export_button.grid(row=8, column=1, padx=(250,0), pady=(0, 0))

            # Import Button
            self.save_state_import_button = tkboot.Button(self.tab, command=save_state_import, width="25", text="Save State Import", bootstyle=DEFAULT)
            self.save_state_import_button.grid(row=8, column=1, padx=(0,185), pady=(0,0))

            #3/6: Buttons
            # Table Export Button
            self.table_export_button = TTK.Button(self.tab, command=table_export ,width="25", text="Table Export (txt)", bootstyle=DEFAULT)
            self.table_export_button.grid(row=7, column=1, padx=(250,0), pady=(0, 0))

            # Table Import Button
            self.table_import_button = tkboot.Button(self.tab, command=table_import, width="25", text="Table Import (txt)", bootstyle=DEFAULT)
            self.table_import_button.grid(row=7, column=1, padx=(0,185), pady=(0,0))
#End of Save State Code
   
            # Generate Table Rows
            gen_table()
            return self.tab

#Save State Code
        # Code the Save State Export Button triggers
        def save_state_export():
            if self.save_state_export_df is not None:
                file_name = asksaveasfilename()
                # Its important to use binary mode
                dbfile = open(file_name, 'ab')
                # source, destination
                pickle.dump(self.save_state_export_df, dbfile)                    
                dbfile.close()

        # Code the Save State Import Button triggers
        def save_state_import():
            file_name = askopenfilename()
            dbfile = open(file_name, 'rb')
            self.save_state_import_df = pickle.load(dbfile)
           
            plot_type = self.save_state_import_df.loc[0]['plot_type']
            df_list = self.save_state_import_df.loc[0]['df_list']

            # Grab the list of state and counties to restore table
            rows = self.save_state_import_df.loc[0]['table_list']

            # Grab all UI elements to restore
            equation        = self.save_state_import_df.loc[0]['equation']
            plot_points     = self.save_state_import_df.loc[0]['plot_points']
            show_legend     = self.save_state_import_df.loc[0]['show_legend'] 
            monthly_split   = self.save_state_import_df.loc[0]['monthly_split']
            plot_dropdown   = self.save_state_import_df.loc[0]['plot_dropdown']
            graph_type      = self.save_state_import_df.loc[0]['graph_type']

            plot_vars_map = {'process_type': self.save_state_import_df.loc[0]['process_type'],
                             'double_plot_diff': self.save_state_import_df.loc[0]['double_plot_diff'],
                             'plot_points': self.save_state_import_df.loc[0]['plot_points'],
                             'connected_curve': self.save_state_import_df.loc[0]['connected_curve'],
                             'begin_month': self.save_state_import_df.loc[0]['begin_month'],
                             'end_month': self.save_state_import_df.loc[0]['end_month'],
                             'degree': self.save_state_import_df.loc[0]['degree'],
                             'deriv_degree': self.save_state_import_df.loc[0]['deriv_degree'],
                             'plots_per_graph' : self.save_state_import_df.loc[0]['plots_per_graph'],
                             'names' : self.save_state_import_df.loc[0]['names'],
                             'show_legend': self.save_state_import_df.loc[0]['show_legend'],
                             'y_max': self.save_state_import_df.loc[0]['y_max'],
                             'y_min': self.save_state_import_df.loc[0]['y_min']}
           
            # TODO: Date range beging, date range end, ymin, ymax, 
            # TODO: Restore Yearly Diff, Derivitive, Degree boxes when dropdown choices are selected


            print('Testing vars: ')
            print("Equation: " + equation)
            print("Plot_type: " + plot_type)
            print("Plot_dropdown:" + plot_dropdown)
            #print("Plot_point " + plot_points) 
            # print("Show legend:" + show_legend)
            # print("Monthly split " + monthly_split)
            
            # Restore the checkbuttons state
            if(plot_points):
                self.plot_points.state(['selected'])
            if(monthly_split):
                self.monthly_check.state(['selected'])
            if(show_legend == 0):
                self.plot_hide_legend.state(['selected'])

            # Restore the state of dropdowns: equations, plot type, graphs
            self.dropdown_equations.set(equation)
            self.plot_type.set(plot_dropdown)
            self.dropdown_graphs.set(graph_type)

            # Check if the equation is special case: "n-degree", "n-degree derivative", or "connected curve"
            check_eq(equation)
            yearly_offset(plot_dropdown)
            
            # Import cases for state and county table
            # Case 1: All states and counties
            # Case 2: Specific state and all counties
            # Case 3: List of states and list of counties
            # Restoring all the table data
            for state, county in rows.items():
                print(f'The county of {state} is ') 
                for line in county:
                    print(line)
                    line = get_selected_counties_for_state(state, line)
                    for row in line:
                        self.data_table.insert(parent='', index='end', values=row)
                    self.data_table.grid(row=2, column=1, pady=(0,83), padx=(250, 235))


                        
            dbfile.close()

            #Proof of Concept Style Style, can't graph b/c of df_list
            fig, x_data, y_data = plotting.plot(plot_type, df_list, plot_vars_map)
            image_graph = FigureCanvasTkAgg(fig, master=self.tab)  # try and attach to the right element here
            image_graph.draw()
            image_graph.get_tk_widget().grid(row=2, column=0, sticky="nwes", rowspan=8, padx=(20,20), pady=(20,20))

        # Checks Check if the equation is either, "n-degree", "n-degree derivative", or "connected curve"
        # If any apply then additional degree/derivative entry box needs to be restored
        def check_eq(equation):

            if equation == "n-degree..":  
                self.ent = tkboot.Entry(self.tab, width = "6", textvariable = equation)
                self.ent.grid(row = 4, column = 1, padx = (230, 0), pady = (10,0))
                self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                self.degree_label.grid(row = 4, column = 1, padx = (100, 0), pady = (10,0))
            elif equation == 'n-degree derivative':
                self.ent = tkboot.Entry(self.tab, width="6", textvariable=equation)
                self.ent.grid(row=4, column=1, padx=(230, 0), pady=(10,0))
                self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                self.degree_label.grid(row=4, column=1, padx=(100, 0), pady=(10,0))
                self.ent2 = tkboot.Entry(self.tab, width="6")
                self.ent2.grid(row=5, column=1, padx=(260, 0), pady=(10,0))
                self.deriv_label = tk.Label(self.tab, font="10", text="Derivitive: ")
                self.deriv_label.grid(row=5, column=1, padx=(110, 0), pady=(10,0))
            elif equation == "Connected-Curve":
                self.ent = tkboot.Entry(self.tab, width="6", textvariable=equation)
                self.ent.grid(row=4, column=1, padx=(230, 0), pady=(10,0))
                self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                self.degree_label.grid(row=4, column=1, padx=(100, 0), pady=(10,0))

        #3/6:
        # Code the Table Export Button triggers
        def table_export():
            if self.table_export_df is not None:
                file_name = asksaveasfilename(filetypes=[("text file", "*.txt")],
                                        defaultextension='.txt')
                print(f'THis is the filename: {file_name}')
                self.table_export_df.to_csv(file_name, sep=',', index=False, header=['state', 'counties'])
            else:
                print("table export stub")

        # Code the Table Export Button triggers
        def table_import():
            # allow user to open multiple files
            file_names = askopenfilenames()
            # loop through each file to make one big panda
            self.table_import_df = pd.concat((pd.read_csv(f, sep=',') for f in file_names),
                                             ignore_index=True)

            if self.table_import_df is not None:
                for index in range(len(self.table_import_df.index)):
                    state = self.table_import_df['state'][index]
                    county = self.table_import_df['counties'][index]

                    # Grab the row of data for the table
                    row = get_selected_counties_for_state(state, county)
                    # Insert the row back into state county table
                    for val in row:
                        # copied (and improved) logic to prevent duplicate insertions
                        if (county, state) in [(self.data_table.item(x)['values'][1],
                                                self.data_table.item(x)['values'][0])
                                               for x in self.data_table.get_children()]:
                            continue
                        self.data_table.insert(parent='', index='end', values=val)
                    
#End of Save State Code
                
        # Exporting data to csv

        #function for calculating standard error
        def get_standard_error(x_inputs, y_inputs):
            #build polyfit input values for calc
            y_mean = np.mean(y_inputs)
            x_mean = np.mean(x_inputs)
            n = len(y_inputs)
            x_sum = 0
            y_sum = 0
            x_y_sum = 0     

            for x in x_inputs:
                x_sum += (x-x_mean)**2

            for y in y_inputs:
                y_sum += (y-y_mean)**2      

            for x,y in zip(x_inputs,y_inputs):
                x_y_sum += (x - x_mean) * (y - y_mean)

            #use polyfit list to calc standard error  
            stndrd_err = np.sqrt((1/(n-2)) * (y_sum - ((x_y_sum**2)/x_sum)))        

            return stndrd_err 

        def save_csv_file():
            if self.export_csv_df is not None:
                file_name = asksaveasfilename(filetypes=[("CSV files", "*.csv")],
                                              defaultextension='.csv')
                orig_file_name = file_name[0:-4] + ".original" + file_name[-4:]
                self.export_csv_df.to_csv(orig_file_name, sep=',', encoding='utf-8', index=False)

                polynomial_degree = degree_dict[self.dropdown_equations.get()] if self.ent == None else int(self.ent.get())
                print(polynomial_degree)
                print(self.export_csv_df)
                exportdf = self.export_csv_df
                #grab the name of the type of data, located in the last column
                dataName = self.export_csv_df.columns[-1]
                steyxList = [''] * len(self.export_csv_df)
                steyx11List = [''] * len(self.export_csv_df)
                smoothedData = [''] * len(self.export_csv_df)
                #grab the indecies of the counties
                indecies = np.where(self.export_csv_df['County'] != '')[0].tolist()
                #add on the end of the list to indecies to facilitate end on last loop
                indecies.append(len(self.export_csv_df))
                #this grabs a row based on numeric index
                #print(self.export_csv_df.iloc[indecies[0]])

                for i in range(1,len(indecies)):
                    #define the slice of data were looking at
                    start = indecies[i-1]
                    end = indecies[i]

                    #these years should be the same in each loop, but keeping this here just in case
                    years = self.export_csv_df.Year.values[start:end].astype(int)
                    #OKAY SO HERE'S THE DEAL, this fucntion was originally created with the assumption that the columns of the dataframe were in the following order:
                    #State, County, Year, N number coefficients where N is the degree of the line, and ONE column of data, as the split months function can't export csv.
                    #AT SOME POINT between February 28th 2023, and March 4th 2023, this behavior changed without me pulling any changes, and started including an EXTRA column of data AND I DON'T KNOW WHY
                    #This data is labeled as February, which would be a great start for the split months data export, but this occors when not splitting months.
                    #In any case, this fix *SHOULD* grab the correct coeffs assuming the first 3 columns and the polynomial_degree get don't start changing too
                    coeffs = self.export_csv_df.iloc[start].to_numpy()[3:3+polynomial_degree+1]
                    coeffs = coeffs.astype(float)
                    yearcount = 0
                    for j in range(start,end):
                        smoothedData[j] = np.polyval(coeffs,int(years[yearcount]))
                        yearcount+=1
                    steyxList[start] = get_standard_error(years,smoothedData[start:end])
                    yearcount = 5
                    for k in range(start+5,end-5):
                        steyx11List[k] = get_standard_error(years[yearcount-5:yearcount+6],smoothedData[k-5:k+6])
                        yearcount += 1


                exportdf['Smoothed Data'] = smoothedData
                exportdf['STEYX'] = steyxList
                exportdf['STEYX 11'] = steyx11List

                exportdf.to_csv(file_name, sep=',', encoding='utf-8', index=False)
                
                # Export Graph to PNG format
                if self.graph is None:
                    print('There is no graph to export')
                else:
                    file_name = file_name[:-4]
                    graph_file = file_name + '.png'
                    fig = self.graph.figure
                    fig.savefig(graph_file)




        frame = ttk.Notebook(self, width=x_max, height=y_max)  # again its the notebook that needs to fill
        frame.pack(fill='both', pady=10, expand=True)
        tabs = ["Notebook1", "Notebook2", "Notebook3", "Notebook4"]
        tab1 = widgets(frame)
        frame.add(tab1, text = "Main")

        # Monthly Split checkbox
        self.monthly_check_var = tk.IntVar()
        self.monthly_check = TTK.Checkbutton(self.tab, text='Split Months', variable=self.monthly_check_var)
        self.monthly_check.grid(row=2, column=1,  padx=(300, 0), pady=(150, 0))
        splitTip = Hovertip(self.monthly_check, 'Plot induvidual equations for each month')

        # Scatter Box Split checkbox
        self.plot_points_var = tk.IntVar()
        self.plot_points = TTK.Checkbutton(self.tab, text='Enable Scatter Plotting', variable=self.plot_points_var)
        self.plot_points.grid(row=2, column=1,  padx=(365, 0), pady=(200, 0))
        scatterTip = Hovertip(self.plot_points, 'Check to enable scatter plotting on graph')

        # Hide Plot Legend checkbox
        self.plot_hide_legend_var = tk.IntVar()
        self.plot_hide_legend = TTK.Checkbutton(self.tab, text='Hide Plot Legend', variable=self.plot_hide_legend_var)
        self.plot_hide_legend.grid(row=2, column=1,  padx=(330, 0), pady=(250, 0))
        hideLegendTip = Hovertip(self.plot_hide_legend, 'Check to disable the legend on the graph')

       
        # Generate Table Rows
        gen_table()

# WIDGETS ----------------------------------------------------------------------------       
        
def start_ui():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    start_ui()
