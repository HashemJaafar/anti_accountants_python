import sqlite3
import math
import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
import pandas as pd
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.lang.builder import Builder
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
import numpy as np

# i shoud learn how to append numpy arrey

Accounts=(
 ('Assets'       ,'current_assets'       ,'Normal')
,('Assets'       ,'current_assets'       ,'Contra')
,('Assets'       ,'long_term_investment' ,'Normal')
,('Assets'       ,'long_term_investment' ,'Contra')
,('Assets'       ,'fixed_assets'         ,'Normal')
,('Assets'       ,'fixed_assets'         ,'Contra')
,('Assets'       ,'intangible_assets'    ,'Normal')
,('Assets'       ,'intangible_assets'    ,'Contra')
,('Liabilities'  ,'current_liabilities'  ,'Normal')
,('Liabilities'  ,'current_liabilities'  ,'Contra')
,('Liabilities'  ,'long_term_liabilities','Normal')
,('Liabilities'  ,'long_term_liabilities','Contra')
,('Owners_equity','Investment_by_owner'  ,'Normal')
,('Owners_equity','Comprehensive_income' ,'Normal')
,('Owners_equity','Retained_Earnings'    ,'Withdrawals')
,('Owners_equity','Retained_Earnings'    ,'Revenues')
,('Owners_equity','Retained_Earnings'    ,'Gains')
,('Owners_equity','Retained_Earnings'    ,'Expenses')
,('Owners_equity','Retained_Earnings'    ,'Losses')
)

class data_base:
    def __init__(self):
        self.db=sqlite3.connect('Accounting.db')
        self.cursor=self.db.cursor()
        self.cursor.execute('''create table if not exists journal (Date INTEGER,journal_number INTEGER,one TEXT,two TEXT,three TEXT,four TEXT,Value REAL,Price REAL,Quantity REAL,
        Selling_price REAL,Expair INTEGER,Description TEXT,Seller_or_buyer_name TEXT,Sites TEXT,Location TEXT,Barcode INTEGER,Employee_name TEXT,The_number_of_pieces_left INTEGER)''')

    def save(self,return_list,return_list1,return_list2):
        Date=datetime.datetime.today()
        
        self.cursor.execute('select * from journal order by Date desc')
        try:Journal_Number=self.cursor.fetchone()[1]+1
        except TypeError:Journal_Number=1

        self.l,self.l1,self.l2=[],[],[]
        for item in return_list:
            self.l.append(item.text)
            item.text=''
        for item in return_list1:
            self.l1.append(item.text)
            item.text='Choose account'
        for item in return_list2:
            self.l2.append(item.text)
        w=np.concatenate((np.array(self.l1).reshape(-1,1),np.array(self.l).reshape(-1,9),np.array(self.l2).reshape(-1,1)), axis=1)
        print(w)

        for i in range(len(w)):

            c=w[i,0].split()

            self.cursor.execute('''insert into journal(Date,journal_number,one,two,three,four,Value,Price,Quantity,
            Selling_price,Expair,Description,Seller_or_buyer_name,Sites,Location,Barcode) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (Date,Journal_Number,c[0],c[1],c[2],c[3],w[i,1],w[i,2],w[i,3],w[i,4],w[i,5],w[i,6],w[i,7],w[i,8],w[i,9],w[i,10]))

    def __del__(self):
        self.db.commit()
        self.db.close()


data_base().__init__()

class data_analyses():
    def r(self):
        df=pd.read_sql_query("SELECT one,two,three,four from journal",sqlite3.connect('Accounting.db'))
        b=df.groupby(['one','two','three','four']).sum()
        # c=b.loc[['Gains']].sum()-b.loc[['Losses']].sum()
        # b.loc['Owners_equity','Retained_Earnings','total']=c
        z=b
        print(z)
        return df#.index.get_value()

kv=Builder.load_string('''
Carousel:
    loop:True
    ScrollView:
        do_scroll_x:False
        scroll_type:['bars', 'content']
        bar_width:'20dp'
        GridLayout:
            id:inputs
            cols:12
            row_force_default:True
            row_default_height:30
            size_hint_y:None
            height:self.minimum_height
    ScrollView:
        do_scroll_x:False
        scroll_type:['bars', 'content']
        bar_width:'20dp'
        GridLayout:
            id:jurnal_grid
            cols:5
            size_hint:(None,None)
            height:self.minimum_height
            width:self.minimum_width
    ScrollView:
        do_scroll_x:False
        scroll_type:['bars', 'content']
        bar_width:'20dp'
        GridLayout:
            id:statment_grid
            cols:4
            size_hint:(None,None)
            height:self.minimum_height
            width:self.minimum_width
''')

class Accounting(App):
    def build(self):return kv


    def on_start(self):
        return_list = [] # shoud be array
        return_list1 = []
        return_list2 = []

        self.root.ids.inputs.add_widget(Button         (background_color=(0,0,0,0),text='Save'      ,on_press=lambda x:data_base().save(return_list,return_list1,return_list2)))
        self.root.ids.inputs.add_widget(ToggleButton   (background_color=(0,0,0,0),text='Print'     ,on_press=self.print))

        for i in range(4):self.root.ids.inputs.add_widget(BoxLayout())
        for i in range(4):self.root.ids.inputs.add_widget(CheckBox(on_press=self.print,active=True))

        self.root.ids.inputs.add_widget(ToggleButton   (background_color=(0,0,0,0),text='Completion',on_press=self.print))
        self.root.ids.inputs.add_widget(Button         (background_color=(0,0,0,0),text='X'         ,on_press=self.clear))

        for i in range(1):

            a=Spinner(background_color=(0,0,0,0),color=(1,1,1,1),text='Choose account',values=[str(i) for i in range(10)],size_hint_x=4)
            return_list1.append(a)
            self.root.ids.inputs.add_widget(a)

            for i in ['Value','Price','Quantity','Selling price','Expair','Description','Seller or buyer name','Sites','Location']:
                a=TextInput(background_color=(0,0,0,0),foreground_color=(1,1,1,1),hint_text=i,multiline=False)
                return_list.append(a)
                self.root.ids.inputs.add_widget(a)

            a=Button(background_color=(0,0,0,0),color=(1,1,1,1),text='Barcode')
            return_list2.append(a)
            self.root.ids.inputs.add_widget(a)
            self.root.ids.inputs.add_widget(Button(background_color=(0,0,0,0),color=(1,1,1,1),text='X'))


    def clear(self,obj):self.Value.text,self.Price.text,self.Quantity.text,self.Description_input.text='','','',''


    def print(self,obj):print('print')


Accounting().run()