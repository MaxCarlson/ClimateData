#!/usr/bin/env python3
import tkinter as tk
from tkinter import LEFT, ttk
import ttkbootstrap as tkboot
from ttkbootstrap import ttk as TTK
from ttkbootstrap import font as tkfont
from ttkbootstrap.constants import *
import psycopg2
from database import *
import plotting
import re
from itertools import chain
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import MapUI
from idlelib.tooltip import Hovertip
from PyQt5.QtWidgets import *                   #pip install PyQt5

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

    return True


def validate_degree(degree):
   
    #check that the degree is a number 
    if bool(degree.isnumeric()) == False:
        return False

    return True


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title('Climate Data')
        self.geometry('1920x1080')
        tkboot.Style('darkly')

        self.app = QApplication([])
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        container = ttk.Notebook(self)
        tab1 = tk.Frame(container, width=1920, height=1080)
        container.add(tab1, text ='Notebook tab 1')
        tab2 = tk.Frame(container, width=1920, height=1080)
        container.add(tab2, text ='Notebook tab 2')
        tab3 = tk.Frame(container, width=1920, height=1080)
        container.add(tab3, text ='Notebook tab 3')
        tab4 = tk.Frame(container, width=1920, height=1080)
        container.add(tab4, text ='Notebook tab 4')
        tab5 = tk.Frame(container, width=1920, height=1080)
        container.add(tab5, text ='Notebook tab 5')
        container.grid(row=0, column=0)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        tabs = [tab1,tab2,tab3,tab4,tab5]


        """
        container = ttk.Notebook(self)
        container.pack(pady=10, expand=True)
        #container = tk.Frame(self)
        tab1 = tk.Frame(container, width=1920, height=1080)
        tab2 = tk.Frame(container, width=1920, height=1080)
        tab1.pack(fill='both', expand=True)
        tab2.pack(fill='both', expand=True)
        container.add(tab1, text ='Notebook tab 1')
        container.add(tab2, text ='Notebook tab 2')
        container.pack(expand = 1, fill ="both")
        #StartPage(container,controller=self, master=self)
        #graphPage(container,controller=self, master=self)
        """
        self.frames = {}
        self.frames2 = {}
        self.frames3 = {}
        self.frames4 = {}
        self.frames5 = {}
        data = ["StartPage", "graphPage"]
        data2 = ["StartPage", "graphPage"]
        loop = 0
        for F in (StartPage, graphPage):
            frame = F(parent=tab1, controller=self, master=tab1)
            self.frames[data[loop]] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
            frame2 = F(parent=tab2, controller=self, master=tab2)
            self.frames2[data2[loop]] = frame2
            frame2.grid(row=0, column=0, sticky="nsew")

            frame3 = F(parent=tab3, controller=self, master=tab3)
            self.frames3[data2[loop]] = frame3
            frame3.grid(row=0, column=0, sticky="nsew")

            frame4 = F(parent=tab4, controller=self, master=tab4)
            self.frames4[data2[loop]] = frame4
            frame4.grid(row=0, column=0, sticky="nsew")

            frame5 = F(parent=tab5, controller=self, master=tab5)
            self.frames5[data2[loop]] = frame5
            frame5.grid(row=0, column=0, sticky="nsew")
            loop += 1
        #self.show_frame("StartPage")
        
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

        # Photo Widget for Start Page
        '''
         # TODO remove picture and add either:
         # Empty canvas
         # Pre-populated canvas
        '''
        img = tk.PhotoImage(file='images/cubic_graph.png')
        label = tk.Label(self, image=img)
        label.image = img
        label.grid(row=0, column=0, padx=(20,10), pady=(100,20))


 
