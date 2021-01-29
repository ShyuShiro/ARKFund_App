
#Load packages
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import json
import csv
import numpy as np
import datetime

while True: #While or For loops are required to make a "break" statement ... unfortunately
    #Script only needs to be run on the weekdays
    today = datetime.datetime.today().weekday() #Grab today's day of the week
    if today == 5 or today == 6: #If today is a weekend
        quit() #quit python
        break #exit program

    #If weekday -- continue to run the actual script
    
    #Define URL links
    URL_base = "https://ark-funds.com/ark"
    funds = ['q','k','w','g','f']
    URLS = [URL_base+i for i in funds]
    print("The url to the funds are:")
    print(URLS)

    #Create functions to help in processing
    def get_soup(url): #Function to grab the HTML off a url
        return bs(requests.get(url).text,'html.parser') #Read the html of a webpage

    def grab_csv(url): 
        '''
        Function to grab the csv file on the HTML page 
        via finding the id associated to the csv file
        Ex: "arkk-hcsv" for ARKK
        Ex2: "arkw-hcsv" for ARKW
        '''
        for link in get_soup(url).find_all('a'): #Grab all <a> elements
            file_link = link.get('id') #Find specific id
            if file_link != None and "csv" in file_link: #Id containing "csv"
                csv_url = link.get('href') #Grab url
        return csv_url

    #Now that the functions have been created ...
    #> 1) Grab the CSV files <br>
    #> 2) Clean them up <br>
    #> 3) Append into 1 data table

    all_df = pd.DataFrame() #Singular df to hold all the different tables
    for URL in URLS: #For each ARK fund
        csv_file = grab_csv(URL) #Grab csv file
        with requests.Session() as s: #Process CSV contents
            download = s.get(csv_file) #Download the csv
            decoded_content = download.content.decode('utf-8') #decode it
            cr = csv.reader(decoded_content.splitlines(), delimiter=',') #Read as csv


            my_list = list(cr) #Convert to list object

    #        for row in my_list: #Debug printing
    #            print(row)

            #Clean up the output
            df = pd.DataFrame(my_list[1:],columns=my_list[0]) #Convert to df
            df = df.drop(['cusip','market value($)'],axis=1) #Dont care for these columns
            df = df[:-3] #drop bottom 3 rows about legal information

            #Change the empty tickers such as "Japanese Yen" and "Morgan Stanly GOVT" to NaN
            df['ticker'].replace('', np.nan, inplace=True) #Convert empty to nan

            #Change the numeric tickers such as "3690" and "4477" for Meituan and Base INC to NaN
            df['ticker'].replace("\d",np.nan,regex=True,inplace=True)

            #Drop NaNs that were just created
            df = df.dropna() #Drop nan

            #Finally append to singular df
            all_df = all_df.append(df)

        #Write singular dataframe to file
        all_df = all_df.sort_values("ticker")
        all_df = all_df.reset_index(drop=True) #Reset the index 
        all_df.to_csv(df['date'][0].replace("/","-")+" ARK data.csv",index=False)

    #Print confirmation of completion
    print("Funds have been downloaded for date of ",df['date'][0])
    break #Exit while loop after 1 loop ... only used the while loop to instate the weekday vs weekend condition

#Now update the database

#To be able to import the ARK.py file and its modules, the directory needs to be added to PATH
import os
import sys
module_path = os.path.abspath(r'C:\Users\Brandon\Desktop\ARK Fund CSV Files')
if module_path not in sys.path:
    sys.path.append(module_path)

#Now import ARK.py functions
from ARK import *

#Run main script which will process today's file and update necessary data tables
_,_,_,_,_,_ = update_arkfund(display_changes=False,manual_update=False)