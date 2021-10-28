import datetime
import time
import sqlite3
import pandas as pd
import numpy as np
import calendar
from decimal import Decimal


def flatten_list(list_of_entry):
    flat_list=[]
    for sublist in list_of_entry:
        if isinstance(sublist,(list,tuple)):
            for item in sublist:
                flat_list.append(item)
        else:flat_list.append(sublist)
    return flat_list


def check_dates(start_date,end_date):
    assert start_date<=end_date,'please enter the start_date<=end_date'
    return start_date,end_date


def dates(date=None):
    try:date=str(datetime.datetime(*date))
    except:date=str(datetime.datetime.today())
    return date


def strip_time(time_in_string):
    try:strip_time=datetime.datetime.strptime(time_in_string,'%Y-%m-%d %H:%M:%S.%f')
    except:
        try:strip_time=datetime.datetime.strptime(time_in_string,'%Y-%m-%d %H:%M:%S')
        except:strip_time=datetime.datetime.strptime(time_in_string,'%H:%M')
    return strip_time


def check_if_duplicates(list_of_elements):
    set_of_elems=set()
    for element in list_of_elements:
        assert element not in set_of_elems,f'{element} is duplicated values in the parameters accounts list and that make error. you should remove it'
        set_of_elems.add(element)         


def discount_tax_calculator(price,discount_tax):
    if discount_tax<0:discount_tax=abs(discount_tax)
    elif discount_tax>0:discount_tax=price*discount_tax
    return discount_tax


