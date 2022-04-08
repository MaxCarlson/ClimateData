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
    "Precipitation"       : "precip"
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

# Helper Functions --------------------------------------------------

def validate_dates(start, end):

    #check that date is in correct format (month/year)
    if bool(re.match("\d+\/\d+", start)) == False or bool(re.match("\d+\/\d+", end)) == False: 
        return False
   
    [begin_month, begin_year] = start.split('/')
    [end_month, end_year] = end.split('/')

    #check that years are four digits 
    if len(begin_year) != 4 or len(end_year) != 4:
        return False

    #check that first year occurs before second year
    if bool(begin_year < end_year) == False:
        return False

    return True


def validate_degree(degree):
   
    #check that the degree is a number 
    if bool(degree.isnumeric()) == False:
        return False

    return True


# Setup database connection
conn = psycopg2.connect("host=localhost dbname=postgres user=postgres password=PASSWORD")
cur = conn.cursor()

class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title('Climate Data')
        self.geometry('1920x1080')
        tkboot.Style('darkly')
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        container = ttk.Notebook(self)
        tab1 = tk.Frame(container, width=1920, height=1080)
        container.add(tab1, text ='Notebook tab 1')
        tab2 = tk.Frame(container, width=1920, height=1080)
        container.add(tab2, text ='Notebook tab 2')
        container.grid(row=0, column=0)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

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
        data = ["StartPage", "graphPage"]
        loop = 0
        for F in (StartPage, graphPage):
            frame = F(parent=tab1, controller=self, master=self)
            self.frames[data[loop]] = frame
            frame.grid(row=0, column=0, sticky="nsew")

            frame = F(parent=tab2, controller=self, master=self)
            self.frames[data[loop]] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            loop += 1
        self.show_frame("StartPage")
        
        #This code breaks the notebook ^^
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        print(frame,"This is the frame")
        frame.tkraise()
    
    
class StartPage(tk.Frame):
    def __init__(self, parent, controller, master):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        button1 = TTK.Button(self, text = "Graph", width="15", bootstyle="secondary", command=lambda: controller.show_frame("graphPage"))
        button2 = TTK.Button(self, text = "Map", width="15", bootstyle="secondary", command=lambda: controller.show_frame("mapPage"))
        button1.grid(row=0, column=1, padx=(450,0), pady=(100,500))
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

        self.begin_date = tkboot.StringVar(value="")
        self.end_date = tkboot.StringVar(value="")
        self.n_degree = tkboot.StringVar(value="")

