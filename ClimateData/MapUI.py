import pandas as pd                             #pip install pandas
import plotly.express as px                     #pip install plotly   
import psycopg2                                 #pip install psycopg2-binary
import json
from urllib.request import urlopen
from PyQt5.QtWidgets import *                   #pip install PyQt5
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *          #pip install PyQtWebEngine
import database
import os
import config
from datetime import date

datatype_dict = {
    "Maximum Temperature" : "tmp_max",
    "Minimum Temperature" : "tmp_min",
    "Average Temperature" : "tmp_avg",
    "Precipitation"       : "precip",
    "Select Data Type..." : "",
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

state_dict = {
    "AL" : [], "AK" : [], "AZ" : [], "AR" : [], "AS" : [], "CA" : [], "CO" : [], "CT" : [],
    "DE" : [], "DC" : [], "FL" : [], "GA" : [], "GU" : [], "HI" : [], "ID" : [], "IL" : [],
    "IN" : [], "IA" : [], "KS" : [], "KY" : [], "LA" : [], "ME" : [], "MD" : [], "MA" : [],
    "MI" : [], "MN" : [], "MS" : [], "MO" : [], "MT" : [], "NE" : [], "NV" : [], "NH" : [],
    "NJ" : [], "NM" : [], "NY" : [], "NC" : [], "ND" : [], "OH" : [], "OK" : [], "OR" : [],
    "PA" : [], "RI" : [], "SC" : [], "SD" : [], "TN" : [], "TX" : [], "UT" : [], "VT" : [], 
    "VA" : [], "VI" : [], "WA" : [], "WV" : [], "WI" : [], "WY" : []
}


class MapWindow(QWindow):

  def __init__(self, pdDF, *args, **kwargs):
    self.conn = psycopg2.connect(config.config_get_db_connection_string())
    self.cur = self.conn.cursor()
    super(MapWindow, self).__init__(*args, **kwargs)
    path = QDir.current().filePath('HTML/map_fig.html')
    self.pdDF = pdDF
    self.lines = []
    self.state_boxes = []
    self.county_boxes = []
    self.date_boxes = []
    self.curr_month = None
    self.curr_year = None
    self.dataType = ''
    self.window = QWidget()
    self.layout = QVBoxLayout()
    self.navbar = QHBoxLayout()
    self.controls = QHBoxLayout()
    self.selection = QHBoxLayout()
    self.echo = QHBoxLayout()
    self.mapFig = None
    self.df = None
    self.genMapFlag = False

    #Map Controls
    self.yearSlider = QSlider(Qt.Horizontal)
    self.yearSliderBox = QLineEdit()
    self.yearSlider.setMinimum(1895)
    self.yearSlider.setMaximum(date.today().year)
    self.yearSlider.valueChanged.connect(self.yearSlideValChange)
    self.yearSliderBox.returnPressed.connect(self.yearSlideBoxChange)
    self.month_list = QComboBox()
    self.month_list.addItems(['Select month...', 'January','February','March','April','May','June','July','August','September','October','November','December'])
    self.month_list.setMinimumWidth(200)
    self.month_list.currentIndexChanged.connect(self.month_list_change)
    self.addButton = QPushButton('+', self.window)
    self.addButton.setMinimumHeight(30)
    self.addButton.setMaximumWidth(40)
    self.addButton.clicked.connect(self.addYear)
    self.deleteButton = QPushButton('Remove')
    self.deleteButton.setMinimumHeight(20)
    self.deleteButton.setMaximumWidth(80)
    self.deleteButton.clicked.connect(self.remove_selected)
    self.mapItButton = QPushButton('Map it!', self.window)
    self.mapItButton.setMinimumHeight(30)
    self.mapItButton.setMaximumWidth(150)
    self.mapItButton.clicked.connect(self.genMap)
    self.yearSliderBox.setStyleSheet('background-color: #2F2F2F; color: white;')
    self.month_list.setStyleSheet('background-color: #555555; color: white;')
    self.mapItButton.setStyleSheet('background-color: #375A7F; color: white;')
    self.addButton.setStyleSheet('background-color: #375A7F; color: white;')
    self.deleteButton.setStyleSheet('background-color: #375A7F; color: white;')
    self.yearSlider.setStyleSheet('QSlider::handle:horizontal {background-color: #375a7f;}')
    self.controls.addWidget(self.mapItButton)
    self.controls.addWidget(self.month_list)
    self.controls.addWidget(self.yearSlider)
    self.controls.addWidget(self.yearSliderBox)
    self.controls.addWidget(self.addButton)
    
    #State/County Selection
    self.state_list = QComboBox()
    self.state_list.addItems(['Select State...', 'AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA', 'HI', 'IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY'])
    self.state_list.currentIndexChanged.connect(self.state_list_change)
    self.county_list = QComboBox()
    self.county_list.addItem('Select County...')
    self.county_list.activated.connect(self.county_list_change)
    self.dataType_list = QComboBox()
    self.dataType_list.addItems(['Select Data Type...', 'Maximum Temperature', 'Minimum Temperature', 'Average Temperature', 'Precipitation'])
    self.dataType_list.activated.connect(self.dataType_list_change)
    self.state_list.setStyleSheet('background-color: #555555; color: white;')
    self.county_list.setStyleSheet('background-color: #555555; color: white;')
    self.dataType_list.setStyleSheet('background-color: #555555; color: white;')
    self.selection.addWidget(self.state_list)
    self.selection.addWidget(self.county_list)
    self.selection.addWidget(self.dataType_list)


    #Data table
    self.data_tree = QTreeView()
    self.data_table = QStandardItemModel(0,4)
    self.data_table.setHeaderData(0, Qt.Horizontal, "State")
    self.data_table.setHeaderData(1, Qt.Horizontal, "County Name")
    self.data_table.setHeaderData(2, Qt.Horizontal, "Country")
    self.data_table.setHeaderData(3, Qt.Horizontal, "Data")
    self.data_tree.setModel(self.data_table)
    self.data_tree.setMaximumHeight(200)
    self.data_tree.setStyleSheet('background-color: #2F2F2F; color: white;')
    self.echo.addWidget(self.data_tree)
    self.echo.addWidget(self.deleteButton)

    #Set title and add widgets and layouts to main window. 
    self.window.setWindowTitle("Climate Data")
    self.browser = QWebEngineView()
    self.openDefaultMap()
    self.layout.addWidget(self.browser)
    self.layout.addLayout(self.controls)
    self.layout.addLayout(self.selection)
    self.layout.addLayout(self.echo)
    self.layout.addLayout(self.navbar)
    self.window.setLayout(self.layout)
    self.window.setStyleSheet('background-color: #222222;')
    self.window.show()

  def fill_data(self):
    model = self.data_tree.model()
    count = model.rowCount(self.data_tree.rootIndex())
    states = self.df['state'].tolist()
    counties = self.df['county_name'].tolist()
    dlist = self.df[self.dataType+"_"+self.curr_month].tolist()
    
    for idx in range(count):
      model.setData(model.index(idx,0), states[idx])
      model.setData(model.index(idx,1), counties[idx])
      model.setData(model.index(idx,3), dlist[idx])
    
  def get_selected(self):
    model = self.data_tree.model()
    index = self.data_tree.selectedIndexes()
    state = model.data(index[0])
    county = model.data(index[1])
    return(state, county)

  def remove_selected(self):
    try:
        state, county = self.get_selected()
        for c in state_dict[state]:
          if c[0] == county:
            state_dict[state].remove(c)

        model = self.data_tree.model()
        indices = self.data_tree.selectionModel().selectedRows()
        for idx in sorted(indices):
          model.removeRow(idx.row())
        self.update_map()
    except:
      print('error removing line')
      return
    

  def county_list_change(self):
    # self.state_boxes.append(self.state_list.currentText())
    # self.county_boxes.append(self.county_list.currentText())
    model = self.data_tree.model()
    county = self.county_list.currentText()
    state = self.state_list.currentText()

    match = 0
    for countyList in state_dict[state]:
        for item in countyList:
            if item == county:
                match = 1

    if match == 0:
        model.insertRow(0)
        model.setData(model.index(0, 0), state)
        model.setData(model.index(0, 1), county)
        model.setData(model.index(0, 2), "US")
        state_dict[state].append([county])
    print(model.data(model.index(0,0)))
  #Builds State/County lists for genMap
  def build_lists(self):
    self.state_boxes = []
    self.county_boxes = []
    counties = []
    for state in state_dict:
      if state_dict[state]:
        self.state_boxes.append(state)
    
    for state in self.state_boxes:
      for county in state_dict[state]:
        counties.append(county[0])
      self.county_boxes.append(counties)
      counties = []

  #Month List Change
  def month_list_change(self):
    monthDict = {
    "January" : "jan",
    "February" : "feb",
    "March" : "mar",
    "April" : "apr",
    "May" : "may",
    "June" : "jun",
    "July" : "jul",
    "August" : "aug",
    "September" : "sep",
    "October" : "oct",
    "November" : "nov",
    "December" : "dec"
    }
    self.curr_month = monthDict[self.month_list.currentText()]
    print(self.curr_month)
  #State List Change
  def state_list_change(self):
    self.county_list.clear()
    self.county_list.addItem('Select County...')
    data = database.get_counties_for_state(self.state_list.currentText())
    data = [x[0] for x in data]
    self.county_list.addItems(data)
    self.state_boxes.append(self.state_list.currentText())
    print(self.state_boxes)
  def dataType_list_change(self):
    self.dataType = datatype_dict[self.dataType_list.currentText()]
    print(self.dataType)
  #Displays slider value
  def yearSlideBoxChange(self):
    self.yearSlider.setValue(int(self.yearSliderBox.text()))
    self.curr_year = int(self.yearSlider.value())
    print(self.curr_year)
  #Changes slider value
  def yearSlideValChange(self):
    self.yearSliderBox.setText(str(self.yearSlider.value()))
    self.curr_year = int(self.yearSliderBox.text())
    print(self.curr_year)
  def monthSlideBoxChange(self):
    self.monthSlider.setValue(int(self.monthSliderBox.text()))
  #Changes slider value
  def monthSlideValChange(self):
    # self.monthSliderBox.setText(monthDict[str(self.monthSlider.value())])
    return

  #Generates the map using pandas dataframe
  def genMap(self):
    self.build_lists()
    print(self.state_boxes)
    if self.curr_month == None:
      print("A month must be selected!")
      return
    if self.curr_year == None:
      print("A year must be selected!")
      return
    if self.dataType == '':
      print("You must select a data type!")
      return  
    if not self.state_boxes:
      self.state_boxes = ['AK','AL','AR','AZ','CA','CO','CT','DE','FL','GA','IA','ID','IL','IN','KS','KY','LA','MA','MD','ME','MI','MN','MO','MS','MT','NC','ND','NE','NH','NJ','NM','NV','NY','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VA','VT','WA','WI','WV','WY']
    if not self.county_boxes:
      self.df = database.get_map_data_for_states(self.state_boxes, 'US', [self.dataType], [self.curr_month], self.curr_year, self.curr_year)
    else:
      self.df = database.get_map_data_for_counties(self.state_boxes, self.county_boxes, 'US', [self.dataType], [self.curr_month], self.curr_year, self.curr_year)
    print(self.df)
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
      counties = json.load(response)
    
    colorscale = 'jet'
    range = (10,130)

    if self.dataType == 'precip':
      colorscale = 'dense'
      range = (0,15)
    self.mapFig = px.choropleth(self.df, geojson=counties, locations='fips_code', color=self.dataType+"_"+self.curr_month, color_continuous_scale=colorscale, range_color=range, scope='usa', hover_name='county_name', hover_data=['state'])
    self.mapFig.update_layout(title=dict(text='Climate Data'), margin=dict(l=0,r=0,b=0))
    self.mapFig.update_geos(resolution=50)
    self.mapFig.update_traces(name='Data', selector=dict(type='choropleth'))
    if not state_dict['AK']:
      self.mapFig.update_geos(fitbounds='locations', visible=True) 
      
    self.mapFig.write_html('HTML/map_fig.html')
    self.browser.setUrl(QUrl.fromLocalFile(os.path.abspath('HTML/map_fig.html')))
    self.genMapFlag = True
    self.fill_data()

  #Used to open blank map of US
  def openDefaultMap(self): 
      self.browser.setUrl(QUrl.fromLocalFile(os.path.abspath('HTML/default_fig.html')))

  #Button control for adding a new line
  def addYear(self):
    if self.genMapFlag == False:
      return 
    self.yearSlider.setValue(int(self.yearSliderBox.text())+1)
    self.update_map()
    self.fill_data()
 
  def update_map(self):
    self.build_lists()
    if len(self.state_boxes) == 0:
      self.browser.setUrl(QUrl.fromLocalFile(os.path.abspath('HTML/default_fig.html')))
      return
    if not self.county_boxes:
      self.df = database.get_map_data_for_states(self.state_boxes, 'US', [self.dataType], [self.curr_month], self.curr_year, self.curr_year)
    else:
      self.df = database.get_map_data_for_counties(self.state_boxes, self.county_boxes, 'US', [self.dataType], [self.curr_month], self.curr_year, self.curr_year)
    li = self.df[self.dataType+"_"+self.curr_month].tolist()
    self.mapFig.update_traces(z=li)
    self.mapFig.write_html('HTML/map_fig.html')
    self.browser.setUrl(QUrl.fromLocalFile(os.path.abspath('HTML/map_fig.html')))

 #Button control to remove a line
  def removeLine(self):
      try:
        toDelete = self.lines.pop()
      except:
        return
      self.deleteLayoutItems(toDelete)
      self.layout.removeItem(toDelete)
      self.state_boxes.pop()
      self.date_boxes.pop()
      return

  #Helper function to remove line.
  def deleteLayoutItems(self, layout):
    for i in reversed(range(layout.count())): 
      layout.itemAt(i).widget().clear()

  #Gets a list of states selected for every line
  def getStates(self):
    states = []
    for boxes in self.state_boxes:
      states.append(boxes.currentText())
    return states

 
  


if __name__ == "__main__":
  app = QApplication([])
  window = MapWindow('TODO:')
  app.setStyleSheet("QHeaderView::section { background-color: #2F2F2F; color: white }")
  app.exec_()