class financial_accounting:
    def __init__(self,company_name='accounting',start_date=None,end_date=None,discount=0,invoice_discounts_tax_list=[[0,0,0]],assets_normal=[],cash_and_cash_equivalent=[],
    fifo=[],lifo=[],wma=[],assets_contra=[],liabilities_normal=[],liabilities_contra=[],equity_normal=[],comprehensive_income=[],equity_contra=[],withdrawals=[],
    revenues=[],service=[],expenses=[],operating_expense=[],interest=[],tax=[],deprecation=[],amortization=[],gains=[],losses=[]):

        self.success=False
        self.company_name=company_name
        self.db=sqlite3.connect(company_name+'.db')
        self.cursor=self.db.cursor()

        self.cursor.execute('''create table if not exists journal (date integer,entry_number integer,account text,value real,price real,quantity real,barcode integer,
        entry_expair integer,description text,name text,employee_name text,entry_date integer,reverse bool)''')

        self.cursor.execute('''create table if not exists inventory (date integer,account text,cost real,quantity real,
        barcode integer,expair integer,seller_name text,employee_name text,entry_date integer)''')

        self.price_discount_tax=fifo+lifo+wma+service
        for i in self.price_discount_tax:
            i[2]=discount_tax_calculator(i[1],i[2])
            i[3]=discount_tax_calculator(i[1],i[3])
        if discount!=0:
            for i in self.price_discount_tax:i[2]=discount_tax_calculator(i[1],discount)

        self.service    =[i[0] for i in service ]
        self.fifo       =[i[0] for i in fifo    ]
        self.lifo       =[i[0] for i in lifo    ]
        self.wma        =[i[0] for i in wma     ]
        self.inventory  =self.fifo+self.lifo+self.wma

        self.cost_of_goods_sold =['cost of '    +i for i in self.inventory]
        self.discounts          =['discount of '+i for i in self.inventory]+['discount of ' +i for i in self.service]+['invoice discount']
        self.tax                =['tax of '     +i for i in self.inventory]+['tax of '      +i for i in self.service]+['invoice tax']+tax
        self.revenues           =['revenue of ' +i for i in self.inventory]+revenues+self.service

        self.cash_and_cash_equivalent=cash_and_cash_equivalent
        self.assets_normal=assets_normal+self.cash_and_cash_equivalent+self.inventory
        self.assets_contra=assets_contra
        self.liabilities_normal=liabilities_normal+['tax']
        self.liabilities_contra=liabilities_contra
        self.comprehensive_income=comprehensive_income
        self.equity_normal=equity_normal+self.comprehensive_income
        self.equity_contra=equity_contra
        self.withdrawals=withdrawals
        self.interest=interest
        self.deprecation=deprecation
        self.amortization=amortization
        self.operating_expense=operating_expense
        self.itda=self.interest+self.tax+self.deprecation+self.amortization
        self.expenses=expenses+self.cost_of_goods_sold+self.discounts+self.itda+self.operating_expense+['expair_expenses']
        self.gains=gains
        self.losses=losses

        self.temporary_debit_accounts =self.withdrawals+self.expenses+self.losses
        self.temporary_credit_accounts=self.revenues+self.gains
        self.temporary_accounts=self.temporary_debit_accounts+self.temporary_credit_accounts
        
        self.debit_accounts =self.assets_normal+self.liabilities_contra+self.equity_contra+self.temporary_debit_accounts
        self.credit_accounts=self.assets_contra+self.liabilities_normal+self.equity_normal+self.temporary_credit_accounts

        self.all_accounts()
        self.adjusting_methods = ['linear','exponential','logarithmic',None]
        self.invoice_discounts_tax_list=invoice_discounts_tax_list
        check_if_duplicates(self.debit_accounts+self.credit_accounts)
        self.start_date,self.end_date=check_dates(dates(start_date),dates(end_date))
        self.now=dates()


    def all_accounts(self):
        try:
            all_accounts=self.column_values('account')
            for i in all_accounts:
                if i not in self.debit_accounts+self.credit_accounts:print(f'{i} is not on parameters accounts lists')
        except:
            all_accounts=[]
            print('you don\'t have journal entry yet')
        return all_accounts


    def price_discount_tax_list(self,string1,string2,account,price_discount_tax_index,quantity):
        for list in self.price_discount_tax:
            if list[0]==account:value=list[price_discount_tax_index]*quantity
        return [string1+string2,value,quantity,None]


    def cost_flow(self,account,quantity,barcode,order_by_date_asc_or_desc='asc'):
        self.success=False
        inventory=self.cursor.execute(f'select cost,quantity from inventory where quantity>0 and account=? and barcode=? order by date {order_by_date_asc_or_desc}',(account,barcode)).fetchall()
        quantity=abs(quantity)
        quantity_count=quantity
        costs=0

        for item in inventory:
            if item[1]>=quantity_count:
                costs+=item[0]*quantity_count
                self.cursor.execute(f'update inventory set quantity=quantity-? where account=? and cost=? and quantity=? and barcode=? order by date {order_by_date_asc_or_desc} limit 1',(quantity_count,account,item[0],item[1],barcode))
                quantity_count=0
                break
            if item[1]<quantity_count:
                costs+=item[0]*item[1]
                self.cursor.execute(f'update inventory set quantity=0 where account=? and cost=? and quantity=? and barcode=? order by date {order_by_date_asc_or_desc} limit 1',(account,item[0],item[1],barcode))
                quantity_count-=item[1]

        assert quantity_count==0,f'you order {quantity} but you have {quantity-quantity_count} {account} with barcode {barcode}'
        self.success=True
        return costs


    def auto_completion(self,list_of_entry):
        new_list_of_entry=[]
        for i in list_of_entry:
            barcode=i[3]
            account=i[0]
            quantity=abs(i[2])
            if account in self.inventory and i[2]<0:
                if   account in self.fifo or account in self.wma:costs=self.cost_flow(account,quantity,barcode)
                elif account in self.lifo:costs=self.cost_flow(account,quantity,barcode,order_by_date_asc_or_desc='desc')
                else:continue

                i[1]=-costs
                new_list_of_entry.append(['cost of '+account,costs,quantity,None])
                new_list_of_entry.append(self.price_discount_tax_list('revenue of ',account,account,1,quantity))
                new_list_of_entry.append(self.price_discount_tax_list('discount of ',account,account,2,quantity))
                new_list_of_entry.append(self.price_discount_tax_list('tax of ',account,account,3,quantity))
                new_list_of_entry.append(self.price_discount_tax_list('tax','',account,3,quantity))

            elif account in self.service:
                i[1]=self.price_discount_tax_list('',account,account,1,quantity)[1]
                new_list_of_entry.append(self.price_discount_tax_list('discount of ',account,account,2,quantity))
                new_list_of_entry.append(self.price_discount_tax_list('tax of ',account,account,3,quantity))
                new_list_of_entry.append(self.price_discount_tax_list('tax','',account,3,quantity))

        list_of_entry+=new_list_of_entry
        total_invoice_before_invoice_discount=0
        for i in list_of_entry:
            if i[0] in self.revenues:total_invoice_before_invoice_discount+=i[1]
            if i[0] in self.discounts:total_invoice_before_invoice_discount-=i[1]

        discount=0
        tax=0
        for i in self.invoice_discounts_tax_list:
            if total_invoice_before_invoice_discount>=i[0]:
                discount=i[1]
                tax=i[2]
        invoice_discount=discount_tax_calculator(total_invoice_before_invoice_discount,discount)
        list_of_entry.append(['invoice discount',invoice_discount,1,None])
        invoice_tax=discount_tax_calculator(total_invoice_before_invoice_discount,tax)
        list_of_entry.append(['invoice tax',invoice_tax,1,None])
        list_of_entry.append(['tax',invoice_tax,1,None])

        return list_of_entry


    def entry_number(self):
        try:entry_number=self.cursor.execute('select * from journal order by entry_number desc').fetchone()[1]+1
        except:entry_number=1
        return entry_number


    def column_values(self,column):return flatten_list(set(self.cursor.execute(f'select "{column}" from journal').fetchall()))


    def reverse_entry(self,entry_number_to_reverse,entry_expair,employee_name):
        self.success=False
        list_of_entry=self.cursor.execute('select * from journal where entry_number=? and date<? and reverse is NULL',(entry_number_to_reverse,self.now))
        list_of_entry=list([list(i) for i in list_of_entry])
        assert list_of_entry!=[],f'you can\'t reverse entry number {entry_number_to_reverse}'
        revised_entry=[]
        entry_number_reverse=self.entry_number()
        for i in list_of_entry:
            try:i[8]=f' (reverse entry for entry number {i[1]} entered by {i[10]} and revised by {employee_name})'
            except:i[8]=f' (reverse entry for entry number {i[1]} entered by {i[10]} and revised by {employee_name})'
            i[0]=self.now
            i[1]=entry_number_reverse
            i[3]*=-1
            i[5]*=-1
            i[7]=entry_expair
            i[10]=employee_name
            i[11]=self.now
            revised_entry.append(i)

        # revised_entry=pd.DataFrame(revised_entry)
        # revised_entry=revised_entry.groupby(2,dropna=False)[[3,5]].sum().reset_index().values.tolist()
        # print('#'*50)
        # print(revised_entry)

        self.insert_into_journal(revised_entry)
        self.cursor.execute('update journal set reverse=True where entry_number=?',(entry_number_to_reverse,))

        for i in revised_entry:
            account=i[2]
            value=i[3]
            price=i[4]
            quantity=i[5]
            bacode=i[6]

            if account in self.inventory and value<0:
                self.cost_flow(account,quantity,bacode)
                self.weighted_average([account])

            elif account in self.inventory and value>0:
                self.insert_into_inventory(self.now,[[account,value,price,quantity,bacode]],i[7],i[9],employee_name,self.now)
                self.weighted_average([account])

        self.cursor.execute('delete from journal where reverse=True and date>?',(self.now,))
        self.success=True


    def invoice(self,list_of_entry,buyer_name=None,buyer_sites=None,buyer_location=None,employee_name=None,entry_date=None,entry_number=None,invoice_description=None):

        discounts,revenues,assets,invoice_discount=[],[],[],[]
        for c in list_of_entry:
            i=c[0:4]
            if i[0] in self.assets_normal and i[0] not in self.inventory and i[1]>0:assets.append(i)
            elif i[0]=='invoice discount':
                invoice_discount=[[i[0],i[1]]]
            elif 'discount of ' in i[0]:
                i[0]=i[0].replace('discount of ','')
                discounts.append(i)
            elif 'revenue of ' in i[0]:
                i[0]=i[0].replace('revenue of ','')
                revenues.append(i)

        if revenues==[]:return

        for i in [discounts,revenues,assets]:
            if i==[]:i+=[[np.nan,np.nan,np.nan,np.nan]]

        if invoice_discount==[]:[[np.nan,np.nan]]

        try:
            discount_frame=pd.DataFrame(discounts,columns=['','total_discount','discount','quantity'])
            revenues_frame=pd.DataFrame(revenues,columns=['','value','price','quantity'])
            assets_frame=pd.DataFrame(assets,columns=['','value','price','quantity'])
            invoice_discount_frame=pd.DataFrame(invoice_discount,columns=['','value'])

            p=pd.concat([revenues_frame,discount_frame]).groupby(['','quantity'],dropna=False).sum().reset_index(level=['','quantity'])
            p['value_after_discount'] = p['value'] - p['total_discount']
            j=p[['value_after_discount','value','total_discount','quantity']].sum()
            p=p.append(j, ignore_index = True)
            p=pd.concat([p,invoice_discount_frame,assets_frame]).replace(0,np.nan).dropna(how='all').fillna('')
            p=p[['','value_after_discount','value','price','total_discount','discount','quantity']]
        except:return
        return f'''company name:{self.company_name}\nbuyer name:{buyer_name}\nbuyer sites:{buyer_sites}\nbuyer location:{buyer_location}\nemployee name:{employee_name}\nentry date:{entry_date}\nentry number:{entry_number}\n{invoice_description}\n{p}'''
        # return self.company_name,buyer_name,buyer_sites,buyer_location,employee_name,entry_date,entry_number,invoice_description,p


    def check_entry(self,list_of_entry):
        self.success=False
        i = 0
        while i < len(list_of_entry):
            if isinstance(list_of_entry[i][1],(float,int))==False or isinstance(list_of_entry[i][2],(float,int))==False or list_of_entry[i][1]==0 or list_of_entry[i][2]==0:
                # print(f'{list_of_entry[i]} is removed because one of the values is not >0 or <0')
                list_of_entry.remove(list_of_entry[i])
            else:i += 1

        zero=0
        for i in list_of_entry:
            if i[0] not in self.equity_normal+self.equity_contra:
                account_balance=flatten_list(self.cursor.execute('select sum(value) from journal where account=? and date<?',(i[0],self.now)))[0]
                if account_balance==None:account_balance=0
                assert Decimal(str(account_balance+i[1]))>0,f'you cant enter {i} because you have {account_balance} and that will make the balance of {i[0]} negative {Decimal(str(account_balance+i[1]))} and that you just can do it in equity accounts not other accounts'
            i.insert(2,i[1]/i[2])
            assert i[2]>0,f'the {i[1]} and {i[3]} should be positive both or negative both'
            if i[0] in self.debit_accounts:zero+=Decimal(str(i[1]))
            elif i[0] in self.credit_accounts:zero-=Decimal(str(i[1]))
            else:assert False,f'{i[0]} is not on parameters accounts lists'
        assert zero==0,f'{zero} not equal 0 if the number>0 it means debit overstated else credit overstated debit-credit=0'

        self.success=True
        return list_of_entry


    def total_second(self,delta_days,time_in_week_list,date):
        total_seconds=1
        for day in range(delta_days):
            for element in time_in_week_list:
                if calendar.day_name[(date+datetime.timedelta(day+1)).weekday()]==element[0]:
                    total_seconds+=(strip_time(element[1])-strip_time(element[2])).seconds
        return total_seconds


    def adjust_entry(self,list_of_entry,date,time_in_week_list,entry_expair,adjusting_method):
        date=strip_time(date)
        entry_expair=strip_time(entry_expair)
        delta_total=entry_expair-date
        date=datetime.datetime.combine(date.date(),strip_time('00:00').time())
        delta_days=delta_total.days+1
        adjusted_list=[]
        total_seconds=self.total_second(delta_days,time_in_week_list,date)

        for i in list_of_entry:
            s=0
            one_account_adjusted_list=[]
            total_value=abs(i[1])
            price=i[2]
            deprecation=total_value**(1/total_seconds)
            value_per_second=i[1]/total_seconds
            second_counter=0

            for day in range(delta_days):
                for element in time_in_week_list:
                    if calendar.day_name[(date+datetime.timedelta(day)).weekday()]==element[0]:
                        seconds=(strip_time(element[1])-strip_time(element[2])).seconds
                        
                        if   adjusting_method=='linear'     :value=seconds*value_per_second
                        elif adjusting_method=='exponential':value=(deprecation**(second_counter+seconds))-(deprecation**second_counter)
                        elif adjusting_method=='logarithmic':value=(total_value/deprecation**second_counter)-(total_value/deprecation**(second_counter+seconds))
                        second_counter+=seconds
                    else:continue

                    quantity=value/price
                    if day>=delta_days-1:
                        value=abs(total_value-s)
                        quantity=value/price
                    s+=abs(value)

                    if i[1]<0:value=-abs(value)
                    if i[3]<0:quantity=-abs(quantity)

                    date1        =str(date+datetime.timedelta(days=day,hours=strip_time(element[2]).hour,minutes=strip_time(element[2]).minute))
                    entry_expair1=str(date+datetime.timedelta(days=day,hours=strip_time(element[1]).hour,minutes=strip_time(element[1]).minute))

                    one_account_adjusted_list.append([date1,i[0],value,price,quantity,i[4],entry_expair1])
            adjusted_list.append(one_account_adjusted_list)
        adjusted_list=[list(i) for i in zip(*adjusted_list)]

        return adjusted_list


    def account_name_from_barcode(self,list_of_entry):
        for i in list_of_entry:
            if i[0]==None and i[3]=='':assert False
            if i[0]==None:i[0]=flatten_list(self.cursor.execute(f'select account from inventory where barcode=?',(i[3],)).fetchall())[0]
        return list_of_entry


    def journal_entry(self,list_of_entry,auto_completion=True,entry_to_correct=None,date=None,entry_expair=None,adjusting_method=None,description=None,
    invoice_description=None,name=None,seller_or_buyer_sites=None,seller_or_buyer_location=None,employee_name=None,time_in_week_list=[['Monday','23:59','00:00'],
    ['Tuesday','23:59','00:00'],['Wednesday','23:59','00:00'],['Thursday','23:59','00:00'],['Friday','23:59','00:00'],['Saturday','23:59','00:00'],['Sunday','23:59','00:00']]):

        self.success=False
        date,entry_expair,time_in_week_list=self.check_parameters(list_of_entry,date,entry_expair,adjusting_method,time_in_week_list)
        list_of_entry=self.account_name_from_barcode(list_of_entry)

        list_of_entry=pd.DataFrame(list_of_entry).replace(np.nan,'')
        list_of_entry=list_of_entry.groupby([0,3],dropna=False).sum().reset_index(level=[0,3])
        list_of_entry=list_of_entry[[0,1,2,3]].values.tolist()

        entry_number=self.entry_number()
        if entry_to_correct!=None:self.reverse_entry(entry_to_correct,entry_expair,employee_name)
        if auto_completion:list_of_entry=self.auto_completion(list_of_entry)
        list_of_entry=self.check_entry(list_of_entry)

        self.insert_into_inventory(date,list_of_entry,entry_expair,name,employee_name,self.now)
        if adjusting_method in ['linear','exponential','logarithmic']:
            adjusted_list=flatten_list(self.adjust_entry(list_of_entry,date,time_in_week_list,entry_expair,adjusting_method))
            for i in adjusted_list:
                self.insert_into_journal([[i[0],entry_number]+i[1:7]+[description,name,employee_name,self.now,None]])
        else:
            for i in list_of_entry:
                self.insert_into_journal([[date,entry_number]+i+[entry_expair,description,name,employee_name,self.now,None]])
        print(self.invoice(list_of_entry,name,seller_or_buyer_sites,seller_or_buyer_location,employee_name,self.now,entry_number,invoice_description))
        self.success=True


    def check_parameters(self,list_of_entry,date,entry_expair,adjusting_method,time_in_week_list):
        self.success=False
        assert isinstance(list_of_entry,list),'unsuccessful. be sure to enter list not other data type'
        assert (entry_expair!=None and adjusting_method not in self.adjusting_methods)==False,f'check entry_expair => {entry_expair} and adjusting_method => {adjusting_method} should be in {self.adjusting_methods}'
        for i in list_of_entry:
            assert (i[0] in self.inventory and adjusting_method in ['linear','exponential','logarithmic'])==False,f'{i[0]} is in inventory you just can None'
        for i in list_of_entry:assert len(i)==4,f'the length of {i} is not 4'
        if entry_expair!=None:date,entry_expair=check_dates(dates(date),dates(entry_expair))
        else:date=dates(date)

        day=str()
        sequential_time=[]
        list_of_days=[]
        for i in time_in_week_list:
            i[0]=i[0].capitalize()
            list_of_days.append(time.strptime(i[0], "%A").tm_wday)
            assert strip_time(i[1])>strip_time(i[2]),f'{i} should be {i[1]}>{i[2]}'
            sequential_time.append(i[2])
            sequential_time.append(i[1])

            if len(list_of_days)>=2:
                assert list_of_days[-1]>=list_of_days[-2],f'{i} {i[0]} is not >={day} the sequential should be like this Monday<Tuesday<Wednesday<Thursday<Friday<Saturday<Sunday'
                if list_of_days[-1]==list_of_days[-2]:
                    assert strip_time(sequential_time[-2])>=strip_time(sequential_time[-3]),f'{i[0]} {sequential_time[-2]} should be >={i[0]} {sequential_time[-3]}'

            day=i[0]
        self.success=True
        return date,entry_expair,time_in_week_list


    def insert_into_journal(self,list_of_entry):
        for single_list in list_of_entry:
            self.cursor.execute('''insert into journal(date,entry_number,account,value,price,quantity,barcode,entry_expair,
            description,name,employee_name,entry_date,reverse) values (?,?,?,?,?,?,?,?,?,?,?,?,?)''',single_list)

                
    def insert_into_inventory(self,date,list_of_entry,entry_expair,seller_name,employee_name,entry_date):
        for i in list_of_entry:
            if i[0] in self.inventory and i[3]>0:
                self.cursor.execute('''insert into inventory(date,account,cost,quantity,barcode,expair,seller_name,employee_name,entry_date)
                values (?,?,?,?,?,?,?,?,?)''',(date,i[0],i[2],i[3],i[4],entry_expair,seller_name,employee_name,entry_date))


    def journal(self,date=[],entry_number=[],account=[],value=[],price=[],quantity=[],barcode=[],entry_expair=[],
    adjusting_method=[],description=[],name=[],employee_name=[],entry_date=[],reverse=[]):

        journal=pd.read_sql_query('select * from journal',self.db).fillna('')
        journal=journal[
         (journal['date'].isin(date))
        &(journal['entry_number'].isin(entry_number))
        &(journal['account'].isin(account))
        &(journal['value'].isin(value))
        &(journal['price'].isin(price))
        &(journal['quantity'].isin(quantity))
        &(journal['barcode'].isin(barcode))
        &(journal['entry_expair'].isin(entry_expair))
        &(journal['adjusting_method'].isin(adjusting_method))
        &(journal['description'].isin(description))
        &(journal['name'].isin(name))
        &(journal['employee_name'].isin(employee_name))
        &(journal['entry_date'].isin(entry_date))
        &(journal['reverse'].isin(reverse))
        ]

        pd.set_option('display.max_rows', 10000, 'display.max_columns', 20)
        return journal


    def inventory1(self):
        i= pd.read_sql_query('select * from inventory',self.db)
        return i


    def financial_statements(self):
        journal=pd.read_sql_query('select date,entry_number,account,value,quantity,entry_expair from journal',self.db)#.fillna('')
        journal_before=journal.loc[journal.date<self.start_date].drop(columns=['date','entry_number','entry_expair'])
        journal_after=journal.loc[(journal.date>=self.start_date)&(journal.date<=self.end_date)].drop(columns=['date','entry_expair'])

        statements_without_cash_flow=self.statements_without_cash_flow(journal_before,journal_after)
        self.current_assets(journal)
        cash_flow_list=self.cash_flow_list(journal_after)

        cash_flow_frame=statements_without_cash_flow[statements_without_cash_flow.account.isin(cash_flow_list.account)]
        cash_flow_with_value=pd.merge(cash_flow_frame,cash_flow_list,on='account')
        financial_statements=cash_flow_with_value.append(statements_without_cash_flow[~statements_without_cash_flow.account.isin(cash_flow_list.account)],ignore_index=True).fillna(0)

        columns=['account','value','cash flow','quantity']
        columns_to_sum=['value','cash flow','quantity']

        list_of_catigory=[
        ['total_assets',self.assets_normal,self.assets_contra],
        ['total_assets_normal',self.assets_normal],
        ['cash_and_cash_equivalent',self.cash_and_cash_equivalent],
        ['total_inventory',self.inventory],
        ['total_fifo',self.fifo],
        ['total_lifo',self.lifo],
        ['total_wma',self.wma],
        ['total_assets_contra',self.assets_contra],
        ['total_liabilities',self.liabilities_normal,self.liabilities_contra],
        ['total_liabilities_normal',self.liabilities_normal],
        ['total_liabilities_contra',self.liabilities_contra],
        ['total_equity',self.equity_normal+[self.retained_earnings,0,0]+self.temporary_credit_accounts,self.equity_contra+self.temporary_debit_accounts],
        ['total_equity_normal',self.equity_normal],
        ['total_equity_contra',self.equity_contra],
        ['total_withdrawals',self.withdrawals],
        ['retained_earnings',self.retained_earnings],
        ['total_net_income',self.revenues+self.gains,self.expenses+self.losses],
        ['total_revenues',self.revenues],
        ['total_expenses',self.expenses],
        ['total_cost_of_goods_sold',self.cost_of_goods_sold],
        ['total_discounts',self.discounts],
        ['total_operating_expense',self.operating_expense],
        ['total_interest',self.interest],
        ['total_itda',self.itda],
        ['total_tax',self.tax],
        ['total_deprecation',self.deprecation],
        ['total_amortization',self.amortization],
        ['total_gains',self.gains],
        ['total_losses',self.losses],
        ]
        financial_statements_classified=self.financial_statements_classified(financial_statements, columns, columns_to_sum, list_of_catigory)
        financial_statements_classified=pd.concat(financial_statements_classified,ignore_index=True)
        financial_statements_classified['price']=financial_statements_classified.value/financial_statements_classified.quantity
        return financial_statements_classified[['account','value','cash flow','price','quantity']].fillna(0).replace(0,'').drop_duplicates(keep='last')


    def financial_statements_classified(self, financial_statements, columns, columns_to_sum, list_of_catigory):
        list_of_frames=[]
        for i in list_of_catigory:
            if i[0]=='retained_earnings':
                list_of_frames.append(pd.DataFrame(([[i[0],i[1],0,0]]),columns=columns))
            elif len(i)==2:
                total=financial_statements[columns_to_sum].loc[financial_statements.account.isin(i[1])].sum()
                list_of_frames.append(pd.DataFrame([flatten_list([i[0],total.values.tolist()])],columns=columns))
                list_of_frames.append(financial_statements[columns].loc[financial_statements.account.isin(i[1])])
            elif len(i)==3:
                normal=financial_statements[columns_to_sum].loc[financial_statements.account.isin(i[1])].sum()
                contra=financial_statements[columns_to_sum].loc[financial_statements.account.isin(i[2])].sum()
                total=normal+contra['cash flow']
                list_of_frames.append(pd.DataFrame([flatten_list([i[0],total.values.tolist()])],columns=columns))
        return list_of_frames


    def current_assets(self,journal):
        accounts_balance=journal.loc[journal['account'].isin(self.assets_normal)].groupby('account',dropna=False).sum().drop(columns='entry_number')
        year_journal=journal.loc[(journal.date>=str(strip_time(self.end_date)-datetime.timedelta(365)))&(journal.date<=self.end_date)].drop(columns='date')
        cash_year_journal=self.cash_journal_without_entry_number(year_journal)
        assets_year_journal=cash_year_journal.loc[~cash_year_journal['account'].isin(self.cash_and_cash_equivalent)&cash_year_journal['account'].isin(self.assets_normal)]
        negative_assets_year_journal=assets_year_journal.loc[assets_year_journal['value']<0]
        negative_assets_balance=negative_assets_year_journal.groupby(['account']).sum()
        current_assets=negative_assets_balance[['value','quantity']].abs()
        non_current_assets=(accounts_balance-current_assets).dropna()
        print(non_current_assets)

        accruals=journal.loc[(
         (journal.entry_expair<=self.end_date)
        # &(journal.entry_expair.isin([np.nan]))
        &(journal.account.isin(self.liabilities_normal))
        )].drop(columns=['date'])
        print(accruals)



    def cash_flow_list(self, journal_after):
        cash_journal_without_entry_number = self.cash_journal_without_entry_number(journal_after)
        cash_journal_after=cash_journal_without_entry_number.groupby('account',dropna=False).sum().reset_index(level='account').values.tolist()

        cash_flow_list=[]
        for i in cash_journal_after:
            if i[0] in self.debit_accounts and i[0] not in self.cash_and_cash_equivalent:
                i[1]*=-1
                i[2]*=-1
                cash_flow_list.append(i)
            elif i[0] in self.credit_accounts:cash_flow_list.append(i)
        cash_flow_list=pd.DataFrame(cash_flow_list,columns=cash_journal_without_entry_number.columns).rename(columns={'value':'cash flow','quantity':'quantity flow'}, inplace = False)
        return cash_flow_list


    def cash_journal_without_entry_number(self, journal_after):
        cash_ledger_after=journal_after.loc[journal_after['account'].isin(self.cash_and_cash_equivalent)]
        cash_journal_after=journal_after.loc[journal_after['entry_number'].isin(cash_ledger_after.entry_number.values.tolist())]
        cash_journal_without_entry_number=cash_journal_after.drop(columns='entry_number')
        return cash_journal_without_entry_number


    def statements_without_cash_flow(self, journal_before, journal_after):
        self.retained_earnings=journal_before['value'].loc[journal_before['account'].isin(self.temporary_credit_accounts)].sum()-journal_before['value'].loc[journal_before['account'].isin(self.temporary_debit_accounts)].sum()
        journal_before_without_tomprary_account=journal_before[~journal_before['account'].isin(self.temporary_accounts)]
        filtered_journal=journal_before_without_tomprary_account.append(journal_after,ignore_index=True)
        financial_statements=filtered_journal.groupby('account',dropna=False).sum().reset_index(level='account')
        return financial_statements


    def weighted_average(self,list_of_accounts):
        try:           
            for i in list_of_accounts:self.cursor.execute('update inventory set cost=(select sum(value)/sum(quantity) from journal where account=?) where account=?',(i,i))
        except:pass


    def expair_expenses(self):
        entry_number=self.entry_number()
        expair_goods=self.cursor.execute('select account,cost*quantity*-1,cost,quantity*-1,barcode from inventory where expair<?',(self.now,)).fetchall()
        expair_expenses=flatten_list(self.cursor.execute('select sum(cost*quantity),sum(cost*quantity)/sum(quantity),sum(quantity) from inventory where expair<?',(self.now,)).fetchall())
        if None not in expair_expenses:
            self.cursor.execute('delete from inventory where expair<?',(self.now,))
            list_of_entry=expair_goods+[['expair_expenses']+expair_expenses+[None]]
            list_of_entry=list([list(i) for i in list_of_entry])
            for i in list_of_entry:self.insert_into_journal([[self.now,entry_number]+i+[None,'to record the expiry of inventory',None,None,self.now,None]])


    def __del__(self):
        if self.success==True:
            self.expair_expenses()
            self.cursor.execute('delete from inventory where quantity=0')
            self.weighted_average(self.wma)
            self.db.commit()
        self.db.close()