class graphPage(tk.Frame):
    def __init__(self, parent, controller, master):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.begin_year = tkboot.StringVar(value="")
        self.end_year = tkboot.StringVar(value="")
        self.begin_date = tkboot.StringVar(value="")
        self.end_date = tkboot.StringVar(value="")
        self.n_degree = tkboot.StringVar(value="")

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

        def on_checkbox():
            return null

        #The data has been entered/ selected by the user. Here is it:
        def on_enter_data():

            [begin_month_num, begin_year] = self.begin_year.get().split('/')
            [end_month_num, end_year] = self.end_year.get().split('/')
            begin_month = month_dict[begin_month_num]
            end_month = month_dict[end_month_num]
            months = []
            for monthNum in range(int(begin_month_num), int(end_month_num)+1):
                month = str(monthNum).zfill(2)
                months.append(month_dict[month])

            #Coefficient Button
            self.button_coeff = TTK.Button(self.tab, width="15", text="View Coefficients", bootstyle="blue")
            self.button_coeff.grid(row=9, column=1, padx=(220,0), pady=(50, 0))

            self.button_coeff = TTK.Button(self.tab, width="16", text="Export data to CSV", bootstyle="blue")
            self.button_coeff.grid(row=9, column=1, padx=(537,0), pady=(50, 0))

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

            counties = list(chain(*counties))
            fig, x_data, y_data = plotting.plot(plot_type, df_list, {'process_type': process_type, 'double_plot_diff': double_plot_diff,
                                                     'plot_points': plot_points, 'connected_curve': connected_curve,
                                                     'begin_month': monthsIdx[begin_month], 'end_month': monthsIdx[end_month],
                                                     'degree': polynomial_degree, 'deriv_degree': derivitive_degree,
                                                     'plots_per_graph' : len(df_list), 'names' : counties})
            canvas = FigureCanvasTkAgg(fig, master = master)  
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, pady=(50, 0), padx=(10, 600))

            #print("\nHere is the data that the user entered: ")
            #print("Begin date month: ")
            #print(begin_month)
            #print("Begin date year: ")
            #print(begin_year)
            #print("End date month: ")
            #print(end_month)
            #print("End date year: ")
            #print(end_year)
            #print("Polynomial degree: ")
            #print(polynomial_degree)
            #print("Data type to plot: ")
            #print(data_type)
            #print("Counties: ")
            #print(counties)
            #print("States: ")
            #print(states)
            #print("County codes: ")
            #print(county_codes)
            #print("Countries: ")
            #print(countries)
            
        def gen_plot_type(event=None):
            self.ent3 = None
            if event.widget.get() == 'Yearly Offset':
                self.ent3 = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                self.ent3.grid(row=6, column=1, padx=(240,0), pady=(30,0))
                year_offset = tk.Label(self.tab, font="10", text="Year Diff: ")
                year_offset.grid(row=6, column=1, padx=(100, 0), pady=(30,0))

        def gen_equation(event=None):
            self.ent = None
            self.ent2 = None
            if event == None:
                degree = ''
            else:
                if event.widget.get() == "n-degree..":
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=7, column=1, padx=(240,0), pady=(30,0))
                    degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    degree_label.grid(row=7, column=1, padx=(100, 0), pady=(30,0))
                elif event.widget.get() == 'n-degree derivative':
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=7, column=1, padx=(240,0), pady=(30,0))
                    degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    degree_label.grid(row=7, column=1, padx=(100, 0), pady=(30,0))
                    self.ent2 = tkboot.Entry(self.tab, width="6")
                    self.ent2.grid(row=8, column=1, padx=(240,0), pady=(0,80))
                    deriv_label = tk.Label(self.tab, font="10", text="Derivitive: ")
                    deriv_label.grid(row=8, column=1, padx=(100, 0), pady=(0,80))
                elif event.widget.get() == "Connected-Curve":
                    self.ent = tkboot.Entry(self.tab, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=7, column=1, padx=(240,0), pady=(30,0))
                    degree_label = tk.Label(self.tab, font="10", text="Degree: ")
                    degree_label.grid(row=7, column=1, padx=(100, 0), pady=(30,0))
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
            selected_item = self.data_table.selection()[0]
            self.data_table.delete(selected_item)
            

        def gen_counties(event=None):
            if event == None:
                state = ''
            else:
                state = event.widget.get()
            data = get_counties_for_state(state)

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
            if county_name == 'All Counties':
                data = get_counties_for_state_all_data(state)
            else:
                data = get_selected_counties_for_state(state, county_name)
            print("Your query returned this data: ")
            print(data)
            for row in data:
                print(row)
                self.data_table.insert(parent='', index='end', values=row)
            self.data_table.grid(row=2, column=1, pady=(0,40), padx=(250, 235))

        def widgets(frame):
            self.tab = tk.Frame(frame, width=1920, height=1080)
            #print(tabs[values])
            #loop[count] = tk.Frame(frame, width=1920, height=1080)
            #Notebook   
            self.notebook_label = tk.Label(self.tab, font="12", text="Notebook:")
            self.notebook_label.grid(row=1, column=0, padx=(10, 500), pady=10)

            #Date range widgets
            self.begin_date_ent = tkboot.Entry(self.tab, textvariable=self.begin_year, width=10)
            self.begin_date_ent.grid(row=4, column=1, padx=(40,0), pady=(0,0))

            self.end_date_ent = tkboot.Entry(self.tab, textvariable=self.end_year, width=10)
            self.end_date_ent.grid(row=5, column=1, padx=(40, 0), pady=(0,0))

            self.begin_date_label = tkboot.Label(self.tab, font="10", text="Date range begin: ", bootstyle="inverse-dark")
            self.begin_date_label.grid(row=4, column=1, padx=(0, 250), pady=(0,0))        

            self.end_date_label = tkboot.Label(self.tab, font="10", text="Date range end: ", bootstyle="inverse-dark")

            """
            self.end_date_label.grid(row=5, column=1, padx=(0, 265), pady=(0,0))
            self.specific_months = TTK.Combobox(self.tab, font="Helvetica 12")
            self.specific_months.set('Select months')
            self.specific_months['state'] = 'readonly'
            self.specific_months['values'] = ('All months', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December') 
            self.specific_months.bind('<<ComboboxSelected>>', gen_specific_date_table) 
            self.specific_months.grid(row=5, column=1, padx=(400, 0))
            """
            

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

            delete_btn = tkboot.Button(self.tab, text="Delete row", command=delete_from_table)
            delete_btn.grid(row=2, column=1, padx=(550,0), pady=(0,160))

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
            self.dropdown_state['values'] = (['AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY'])
            self.dropdown_state.bind('<<ComboboxSelected>>', gen_counties)
            self.dropdown_state.grid(row=1, column=1, padx=(0, 190), pady=(20, 20))

            # Initialize Counties Dropdown Widget
            self.dropdown_county = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_county.set('Select county...')
            self.dropdown_county['state'] = 'readonly'
            self.dropdown_county.bind('<<ComboboxSelected>>', gen_table)
            self.dropdown_county.grid(row=1, column=1, padx=(290, 0), pady=(20, 20))

            #Home button
            self.button_back = TTK.Button(self.tab, width="15", text="Back to home", bootstyle="blue", command=lambda: controller.show_frame("StartPage"))
            self.button_back.grid(row=0, column=1, padx=(0,250), pady=(100, 10))

            #Add instance to notebook button
            self.button_notebook_add = TTK.Button(self.tab, width="25", text="Add instance to notebook", bootstyle="blue")
            self.button_notebook_add.grid(row=0, column=0, padx=(10,580), pady=(50, 20))

            #Dropdown for datatype selection
            self.plot_type = TTK.Combobox(self.tab, font="Helvetica 12")
            self.plot_type.set('Select data type...')
            self.plot_type['state'] = 'readonly'
            self.plot_type['values'] = ['Line', 'Yearly Offset']
            self.plot_type.bind('<<ComboboxSelected>>', gen_plot_type)
            self.plot_type.grid(row=6, column=1,  padx=(0, 190), pady=(30, 0))

            #Dropdown Widget for equation selection
            self.dropdown_equations = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_equations.set('Select equation...')
            self.dropdown_equations['state'] = 'readonly'
            self.dropdown_equations['values'] = ['Connected', 'Connected-Curve', 'Linear', 
                                                 'Quadratic', 'Cubic', 'n-degree..', 'n-degree derivative']
            self.dropdown_equations.bind('<<ComboboxSelected>>', gen_equation)
            self.dropdown_equations.grid(row=7, column=1,  padx=(0, 190), pady=(30, 0))


            #Dropdown for datatype selection
            self.dropdown_graphs = TTK.Combobox(self.tab, font="Helvetica 12")
            self.dropdown_graphs.set('Select data type...')
            self.dropdown_graphs['state'] = 'readonly'
            self.dropdown_graphs['values'] = ["Minimum temperature", "Maximum temperature", "Average temperature", "Precipitation", "Palmer Drought Severity", "Palmer Hydrological Drought", "Modified Palmer Drought Severity", "1-month Standardized Precipitation", "2-month Standardized Precipitation", "3-month Standardized Precipitation", "6-month Standardized Precipitation", "9-month Standardized Precipitation", "12-month Standardized Precipitation", "24-month Standardized Precipitation"]
            self.dropdown_graphs.bind('<<ComboboxSelected>>', gen_datatype_columns)
            self.dropdown_graphs.grid(row=8, column=1,  padx=(0, 200), pady=(40, 0))
            datatypeTip = Hovertip(self.dropdown_graphs, 'Select which type of weather data to graph')


            #Button for submitting all that the user has entered
            self.data_submit = tkboot.Button(
                self.tab, 
                command=on_enter_data,
                width="25", 
                text="Graph it!", 
                bootstyle=DEFAULT
            )
            self.data_submit.grid(row=9, column=1, padx=(0,173), pady=(50,0))
            self.data_submit.focus_set()

            # Generate Table Rows
            gen_table()
            return self.tab


        frame = ttk.Notebook(self)
        frame.pack(fill='both', pady=10, expand=True)
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
        self.plot_points.grid(row=4, column=1,  padx=(650, 0), pady=(0, 0))
        scatterTip = Hovertip(self.plot_points, 'Check to enable scatter plotting on graph')

        
# WIDGETS ----------------------------------------------------------------------------       
        
def start_ui():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    start_ui()