# FUNCTIONS -----------------------------------------------------------------
        #called when submit button for date entry is used
        def on_submit():
            #user input is invalid, call validate_dates function
            if validate_dates(self.begin_date.get(), self.end_date.get()) == False:    
                tkboot.dialogs.Messagebox.show_error("Invalid date entry. \nEntry rules: \n- Entry must be in form: 'month/year' \n- Years must be in chronological order \n- Years must be four digits \n- Entry example: '06/1993'", title='Invalid date entry')

            else: 
                #user input is valid, parse it into two months and two years
                print("User entered this begin date: " + self.begin_date.get())
                print("User entered this ending date: " + self.end_date.get())
                print("parsing data into months/ years.....")
                [begin_month, begin_year] = self.begin_date.get().split('/')
                [end_month, end_year] = self.end_date.get().split('/')
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
            [begin_month, begin_year] = self.begin_date.get().split('/')
            [end_month, end_year] = self.end_date.get().split('/')
            begin_month = month_dict[begin_month]
            end_month = month_dict[end_month]
            
            polynomial_degree = degree_dict[self.dropdown_equations.get()] if self.ent == None else self.ent.get()
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
                    print("in if")
                    print(temp_dict[values[0]])
                else:
                    print("in else")
                    temp_dict[values[0]] = [values[1]]
                    print(temp_dict[values[0]])
            
            counties = []
            for key in temp_dict.keys():
                counties.append(temp_dict[key])

            monthsIdx = {'jan' : 0, 'feb' : 1, 'mar' : 2, 'apr': 3, 'may': 4, 'jun': 5, 
                         'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11}

            df_list = get_data_for_counties_dataset(states, counties, 'US', [data_type], begin_month, end_month, int(begin_year), int(end_year))

            counties = list(chain(*counties))
            fig = plotting.plot('scatter_poly', df_list, {'process_type': 'months', 'begin_month': monthsIdx[begin_month],
                                                          'degree': polynomial_degree, 'plots_per_graph' : len(df_list), 'counties' : counties})
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
            
        def gen_equation(event=None):
            if event == None:
                degree = ''
            else:
                if event.widget.get() == "n-degree..":
                    self.ent = tkboot.Entry(self.frame_right, width="6", textvariable=event.widget.get())
                    self.ent.grid(row=6, column=1, padx=(240,0), pady=(30,0))
                    degree_label = tk.Label(self.frame_right, font="10", text="Degree: ")
                    degree_label.grid(row=6, column=1, padx=(100, 0), pady=(30,0))
                    sub_btn = tkboot.Button(
                        self.frame_right,
                        text="Submit degree",
                        command=on_submit_degree,
                        bootstyle="blue",
                        width=12
                    )
                    sub_btn.grid(row=6, column=1, padx=(450, 0), pady=(30,0))
                    sub_btn.focus_set()
                else:
                    self.ent = None
                    degree = event.widget.get()
                    print("Degree of equation is: ")
                    print(degree_dict[degree])

        def gen_datatype_columns(event):
            print("User selected this data type: " + event.widget.get())
            print("parsing data type into correct format.... ")
            
            columns = event.widget.get()
            #Data type 'columns' for database function 'get_data_for_counties_dataset'
            print("Data type in correct format is: " + datatype_dict[columns])

        def gen_counties(event=None):
            if event == None:
                county_name = ''
            else:
                county_name = event.widget.get()
            cur.execute("""
            SELECT county_name FROM county_codes WHERE state = %s;
            """,
            [county_name])
            conn.commit()
            data = cur.fetchall()
            print("Your query returned this data: ")
            data = [ x[0] for x in data ]
            print(data)
            self.dropdown_county['values'] = data
            self.dropdown_county.grid(row=1, column=1, padx=(290, 0), pady=(0, 0))

        def gen_table(event=None):
            if event == None:
                county_name = ''
                state = ''
            else:
                county_name = event.widget.get()
                state = self.dropdown_state.get()
            #for child in self.data_table.get_children():
                #self.data_table.delete(child)
            cur.execute("""
            SELECT state, county_name, county_code, country FROM county_codes WHERE county_name = %s AND state = %s;
            """,
            [county_name, state])
            conn.commit()
            data = cur.fetchall()
            print("Your query returned this data: ")
            print(data)
            for row in data:
                self.data_table.insert(parent='', index='end', values=row)
            self.data_table.grid(row=2, column=1, pady=(0,40), padx=(250, 235))

        def widgets(frame):
            tab = tk.Frame(frame, width=1920, height=1080)
            #print(tabs[values])
            #loop[count] = tk.Frame(frame, width=1920, height=1080)
            #Notebook   
            self.notebook_label = tk.Label(tab, font="12", text="Notebook:")
            self.notebook_label.grid(row=1, column=0, padx=(10, 710), pady=0)

            #Date range widgets
            self.begin_date_ent = tkboot.Entry(tab, textvariable=self.begin_date)
            self.begin_date_ent.grid(row=4, column=1, padx=(100,0), pady=(0,0))

            self.end_date_ent = tkboot.Entry(tab, textvariable=self.end_date)
            self.end_date_ent.grid(row=5, column=1, padx=(100, 0), pady=(0,0))

            self.begin_date_label = tk.Label(tab, font="10", text="Date range begin: ")
            self.begin_date_label.grid(row=4, column=1, padx=(0, 250), pady=(0,0))        

            self.end_date_label = tk.Label(tab, font="10", text="Date range end: ")
            self.end_date_label.grid(row=5, column=1, padx=(0, 265), pady=(0,0))

            self.sub_btn = tkboot.Button(
                tab,
                text="Submit dates",
                command=on_submit,
                bootstyle="blue",
                width=12,
            )
            self.sub_btn.grid(row=5, column=1, padx=(450, 0), pady=(0,0))
            self.sub_btn.focus_set()
            

            # Initialize Table Widget
            self.data_table = TTK.Treeview(tab)
            self.data_table['columns'] = ('state', 'county_name', 'county_code', 'country')
            self.data_table.column('#0', width=0, stretch=tk.NO)
            self.data_table.column('state', width=110)
            self.data_table.column('county_name', width=110)
            self.data_table.column('county_code', width=110)
            self.data_table.column('country', width=80)
            self.data_table.heading('#0', text="", anchor=tk.CENTER)
            self.data_table.heading('state', text="State")
            self.data_table.heading('county_name', text="County Name")
            self.data_table.heading('county_code', text="County Code")
            self.data_table.heading('country', text="Country")

            # Initialize State Dropdown Widget
            self.dropdown_state = TTK.Combobox(tab, font="Helvetica 12")
            self.dropdown_state.set('Select state...')
            self.dropdown_state['state'] = 'readonly'
            self.dropdown_state['values'] = (['AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY'])
            self.dropdown_state.bind('<<ComboboxSelected>>', gen_counties)
            self.dropdown_state.grid(row=1, column=1, padx=(0, 190), pady=(20, 20))

            # Initialize Counties Dropdown Widget
            self.dropdown_county = TTK.Combobox(tab, font="Helvetica 12")
            self.dropdown_county.set('Select county...')
            self.dropdown_county['state'] = 'readonly'
            self.dropdown_county.bind('<<ComboboxSelected>>', gen_table)
            self.dropdown_county.grid(row=1, column=1, padx=(290, 0), pady=(20, 20))

            #Home button
            self.button_back = TTK.Button(tab, width="15", text="Back to home", bootstyle="blue", command=lambda: controller.show_frame("StartPage"))
            self.button_back.grid(row=0, column=1, padx=(0,250), pady=(100, 10))

            #Add instance to notebook button
            #self.button_notebook_add = TTK.Button(tab1, width="25", text="Add instance to notebook", bootstyle="blue")
            #self.button_notebook_add.grid(row=0, column=0, padx=(10,580), pady=(50, 20))

            #Dropdown Widget for equation selection
            self.dropdown_equations = TTK.Combobox(tab, font="Helvetica 12")
            self.dropdown_equations.set('Select equation...')
            self.dropdown_equations['state'] = 'readonly'
            self.dropdown_equations['values'] = ['Linear', 'Quadratic', 'Cubic', 'n-degree..']
            self.dropdown_equations.bind('<<ComboboxSelected>>', gen_equation)
            self.dropdown_equations.grid(row=6, column=1,  padx=(0, 190), pady=(30, 0))


            #Dropdown for datatype selection
            self.dropdown_graphs = TTK.Combobox(tab, font="Helvetica 12")
            self.dropdown_graphs.set('Select data type...')
            self.dropdown_graphs['state'] = 'readonly'
            self.dropdown_graphs['values'] = ["Minimum temperature", "Maximum temperature", "Average temperature", "Precipitation"]
            self.dropdown_graphs.bind('<<ComboboxSelected>>', gen_datatype_columns)
            self.dropdown_graphs.grid(row=7, column=1,  padx=(0, 190), pady=(30, 0))


            #Button for submitting all that the user has entered
            self.data_submit = tkboot.Button(
                tab, 
                command=on_enter_data,
                width="25", 
                text="Graph it!", 
                bootstyle=SUCCESS
            )
            self.data_submit.grid(row=8, column=1, padx=(0,173), pady=(150,0))
            self.data_submit.focus_set()

            # Generate Table Rows
            gen_table()
            return tab

        

        frame = ttk.Notebook(self)
        frame.pack(fill='both', pady=10, expand=True)
        tabs = ["Notebook1", "Notebook2", "Notebook3", "Notebook4"]
        #tab1 = tk.Frame(frame, width=1920, height=1080)
        tab1 = widgets(frame)
        frame.add(tab1, text = "Main")
        
# WIDGETS ----------------------------------------------------------------------------       
        
def start_ui():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    start_ui()






"""
        #second tab ---------------------------------------------------------------------------------------------------------------------------->
        self.notebook_label = tk.Label(tab2, font="12", text="Notebook: ")
        self.notebook_label.grid(row=1, column=0, padx=(10, 710), pady=(0,10))

        #Date range widgets
        self.begin_date_ent = tkboot.Entry(tab2, textvariable=self.begin_date)
        self.begin_date_ent.grid(row=4, column=1, padx=(100,0), pady=(0,0))

        self.end_date_ent = tkboot.Entry(tab2, textvariable=self.end_date)
        self.end_date_ent.grid(row=5, column=1, padx=(100, 0), pady=(0,0))

        self.begin_date_label = tk.Label(tab2, font="10", text="Date range begin: ")
        self.begin_date_label.grid(row=4, column=1, padx=(0, 250), pady=(0,0))        

        self.end_date_label = tk.Label(tab2, font="10", text="Date range end: ")
        self.end_date_label.grid(row=5, column=1, padx=(0, 265), pady=(0,0))

        self.sub_btn = tkboot.Button(
            tab2,
            text="Submit dates",
            command=on_submit,
            bootstyle="blue",
            width=12,
        )
        self.sub_btn.grid(row=5, column=1, padx=(450, 0), pady=(0,0))
        self.sub_btn.focus_set()
        

        # Initialize Table Widget
        self.data_table = TTK.Treeview(tab2)
        self.data_table['columns'] = ('state', 'county_name', 'county_code', 'country')
        self.data_table.column('#0', width=0, stretch=tk.NO)
        self.data_table.column('state', width=110)
        self.data_table.column('county_name', width=110)
        self.data_table.column('county_code', width=110)
        self.data_table.column('country', width=80)
        self.data_table.heading('#0', text="", anchor=tk.CENTER)
        self.data_table.heading('state', text="State")
        self.data_table.heading('county_name', text="County Name")
        self.data_table.heading('county_code', text="County Code")
        self.data_table.heading('country', text="Country")

        # Initialize State Dropdown Widget
        self.dropdown_state = TTK.Combobox(tab2, font="Helvetica 12")
        self.dropdown_state.set('Select state...')
        self.dropdown_state['state'] = 'readonly'
        self.dropdown_state['values'] = (['AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY'])
        self.dropdown_state.bind('<<ComboboxSelected>>', gen_counties)
        self.dropdown_state.grid(row=1, column=1, padx=(0, 190), pady=(20, 20))

        # Initialize Counties Dropdown Widget
        self.dropdown_county = TTK.Combobox(tab2, font="Helvetica 12")
        self.dropdown_county.set('Select county...')
        self.dropdown_county['state'] = 'readonly'
        self.dropdown_county.bind('<<ComboboxSelected>>', gen_table)
        self.dropdown_county.grid(row=1, column=1, padx=(290, 0), pady=(20, 20))

        #Home button
        self.button_back = TTK.Button(tab2, width="15", text="Back to home", bootstyle="blue", command=lambda: controller.show_frame("StartPage"))
        self.button_back.grid(row=0, column=1, padx=(0,250), pady=(100, 10))

        #Add instance to notebook button
        self.button_notebook_add = TTK.Button(tab2, width="25", text="Add instance to notebook", bootstyle="blue")
        self.button_notebook_add.grid(row=0, column=0, padx=(10,580), pady=(50, 20))

        #Dropdown Widget for equation selection
        self.dropdown_equations = TTK.Combobox(tab2, font="Helvetica 12")
        self.dropdown_equations.set('Select equation...')
        self.dropdown_equations['state'] = 'readonly'
        self.dropdown_equations['values'] = ['Linear', 'Quadratic', 'Cubic', 'n-degree..']
        self.dropdown_equations.bind('<<ComboboxSelected>>', gen_equation)
        self.dropdown_equations.grid(row=6, column=1,  padx=(0, 190), pady=(30, 0))


        #Dropdown for datatype selection
        self.dropdown_graphs = TTK.Combobox(tab2, font="Helvetica 12")
        self.dropdown_graphs.set('Select data type...')
        self.dropdown_graphs['state'] = 'readonly'
        self.dropdown_graphs['values'] = ["Minimum temperature", "Maximum temperature", "Average temperature", "Precipitation"]
        self.dropdown_graphs.bind('<<ComboboxSelected>>', gen_datatype_columns)
        self.dropdown_graphs.grid(row=7, column=1,  padx=(0, 190), pady=(30, 0))


        #Button for submitting all that the user has entered
        self.data_submit = tkboot.Button(
            tab2, 
            command=on_enter_data,
            width="25", 
            text="Graph it!", 
            bootstyle=SUCCESS
        )
        self.data_submit.grid(row=8, column=1, padx=(0,173), pady=(150,0))
        self.data_submit.focus_set()
"""





"""
        # Frame
        frame = ttk.Notebook(self)
        frame.pack(pady=10, expand=True)
        #container = tk.Frame(self)
        #tab1 = tk.Frame(frame, width=1920, height=1080)
        #tab2 = tk.Frame(frame, width=1920, height=1080)
        #tab1.pack(fill='both', expand=True)
        #tab2.pack(fill='both', expand=True)
        #frame.add(tab1, text ='Notebook tab 1')
        #frame.add(tab2, text ='Notebook tab 2')
        #frame.pack(expand = 1, fill ="both")
        frame = tk.Frame(self)
        frame.grid(row=0, sticky="nw")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)            
        frame.grid_columnconfigure(2, weight=1)
        frame.grid_columnconfigure(3, weight=1)
        tabs = ["Notebook1", "Notebook2", "Notebook3", "Notebook4"]
        tab = tk.Frame(frame, width=1920, height=1080)
        tab2 = tk.Frame(frame, width=1920, height=1080)
        tab3 = tk.Frame(frame, width=1920, height=1080)
        tab4 = tk.Frame(frame, width=1920, height=1080)
        loop = {"Notebook1": tab, "Notebook2":tab2, "Notebook3":tab3, "Notebook4":tab4}
        count = 0 
        size = len(tabs)
        for values in range(size):
            print(loop[tabs[count]], "This is the data <--->")
            #print(tabs[values])
            #loop[count] = tk.Frame(frame, width=1920, height=1080)
            frame.add(loop[tabs[count]], text =tabs[values])
            #Notebook   
            self.notebook_label = tk.Label(loop[tabs[count]], font="12", text=tabs[values]+":")
            self.notebook_label.grid(row=1, column=0, padx=(10, 710), pady=0)

            #Date range widgets
            self.begin_date_ent = tkboot.Entry(loop[tabs[count]], textvariable=self.begin_date)
            self.begin_date_ent.grid(row=4, column=1, padx=(100,0), pady=(0,0))

            self.end_date_ent = tkboot.Entry(loop[tabs[count]], textvariable=self.end_date)
            self.end_date_ent.grid(row=5, column=1, padx=(100, 0), pady=(0,0))

            self.begin_date_label = tk.Label(loop[tabs[count]], font="10", text="Date range begin: ")
            self.begin_date_label.grid(row=4, column=1, padx=(0, 250), pady=(0,0))        

            self.end_date_label = tk.Label(loop[tabs[count]], font="10", text="Date range end: ")
            self.end_date_label.grid(row=5, column=1, padx=(0, 265), pady=(0,0))

            self.sub_btn = tkboot.Button(
                loop[tabs[count]],
                text="Submit dates",
                command=on_submit,
                bootstyle="blue",
                width=12,
            )
            self.sub_btn.grid(row=5, column=1, padx=(450, 0), pady=(0,0))
            self.sub_btn.focus_set()
            

            # Initialize Table Widget
            self.data_table = TTK.Treeview(loop[tabs[count]])
            self.data_table['columns'] = ('state', 'county_name', 'county_code', 'country')
            self.data_table.column('#0', width=0, stretch=tk.NO)
            self.data_table.column('state', width=110)
            self.data_table.column('county_name', width=110)
            self.data_table.column('county_code', width=110)
            self.data_table.column('country', width=80)
            self.data_table.heading('#0', text="", anchor=tk.CENTER)
            self.data_table.heading('state', text="State")
            self.data_table.heading('county_name', text="County Name")
            self.data_table.heading('county_code', text="County Code")
            self.data_table.heading('country', text="Country")

            # Initialize State Dropdown Widget
            self.dropdown_state = TTK.Combobox(loop[tabs[count]], font="Helvetica 12")
            self.dropdown_state.set('Select state...')
            self.dropdown_state['state'] = 'readonly'
            self.dropdown_state['values'] = (['AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY'])
            self.dropdown_state.bind('<<ComboboxSelected>>', gen_counties)
            self.dropdown_state.grid(row=1, column=1, padx=(0, 190), pady=(20, 20))

            # Initialize Counties Dropdown Widget
            self.dropdown_county = TTK.Combobox(loop[tabs[count]], font="Helvetica 12")
            self.dropdown_county.set('Select county...')
            self.dropdown_county['state'] = 'readonly'
            self.dropdown_county.bind('<<ComboboxSelected>>', gen_table)
            self.dropdown_county.grid(row=1, column=1, padx=(290, 0), pady=(20, 20))

            #Home button
            self.button_back = TTK.Button(loop[tabs[count]], width="15", text="Back to home", bootstyle="blue", command=lambda: controller.show_frame("StartPage"))
            self.button_back.grid(row=0, column=1, padx=(0,250), pady=(100, 10))

            #Add instance to notebook button
            #self.button_notebook_add = TTK.Button(tab1, width="25", text="Add instance to notebook", bootstyle="blue")
            #self.button_notebook_add.grid(row=0, column=0, padx=(10,580), pady=(50, 20))

            #Dropdown Widget for equation selection
            self.dropdown_equations = TTK.Combobox(loop[tabs[count]], font="Helvetica 12")
            self.dropdown_equations.set('Select equation...')
            self.dropdown_equations['state'] = 'readonly'
            self.dropdown_equations['values'] = ['Linear', 'Quadratic', 'Cubic', 'n-degree..']
            self.dropdown_equations.bind('<<ComboboxSelected>>', gen_equation)
            self.dropdown_equations.grid(row=6, column=1,  padx=(0, 190), pady=(30, 0))


            #Dropdown for datatype selection
            self.dropdown_graphs = TTK.Combobox(loop[tabs[count]], font="Helvetica 12")
            self.dropdown_graphs.set('Select data type...')
            self.dropdown_graphs['state'] = 'readonly'
            self.dropdown_graphs['values'] = ["Minimum temperature", "Maximum temperature", "Average temperature", "Precipitation"]
            self.dropdown_graphs.bind('<<ComboboxSelected>>', gen_datatype_columns)
            self.dropdown_graphs.grid(row=7, column=1,  padx=(0, 190), pady=(30, 0))


            #Button for submitting all that the user has entered
            self.data_submit = tkboot.Button(
                loop[tabs[count]], 
                command=on_enter_data,
                width="25", 
                text="Graph it!", 
                bootstyle=SUCCESS
            )
            self.data_submit.grid(row=8, column=1, padx=(0,173), pady=(150,0))
            self.data_submit.focus_set()

            # Generate Table Rows
            gen_table()
            count += 1

"""