if __name__ == "__main__":
    s=financial_accounting(
    company_name='a',
    # start_date=(2020,9,7),
    # end_date=(2020,11,3),
    start_date=(2021,9,7),
    end_date=(2021,11,3),
    discount=0,
    invoice_discounts_tax_list=[[5,-1,-1],[100,0.05,-1]],
    assets_normal=['Office Equipment','Advertising Supplies','Prepaid Insurance'],
    cash_and_cash_equivalent=['Cash'],
    fifo=[],
    lifo=[['book1',15,0.1,0]],
    wma=[['book',10,-1,-1]],
    assets_contra=[],
    liabilities_normal=['Notes Payable','Accounts Payable','Unearned Revenue'],
    liabilities_contra=[],
    equity_normal=['C. R. Byrd, Capital','hashem'],
    comprehensive_income=[],
    equity_contra=[],
    withdrawals=['C. R. Byrd, Drawing'],
    revenues=[],
    service=[['Service Revenue',2,-1,-1]],
    expenses=['Salaries Expense','Rent Expense'],
    gains=[],
    losses=[],
    )

    # s.journal_entry([
    # # ['Cash',1000000,1000000,None],
    # # ['hashem',1000000,1000000,None],
    # # ['Cash',-1000,-1000,None],
    # # ['book',1000,50,'booook'],
    # # ['Cash',-600,-600,None],
    # # ['book',600,50,'booook'],
    # # ['Cash',-180,-180,None],
    # # ['book1',180,25,'booook'],
    # ['Cash',8,8,''],
    # ['book',10,-1,'booook'],
    # ['book1',10,-1,'booook'],
    # ['Service Revenue',10,1,None],
    # ['Cash',10000,10000,''],
    # ['Notes Payable',10000,10000,''],
    # ],
    # # auto_completion=False,
    # # entry_to_correct=s.entry_number()-1,
    # # date=(2020,10,2),
    # # time_in_week_list=[
    # # ['Monday','2:59','02:00'],
    # # ['Wednesday','2:59','0:00'],
    # # ['Wednesday','13:59','10:00'],
    # # ['Friday','3:59','3:00'],
    # # ['Friday','23:59','4:00'],
    # # ['sunDay','10:00','1:00'],
    # # ['SundAy','23:59','20:00'],
    # # ],
    # entry_expair=(2021,10,12),
    # adjusting_method='linear',
    # description='to record the start',
    # invoice_description='the delevery is 1 dollar',
    # name='saba',
    # seller_or_buyer_sites='dowera',
    # seller_or_buyer_location='home',
    # employee_name='hashem'
    # )

    s.financial_statements()
    # print(s.inventory1())
    # print(s.financial_statements())
    # print(s.journal())

    # i should make the revese entry very minimalist or shortcated
    # barcode i will make