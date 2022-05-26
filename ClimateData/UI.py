#!/usr/bin/env python3
import tkinter as tk
from tkinter import LEFT, ttk, Canvas
import ttkbootstrap as tkboot
from ttkbootstrap import ttk as TTK
from ttkbootstrap import font as tkfont
from ttkbootstrap.constants import *
from tkinter.filedialog import asksaveasfilename
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
        tab = tk.Frame(self.container, width=1920, height=1080)
        self.container.add(tab, text=f'Tab {self.tab_counter}')
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        loop = 0 
        data = ["StartPage", "graphPage"]
        for F in (StartPage, graphPage):
            current_frame = F(parent=tab, controller=self, master=tab)
            #self.frame_list.append(current_frame)
            if loop == 0:
                self.frames.append({})
            self.frames[self.tab_counter - 1][data[loop]] = current_frame
            current_frame.grid(row=0, column=0)
            current_frame.grid_columnconfigure(0,weight=1)
            current_frame.grid_columnconfigure(1,weight=1)
            current_frame.grid_columnconfigure(2,weight=1)
            current_frame.grid_rowconfigure(0,weight=1)
            current_frame.grid_rowconfigure(1,weight=1)
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
        self.geometry('1920x1080')
        tk.Grid.rowconfigure(self,0,weight=1)
        tk.Grid.columnconfigure(self,0,weight=1)
        tk.Grid.rowconfigure(self,1,weight=1)
        tkboot.Style('darkly')

        self.app = QApplication([])
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.container = ttk.Notebook(self)

        self.container.grid(row=0, column=0)
        self.container.grid_columnconfigure(0,weight=1)
        self.container.grid_columnconfigure(1,weight=1)
        self.container.grid_columnconfigure(2,weight=1)
        self.container.grid_rowconfigure(0,weight=1)
        self.container.grid_rowconfigure(1,weight=1)
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
        self.new_tab.grid(row=0, column=0, padx=(0,100), pady=(0,0), sticky='NE')
        self.new_tab.grid_columnconfigure(0,weight=1)
        self.new_tab.grid_columnconfigure(1,weight=1)
        self.new_tab.grid_columnconfigure(2,weight=1)
        self.new_tab.grid_rowconfigure(0,weight=1)
        self.new_tab.grid_rowconfigure(1,weight=1)
        self.new_tabTip = Hovertip(self.new_tab, 'Create a new notebook tab')

        #Delete button for a notebook tab
        self.delete_tab = tkboot.Button(
            self,
            command=self.destroy_tab,
            width="10",
            text="Delete tab",
            bootstyle=DEFAULT
        )
        self.delete_tab.grid(row=0, column=0, padx=(0,0), pady=(0,0), sticky='NE')
        self.delete_tab.grid_columnconfigure(0,weight=1)
        self.delete_tab.grid_columnconfigure(1,weight=1)
        self.delete_tab.grid_columnconfigure(2,weight=1)
        self.delete_tab.grid_rowconfigure(0,weight=1)
        self.delete_tab.grid_rowconfigure(1,weight=1)
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

        # Yearly Offset Input Selection
        self.ent3 = None
        self.year_offset = None

        # Degree inputs and labels
        self.ent = None
        self.degree_label = None
        self.ent2 = None
        self.deriv_label = None

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
            monthly_split   = self.monthly_check_var.get()

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
            fig, x_data, y_data = plotting.plot(plot_type, df_list, {'process_type': process_type, 'double_plot_diff': double_plot_diff,
                                                     'plot_points': plot_points, 'connected_curve': connected_curve,
                                                     'begin_month': monthsIdx[begin_month], 'end_month': monthsIdx[end_month],
                                                     'degree': polynomial_degree, 'deriv_degree': derivitive_degree,
                                                     'plots_per_graph' : len(df_list), 'names' : (remove_alaska(states) if data_type in state_data_types else counties)})


            image_graph = FigureCanvasTkAgg(fig, master = master)  
            image_graph.draw()
            image_graph.get_tk_widget().grid(row=0, column=0, pady=(50, 0), padx=(10, 600))
            image_graph.grid_columnconfigure(0,weight=1)
            image_graph.grid_columnconfigure(1,weight=1)
            image_graph.grid_columnconfigure(2,weight=1)
            image_graph.grid_rowconfigure(0,weight=1)
            image_graph.grid_rowconfigure(1,weight=1)

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
                                                drought_data=(True if data_type in state_data_types else False))

                # Export CSV Button
                self.export_csv_button = TTK.Button(self.tab, command=save_csv_file ,width="16", text="Export data to CSV", bootstyle="blue")
                self.export_csv_button.grid(row=9, column=1, padx=(250,0), pady=(50, 0))
                self.export_csv_button.grid_columnconfigure(0,weight=1)
                self.export_csv_button.grid_columnconfigure(1,weight=1)
                self.export_csv_button.grid_columnconfigure(2,weight=1)
                self.export_csv_button.grid_rowconfigure(0,weight=1)
                self.export_csv_button.grid_rowconfigure(9,weight=1)

        def gen_plot_type(event=None):
            if event.widget.get() == 'Yearly Offset':
                self.ent3 = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                self.ent3.grid(row=6, column=1, padx=(240,0), pady=(30,0))
                self.ent3.grid_columnconfigure(0,weight=1)
                self.ent3.grid_columnconfigure(1,weight=1)
                self.ent3.grid_columnconfigure(2,weight=1)
                self.ent3.grid_rowconfigure(0,weight=1)
                self.ent3.grid_rowconfigure(6,weight=1)
                self.year_offset = tk.Label(self.tab, font="10", text="Year Diff: ")
                self.year_offset.grid(row=6, column=1, padx=(100, 0), pady=(30,0))
                self.year_offset.grid_columnconfigure(0,weight=1)
                self.year_offset.grid_columnconfigure(1,weight=1)
                self.year_offset.grid_columnconfigure(2,weight=1)
                self.year_offset.grid_rowconfigure(0,weight=1)
                self.year_offset.grid_rowconfigure(6,weight=1)
            else:
                if self.ent3 is not None:
                    self.ent3.destroy()
                    self.ent3 = None
                    self.year_offset.destroy()
                    self.year_offset = None

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
                    self.ent.grid(row=7, column=1, padx=(240,0), pady=(30,0))
                    self.ent.grid_columnconfigure(0,weight=1)
                    self.ent.grid_columnconfigure(1,weight=1)
                    self.ent.grid_columnconfigure(2,weight=1)
                    self.ent.grid_rowconfigure(0,weight=1)
                    self.ent.grid_rowconfigure(7,weight=1)
                    self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    self.degree_label.grid(row=7, column=1, padx=(100, 0), pady=(30,0))
                    self.degree_label.grid_columnconfigure(1,weight=1)
                    self.degree_label.grid_columnconfigure(2,weight=1)
                    self.degree_label.grid_rowconfigure(0,weight=1)
                    self.degree_label.grid_rowconfigure(7,weight=1)
                elif event.widget.get() == 'n-degree derivative':
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=7, column=1, padx=(240,0), pady=(30,0))
                    self.ent.grid_columnconfigure(0,weight=1)
                    self.ent.grid_columnconfigure(1,weight=1)
                    self.ent.grid_columnconfigure(2,weight=1)
                    self.ent.grid_rowconfigure(0,weight=1)
                    self.ent.grid_rowconfigure(7,weight=1)
                    self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    self.degree_label.grid(row=7, column=1, padx=(100, 0), pady=(30,0))
                    self.degree_label.grid_columnconfigure(1,weight=1)
                    self.degree_label.grid_columnconfigure(2,weight=1)
                    self.degree_label.grid_rowconfigure(0,weight=1)
                    self.degree_label.grid_rowconfigure(7,weight=1)
                    self.ent2 = tkboot.Entry(self.tab, width="6")
                    self.ent2.grid(row=8, column=1, padx=(240,0), pady=(0,80))
                    self.ent2.grid_columnconfigure(0,weight=1)
                    self.ent2.grid_columnconfigure(1,weight=1)
                    self.ent2.grid_columnconfigure(2,weight=1)
                    self.ent2.grid_rowconfigure(0,weight=1)
                    self.ent2.grid_rowconfigure(8,weight=1)
                    self.deriv_label = tk.Label(self.tab, font="10", text="Derivitive: ")
                    self.deriv_label.grid(row=8, column=1, padx=(100, 0), pady=(0,80))
                    self.deriv_label.grid_columnconfigure(1,weight=1)
                    self.deriv_label.grid_columnconfigure(2,weight=1)
                    self.deriv_label.grid_rowconfigure(0,weight=1)
                    self.deriv_label.grid_rowconfigure(8,weight=1)
                elif event.widget.get() == "Connected-Curve":
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=7, column=1, padx=(240,0), pady=(30,0))
                    self.ent.grid_columnconfigure(0,weight=1)
                    self.ent.grid_columnconfigure(1,weight=1)
                    self.ent.grid_columnconfigure(2,weight=1)
                    self.ent.grid_rowconfigure(0,weight=1)
                    self.ent.grid_rowconfigure(7,weight=1)
                    self.degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    self.degree_label.grid(row=7, column=1, padx=(100, 0), pady=(30,0))
                    self.degree_label.grid_columnconfigure(1,weight=1)
                    self.degree_label.grid_columnconfigure(2,weight=1)
                    self.degree_label.grid_rowconfigure(0,weight=1)
                    self.degree_label.grid_rowconfigure(7,weight=1)
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
            if state == 'All states':
                print("All states selected")
                #logic for all states selection goes here
                self.dropdown_county['values'] = all_counties

            print("Your query returned this data: ")
            data = [ x[0] for x in data ]
            data = ['All Counties'] + data
            print(data)
            self.dropdown_county['values'] = data
            self.dropdown_county.grid(row=3, column=1, padx=(290, 0), pady=(0, 0))
            self.dropdown_county.grid_columnconfigure(1,weight=1)
            self.dropdown_county.grid_columnconfigure(2,weight=1)
            self.dropdown_county.grid_rowconfigure(0,weight=1)
            self.dropdown_county.grid_rowconfigure(1,weight=1)

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
            self.date_table.grid_columnconfigure(1,weight=1)
            self.date_table.grid_columnconfigure(2,weight=1)
            self.date_table.grid_rowconfigure(0,weight=1)
            self.date_table.grid_rowconfigure(7,weight=1)

        def gen_table(event=None):
            if event == None:
                county_name = ''
                state = ''
            else:
                county_name = event.widget.get()
                state = self.dropdown_state.get()
            if county_name in [ self.data_table.item(x)['values'][1] for x in self.data_table.get_children()]:
                return
            if county_name == 'All Counties':
                data = get_counties_for_state_all_data(state)
            else:
                data = get_selected_counties_for_state(state, county_name)
            print("Your query returned this data: ")
            print(data)
            for row in data:
                print(row)
                self.data_table.insert(parent='', index='end', values=row)
            self.data_table.grid(row=2, column=1, pady=(0,0), padx=(0, 0))
            self.date_table.grid_columnconfigure(1,weight=1)
            self.date_table.grid_columnconfigure(2,weight=1)
            self.date_table.grid_rowconfigure(0,weight=1)
            self.date_table.grid_rowconfigure(2,weight=1)
            print("This: ", self.data_table.get_children())


        def widgets(frame):
            self.tab = tk.Frame(frame, width=1920, height=1080)
            self.tab.grid_columnconfigure(0,weight=1)
            self.tab.grid_columnconfigure(1,weight=1)
            self.tab.grid_columnconfigure(2,weight=1)
            self.tab.grid_rowconfigure(0,weight=1)
            self.tab.grid_rowconfigure(1,weight=1)
            #Notebook   
            self.notebook_label = tk.Label(self.tab, font="12")
            self.notebook_label.grid(row=1, column=0, padx=(10, 500), pady=10)
            self.notebook_label.grid_columnconfigure(0,weight=1)
            self.notebook_label.grid_columnconfigure(1,weight=1)
            self.notebook_label.grid_columnconfigure(2,weight=1)
            self.notebook_label.grid_rowconfigure(0,weight=1)
            self.notebook_label.grid_rowconfigure(1,weight=1)

            #Date range widgets
            self.begin_date_ent = tkboot.Entry(self.tab, textvariable=self.begin_year, width=10)
            self.begin_date_ent.grid(row=4, column=1, padx=(40,0), pady=(0,0))

            self.end_date_ent = tkboot.Entry(self.tab, textvariable=self.end_year, width=10)
            self.end_date_ent.grid(row=5, column=1, padx=(40, 0), pady=(0,0))

            self.begin_date_label = tkboot.Label(self.tab, font="10", text="Date range begin: ", bootstyle="inverse-dark")
            self.begin_date_label.grid(row=4, column=1, padx=(0, 250), pady=(0,0))        

            self.end_date_label = tkboot.Label(self.tab, font="10", text="Date range end: ", bootstyle="inverse-dark")
            self.end_date_label.grid(row=5, column=1, padx=(0, 263), pady=(0,0))

            self.begin_date_label.grid_columnconfigure(0,weight=1)
            self.begin_date_label.grid_columnconfigure(1,weight=1)
            self.begin_date_label.grid_columnconfigure(2,weight=1)
            self.begin_date_label.grid_rowconfigure(0,weight=1)
            self.begin_date_label.grid_rowconfigure(4,weight=1)

            self.end_date_label.grid_columnconfigure(0,weight=1)
            self.end_date_label.grid_columnconfigure(1,weight=1)
            self.end_date_label.grid_columnconfigure(2,weight=1)
            self.end_date_label.grid_rowconfigure(0,weight=1)
            self.end_date_label.grid_rowconfigure(5,weight=1)

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

            self.data_table.grid_columnconfigure(0,weight=1)
            self.data_table.grid_columnconfigure(1,weight=1)
            self.data_table.grid_columnconfigure(2,weight=1)
            self.data_table.grid_rowconfigure(0,weight=1)
            self.data_table.grid_rowconfigure(1,weight=1)

            #Delete selected rows from the table
            delete_btn = tkboot.Button(self.tab, text="Delete row(s)", command=delete_from_table)
            delete_btnTip = Hovertip(delete_btn, 'Delete selected row(s) from table')
            delete_btn.grid(row=2, column=1, padx=(560,0), pady=(0,0))
            delete_btn.grid_columnconfigure(0,weight=1)
            delete_btn.grid_columnconfigure(1,weight=1)
            delete_btn.grid_columnconfigure(2,weight=1)
            delete_btn.grid_rowconfigure(0,weight=1)
            delete_btn.grid_rowconfigure(2,weight=1)

            #Delete every row from the table
            delete_all_rows = tkboot.Button(self.tab, text="Delete all", command=delete_all_from_table)
            delete_all_rows_tip = Hovertip(delete_all_rows, 'Delete all rows from table')
            delete_all_rows.grid(row=2, column=1, padx=(535,0), pady=(0,120))
            delete_all_rows.grid_columnconfigure(0,weight=1)
            delete_all_rows.grid_columnconfigure(1,weight=1)
            delete_all_rows.grid_columnconfigure(2,weight=1)
            delete_all_rows.grid_rowconfigure(0,weight=1)
            delete_all_rows.grid_rowconfigure(2,weight=1)

            #Table widget for specific dates
            self.date_table = TTK.Treeview(self.tab, height=5)
            self.date_table['columns'] = ('Month')
            self.date_table.column('#0', width=0, stretch=tk.NO)
            self.date_table.column('Month', width=200)
            self.date_table.heading('#0', text="", anchor=tk.CENTER)
            self.date_table.heading('Month', text="Month")
            self.date_table.grid_columnconfigure(0,weight=1)
            self.date_table.grid_columnconfigure(1,weight=1)
            self.date_table.grid_columnconfigure(2,weight=1)
            self.date_table.grid_rowconfigure(0,weight=1)
            self.date_table.grid_rowconfigure(1,weight=1)

            # Initialize State Dropdown Widget
            self.dropdown_state = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_state.set('Select state...')
            self.dropdown_state['state'] = 'readonly'
            self.dropdown_state['values'] = (['All states', 'AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY'])
            self.dropdown_state.bind('<<ComboboxSelected>>', gen_counties)
            self.dropdown_state.grid(row=3, column=1, padx=(0, 190), pady=(20,20))
            self.dropdown_state.grid_columnconfigure(0,weight=1)
            self.dropdown_state.grid_columnconfigure(1,weight=1)
            self.dropdown_state.grid_columnconfigure(2,weight=1)
            self.dropdown_state.grid_rowconfigure(0,weight=1)
            self.dropdown_state.grid_rowconfigure(3,weight=1)

            # Initialize Counties Dropdown Widget
            self.dropdown_county = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_county.set('Select county...')
            self.dropdown_county['state'] = 'readonly'
            self.dropdown_county['values'] = (['No state selected'])
            self.dropdown_county.bind('<<ComboboxSelected>>', gen_table)
            self.dropdown_county.grid(row=3, column=1, padx=(290, 0), pady=(20, 20))
            self.dropdown_county.grid_columnconfigure(0,weight=1)
            self.dropdown_county.grid_columnconfigure(1,weight=1)
            self.dropdown_county.grid_columnconfigure(2,weight=1)
            self.dropdown_county.grid_rowconfigure(0,weight=1)
            self.dropdown_county.grid_rowconfigure(3,weight=1)

            self.button2 = TTK.Button(self.tab, text = "Open map", width="15", bootstyle="secondary", command=lambda: controller.open_map("TODO:"))
            self.button2.grid(row=1, column=1, padx=(0,250), pady=(0,0))
            self.button2.grid_columnconfigure(0,weight=1)
            self.button2.grid_columnconfigure(1,weight=1)
            self.button2.grid_columnconfigure(2,weight=1)
            self.button2.grid_rowconfigure(0,weight=1)
            self.button2.grid_rowconfigure(1,weight=1)

            #Dropdown Widget for equation selection
            self.dropdown_equations = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_equations.set('Select equation...')
            self.dropdown_equations['state'] = 'readonly'
            self.dropdown_equations['values'] = ['Connected', 'Connected-Curve', 'Linear', 
                                                 'Quadratic', 'Cubic', 'n-degree..', 'n-degree derivative']
            self.dropdown_equations.bind('<<ComboboxSelected>>', gen_equation)
            self.dropdown_equations.grid(row=7, column=1,  padx=(0, 190), pady=(30, 0))
            self.dropdown_equations.grid_columnconfigure(0,weight=1)
            self.dropdown_equations.grid_columnconfigure(1,weight=1)
            self.dropdown_equations.grid_columnconfigure(2,weight=1)
            self.dropdown_equations.grid_rowconfigure(0,weight=1)
            self.dropdown_equations.grid_rowconfigure(7,weight=1)


            #Dropdown for datatype selection
            self.dropdown_graphs = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_graphs.set('Select data type...')
            self.dropdown_graphs['state'] = 'readonly'
            self.dropdown_graphs['values'] = ["Minimum temperature", "Maximum temperature", "Average temperature", "Precipitation", "Palmer Drought Severity", "Palmer Hydrological Drought", "Modified Palmer Drought Severity", "1-month Standardized Precipitation", "2-month Standardized Precipitation", "3-month Standardized Precipitation", "6-month Standardized Precipitation", "9-month Standardized Precipitation", "12-month Standardized Precipitation", "24-month Standardized Precipitation"]
            self.dropdown_graphs.bind('<<ComboboxSelected>>', gen_datatype_columns)
            self.dropdown_graphs.grid(row=8, column=1,  padx=(0, 190), pady=(30, 0))
            datatypeTip = Hovertip(self.dropdown_graphs, 'Select which type of weather data to graph')
            self.dropdown_graphs.grid_columnconfigure(0,weight=1)
            self.dropdown_graphs.grid_columnconfigure(1,weight=1)
            self.dropdown_graphs.grid_columnconfigure(2,weight=1)
            self.dropdown_graphs.grid_rowconfigure(0,weight=1)
            self.dropdown_graphs.grid_rowconfigure(8,weight=1)


            #Button for submitting all that the user has entered
            self.data_submit = tkboot.Button(
                self.tab, 
                command=on_enter_data,
                width="25", 
                text="Graph it!", 
                bootstyle=DEFAULT
            )
            self.data_submit.grid(row=9, column=1, padx=(0,185), pady=(50,0))
            self.data_submit.grid_columnconfigure(0,weight=1)
            self.data_submit.grid_columnconfigure(1,weight=1)
            self.data_submit.grid_columnconfigure(2,weight=1)
            self.data_submit.grid_rowconfigure(0,weight=1)
            self.data_submit.grid_rowconfigure(9,weight=1)

            # Generate Table Rows
            gen_table()
            return self.tab

                
        # Exporting data to csv
        def save_csv_file():
            if self.export_csv_df is not None:
                file_name = asksaveasfilename(filetypes=[("CSV files", "*.csv")],
                                              defaultextension='.csv')
                self.export_csv_df.to_csv(file_name, sep=',', encoding='utf-8', index=False)

        frame = ttk.Notebook(self)
        frame.pack(fill='both', pady=10, expand=True)
        frame.grid_columnconfigure(0,weight=1)
        frame.grid_columnconfigure(1,weight=1)
        frame.grid_columnconfigure(2,weight=1)
        frame.grid_rowconfigure(0,weight=1)
        frame.grid_rowconfigure(1,weight=1)
        tabs = ["Notebook1", "Notebook2", "Notebook3", "Notebook4"]
        tab1 = widgets(frame)
        frame.add(tab1, text = "Main") 

        # Monthly Split checkbox
        self.monthly_check_var = tk.IntVar()
        self.monthly_check = TTK.Checkbutton(self.tab, text='Split Months', variable=self.monthly_check_var)
        self.monthly_check.grid(row=4, column=1,  padx=(300, 0), pady=(0, 0))
        splitTip = Hovertip(self.monthly_check, 'Plot induvidual equations for each month')

        # Scatter Box Split checkbox
        self.plot_points_var = tk.IntVar()
        self.plot_points = TTK.Checkbutton(self.tab, text='Enable Scatter Plotting', variable=self.plot_points_var)
        self.plot_points.grid(row=5, column=1,  padx=(365, 0), pady=(10, 0))
        scatterTip = Hovertip(self.plot_points, 'Check to enable scatter plotting on graph')

        #Dropdown for plot type  selection
        self.plot_type = TTK.Combobox(self.tab, font="Helvetica 12")
        self.plot_type.set('Select plot type...')
        self.plot_type['state'] = 'readonly'
        self.plot_type['values'] = ['Line', 'Yearly Offset']
        self.plot_type.bind('<<ComboboxSelected>>', gen_plot_type)
        self.plot_type.grid(row=6, column=1,  padx=(0, 190), pady=(30, 0))
        datatypeTip = Hovertip(self.plot_type, 'Select plot type')
        self.grid_columnconfigure(0,weight=1)
        self.grid_columnconfigure(1,weight=1)
        self.grid_columnconfigure(2,weight=1)
        self.grid_rowconfigure(4,weight=1)
        self.grid_rowconfigure(5,weight=1)
        self.grid_rowconfigure(6,weight=1)
        # Generate Table Rows
        gen_table()

# WIDGETS ----------------------------------------------------------------------------       
        
def start_ui():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    start_ui()
