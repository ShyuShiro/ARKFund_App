def set_dir(path=""):
    import os
    if path != "":
        os.chdir(path)
    else:
        pass #Keep directory as current working directory

def see_data(db=0): #Function to view the data in the database easily
    import sqlite3
    import pandas as pd
    
    set_dir()
    
    if db == 0:
        db_name = "ARKFund.db"
        db_table = "arkfunds"
    elif db == 1:
        db_name = "sectors.db"
        db_table = "sectors"
        
    conn = sqlite3.connect(db_name) #Connect
    df = pd.read_sql_query('SELECT * FROM ' + db_table,conn)
    #display(df) #Print all data
    conn.close()
    return df

def capitalization(ticker): #Determine cap size of company
    import finviz
    import yfinance as yf
    
    try: #finviz approach
        info = finviz.get_stock(ticker)['Market Cap'] #Get market cap

        #Split market cap to take only whole number
        l,r = info.split('.')
        valuation = int(l) #Left of the decimal place
        units = r[-1] #Units ("M" or "B")

        #Nano is less than 50M ... dont think i need to classify this though
        #Micro is anything 300M and less
        #Small is [300M,2B]
        #Mid is [2B,10B]
        #Large is everything else
        if units == "M":
            if valuation <300:
                cap = "Micro"
            else:
                cap = "Small"
        elif units == "B":
            if valuation < 2:
                cap = "Small"
            elif valuation <= 10:
                cap = "Mid"
            else:
                cap = "Large"
        elif units == "T": #Companies like AAPL are 2151B ... but just in case finviz ever updates to trillion
            cap = "Large"
        else:
            cap = "Nano" #Catch case if something else shows up ... would have to assume Nano cap
    except: #If finviz is unable to gather the information ... try yfinance
        try:
            valuation = yf.Ticker(ticker).info['marketCap']
            if valuation/1000000000>10: #Greater than 10B company
                valuation = valuation/1000000000
                cap = "Large"
                units = "B"
            elif valuation/1000000000>2: #Greater than 2B company
                valuation = valuation/1000000000
                cap = "Mid"
                units = "B"
            elif valuation/1000000000>0: #In the billion range
                valuation = valuation/1000000000
                cap = "Small"
                units = "B"
            else:
                if valuation/1000000>300: #Greater than 300M company
                    valuation = valuation/1000000
                    cap = "Small"
                    units = "M"
                else:
                    valuation = valuation/1000000
                    cap = "Micro"
                    units = "M"
            valuation = int(str(valuation).split('.')[0]) #Finalize the valuation as an integer of the whole number value
        except: #If yfinance doesnt work -- simply state "NA"
            cap = "NA"
            valuation = "NA"
            units = ""
        
    return cap,str(valuation)+units #Cap = classification | MarketCap

def update_sectors(df):
    '''
    Function to check if any new unique tickers exist
    -- If not, do nothing
    -- If so,
    ---- Utilize finviz to find sector info for ticker
    ---- Update the sectors.db to include this unique ticker
    '''
    import finviz
    import yfinance as yf
    import os
    import sqlite3
    import pandas as pd

    set_dir()
    
    if "sectors.db" in os.listdir():
        #Connect to db
        conn = sqlite3.connect('sectors.db')

    else:
        #Create db
        conn = sqlite3.connect('sectors.db') #Yes ... its the same line of code to connect or create

        #Create cursor
        c = conn.cursor()

        #Define table structure
        c.execute('''CREATE TABLE sectors (ticker TEXT, sector TEXT, cap TEXT, market_cap INT)''')
        conn.commit() #save

    print("update_sectors():")
    print("\t--- Connection to sector db established ---")

    #Grab db info
    sector_tickers = pd.read_sql_query("SELECT * FROM sectors ORDER BY ticker",conn)
    
    if len(df) < 1: #No df to process
        #Find all unique tickers in the database
        data_to_process = False
    else:
        data_to_process = True
    
    if data_to_process:
        
        #Clean up the ticker column of dataframe
        df['ticker'] = df['ticker'].str.split().str.get(0) #Split & grab the first word of the ticker column to save as ticker
            #This converts things like "TAK UN" to "TAK" while still keeping things like "AAPL" as "AAPL"
        
        #Now find unique entries
        tickers = df['ticker'].unique() 

        missing = []
        print("\tChecking if tickers need updating")
        for i in tickers:
            if i not in sector_tickers['ticker'].unique():
                missing.append(i) #Add all new tickers to "missing"
                if len(missing) == 1: #If a new ticker is found, do a printout notification
                    print("\t\tNew tickers found")

        sector = []
        cap_designation = []
        valuation = []
        if len(missing) < 1:
            print("\t\tNo new tickers to update")
        else:
            print("\tSearching sector & capitalization info for %d tickers"%len(tickers))
            for i in missing: #For each ticker missing, attempt to find the sector for it
                print("\t\t"+i+" --- ",end='')
                try:
                    sec = finviz.get_stock(i)['Sector']
                    c,m = capitalization(i)
                except: #If finviz cannot find the information, try yfinance
                    try:
                        sec = yf.Ticker(i).info['sector']
                        c,m = capitalization(i)
                    except: #If neither can find information --- set "NA"
                        sec = "NA" #Some tickers like "8994" will not pull up a result
                        c = "NA"
                        m = "NA"
                cap_designation.append(c)
                valuation.append(m)
                sector.append(sec)
                print(sec) #Attach the sector to the printout
            
        #Update the df
        sector_tickers = sector_tickers.append(pd.DataFrame({'ticker':missing,
                                                             'sector':sector,
                                                             'cap':cap_designation,
                                                             'market_cap':valuation}),ignore_index=True)

        #Format the df a bit
        sector_tickers = sector_tickers.sort_values(by='ticker').reset_index(drop=True) #sort by ticker & reset index

        #Write to db
        sector_tickers.to_sql(name='sectors', con=conn, if_exists='replace', index=False)

        conn.commit() #Save
        print("\tSector information has been updated")
    
    #Close connections   
    conn.close()
    print("\tConnection to sectors.db has been closed")
    
    return sector_tickers

def backup_data():
    '''
    Run every so often to backup the ARKFunds.db and Sectors.db files
    '''
    from shutil import copyfile
    import datetime
    
    set_dir() #Make sure directory is set appropriately
    
    today = datetime.datetime.today()
    
    if today.weekday() == 4: #If day of week is Friday
        print("backup_data() activated --- backing up databases because it is Friday")
        copyfile("ARKFund.db","Backups/"+today.date().isoformat()+" ARKFund.db")
        copyfile("sectors.db","Backups/"+today.date().isoformat()+" sectors.db")
        print("\tData has been backedup for today: ",today.date().isoformat())
    else:
        pass     #Backup both ".db" files (executes on Friday)

def change_in_portfolio(date1=None,date2=None,fund=None,debug=False):
    '''
    Functionality for `fund` argument built in ... but not fully tested
    '''
    import numpy as np
    import pandas as pd
    
    df = see_data(0) #Grab all data in SQL database
    unique_dates = df['date'].unique()
    df['date'] = df['date'].astype('datetime64[ns]') #Convert date to datetime object
    df = df.sort_values(by='date',ascending=True).drop(['sector','market_cap','weight'],axis=1) #Sort ascending dates & drop unnecessary columns
    
    #If no dates provided
    if date1 == None or date2 == None:
        date1 = unique_dates[-2] #Previous trading session
        date2 = unique_dates[-1] #Most recent trading session
    
    #If dates provided are short-hand .... add the year to them
    def add_year(date):
        import datetime
        year = datetime.datetime.today().year
        return date+"/"+str(year)
    if len(date1)<7:
        date1 = add_year(date1)
    if len(date2)<7:
        date2 = add_year(date2)
    
    #To account for "New" positions opened... the date BEFORE date1 needs to be referenced.
    #Ex: If a new position is opened on 1/11 ... how do you know it is new unless you can confirm from 1/10 that a position was not previously held
    loc_initial_date = np.where(np.array(unique_dates)==date1)[0][0]-1 #Minus 1 to reach the previous date
    
    if loc_initial_date == -1:
        loc_initial_date += 1 #change to 0 index if it is the first date
    
    #If no fund provided, simply search by dates
    if fund == None:
        #Grab subset info for the dates
        a = df[(df['date']==date1)]
        b = df[(df['date']==date2)]
    else:
        #Grab subset info for the specified fund
        a = df[(df['date']==date1)&(df['fund']==fund)]
        b = df[(df['date']==date2)&(df['fund']==fund)]
    
    #Compare via `how='outer'`
    diff = a.merge(b,how='outer',on=['fund','company','ticker','cap'],indicator=False) #Determine differences between the 2 dates
    diff['change'] = diff['shares_y']-diff['shares_x'] #Compute change in shares
    diff['percent_change'] = np.round(np.divide(100*diff['change'],diff['shares_x']),2)
    
    #Pick only select columns
    #diff = diff[['date_x','date_y','fund','ticker','shares_x','shares_y','change']]
    
    #Create new DF with appropriate column headers
    changes = diff.rename(columns={'shares_x':"shares_then","shares_y":"shares_now",
                                'date_x':"start_date","date_y":"end_date"}) #Rename for clarity
    changes = changes[['start_date','end_date','fund','company','ticker','shares_then','shares_now','change','percent_change','cap']]
    changes = changes[changes['change']!=0] #Drop any rows which have no action (ie: Change = 0 because no change in shares)
    
    ###Determine positions that are new
    new = changes[pd.isna(changes['shares_then'])] #All positions which didn't have shares before are new
    
    # Compute a sliced df containing only dates between [date1,date2] for use in `new` and `closed` dfs
    #Subset the original df to be between these 2 dates
    df = df[(df['date']>=unique_dates[loc_initial_date])&(df['date']<=date2)] #This new df is used to compute new & closed positions
    
    #Compute the date these positions opened
    initiation_date = []
    for i,row in new.iterrows():
        subset = df[(df['ticker']==row['ticker'])&(df['fund']==row['fund'])] #Find this subset in the sliced [date1,date2] df
        initiation_date.append(subset.iloc[0]['date'])

    new = new[['fund','ticker','shares_now']] #Drop the useless information (NaN columns)
    new = new.rename(columns={'shares_now':'shares_initiated'}) #rename column
    new['initiation_date'] = initiation_date #Create a new column with the date of position start
    new = new.sort_values(by='initiation_date',ascending=False) #Sort df by open dates
    
    ###Determine positions that closed
    closed = diff[pd.isna(diff['shares_y'])==True] #All positions which no longer have shares on today's date are closed
    #Determine date the position(s) were closed
    sell_date = []
    for _,row in closed.iterrows():
        subset = df[(df['ticker']==row['ticker'])&(df['fund']==row['fund'])] #Find all instances of the closed ticker position
        sell_date.append(subset['date'].iloc[-1]) #The final entry's date is the close date

    closed = closed[['fund','ticker','shares_x']].rename(columns={'shares_x':"shares_before_sale"}) #Drop unnecessary columns
    closed['close_date'] = sell_date #Create column
    closed = closed.sort_values(by='close_date',ascending=False) #Sort data
    
    ##Update Change df to not include new or closed positions
    #The rows that would exist in "new" and "closed" are present in "changes" as well -- eliminate by finding all non-NaN entries
    changes = changes[pd.isna(changes['change'])==False] #Make the "changes" df have all changes that arent new/closed

    ##Determine what are `significant` transactions to keep an eye on
    alerts = changes.copy() #Copy the df
    changes = changes.drop(['cap','company'],axis=1) #Drop the last few columns on Change column that arent necessary
    alerts = alerts[(np.abs(alerts['percent_change'])>=10)|((np.abs(alerts['percent_change'])>=4.5)&(alerts['cap']=='Small'))].sort_values(by=['percent_change'],ascending=False).reset_index(drop=True)
    
    if debug: #Just making a quick method to print all 4 df results accordingly
        print("dates:")
        print(date1,date2)
        print("Changes:")
        display(changes)
        print("New positions:")
        display(new)
        print("Closed positions:")
        display(closed)
        print("Alerts:")
        display(alerts)
    
    return changes, new, closed, alerts
    
def update_capitalization(manual_update=False):
    """
    Function to update capitalization & market cap for ALL stocks in the database
    Recommend running once in a while ... maybe once a week?
    
    Why run this?
    Companies may break the barrier from Small -> Mid or drop from Mid -> Small (since the bound is only 2B to 10B for small)
    """
    import pandas as pd
    import numpy as np
    import sqlite3
    import datetime
    
    today = datetime.datetime.today().weekday()
    
    #Check if "update_capitalization" has run today by checking if today's date exists in the checkbox.csv file
    now = datetime.datetime.now()
    d = pd.read_csv('Logs/capitalization_checkbox.csv') #Read the file
    date_now = now.strftime("%m/%d/%Y") #Convert today's date to "MM/DD/YYYY" format

    go_ahead = False #Set boolean value
    if manual_update == True: #If manual updating ... update the log
        if date_now in d['date'].values:
            print("Date already exists -- manual updating request denied")
        else:
            go_ahead = True #Else update
    
    if manual_update=="disable": #'disable' feature is kind of usless now that the checkbox.csv file exists, oh well~
        pass
    else:
        if today == 4 or go_ahead==True:
            
            #Check if today's date exists already
            if date_now in d['date'].values:
                go_ahead = False #If so, don't execute again
            else:
                d = d.append({'date':date_now,'ran':'yes'},ignore_index=True) #If not, update the file and run capitalization update
                d.to_csv("Logs/capitalization_checkbox.csv",index=False) #Write the file
                go_ahead = True
            
            if go_ahead == True: #manual_update==True disregards both 
                print("update_capitalization():")
                print("\tUpdating capitalization information for entire database")
                conn = sqlite3.connect("ARKFund.db")
                conn2 = sqlite3.connect("sectors.db")
                df = pd.read_sql_query("SELECT * FROM arkfunds",conn)
                print("\tConnection to ARKFund.db established")
                sectors = pd.read_sql_query("SELECT * FROM sectors",conn2)
                print("\tConnection to sectors.db established")

                #Create placeholder lists
                c = [] #Cap designation (Eg: Small)
                m = [] #Market cap value (Eg: 1B)

                count = 0
                total = len(sectors['ticker'])
                print("\tUpdating %s tickers:"%total)
                for i in sectors['ticker']:
                    if count%25 == 0: #Every 25 rows, update the progress
                        print("\t\t%.2f/100%%"%(np.round(count/total,2)*100))
                    try:
                        cap_designation,market_cap = capitalization(i)
                    except:
                        cap_designation,market_cap = ["NA","NA"]
                    c.append(cap_designation)
                    m.append(market_cap)
                    count += 1

                print("\t\tDone finding capitalizations -- Merging to `sectors` database")
                sectors['cap'] = c
                sectors['market_cap'] = m

                print("\tWriting results to sectors.db")
                sectors.to_sql(name='sectors',con=conn2,if_exists='replace',index=False)
                print("\t\tSectors.db updated successfully")

                #Create dictionaries to map (Ticker --> Cap) and (Ticker --> Market_cap)
                dct_cap = dict(sectors[['ticker','cap']].to_dict('split')['data']) # dct of {'AAPL':'Large', ... , 'ZM':'Large'}
                dct_market_cap = dict(sectors[['ticker','market_cap']].to_dict('split')['data']) #dct of {'AAPL':'2180B', ... , 'ZM':'114B'}

                df = df.drop(['cap','market_cap'],axis=1) #Drop the cap and market_cap columns because we'll be updating them

                #Re-create the columns via mapping
                df['cap'] = df['ticker'].map(dict(dct_cap))
                df['market_cap'] = df['ticker'].map(dict(dct_market_cap))

                print("\tWriting results to ARKFunds.db")
                df.to_sql(name='arkfunds', con=conn, if_exists="replace", index=False)
                print("\t\tARKFund.db updated successfully")

                #Now actually save the data (even though printouts have been saying its been successful)
                conn.commit()
                conn2.commit()

                conn.close()
                conn2.close()
                print("\tDatabase connections closed successfully")
        else:
            pass #Dont execute unless it's Friday
        
def ticker_lookup_dash(tickers,date1=None,date2=None,together=True,funds=None):
    '''
    This version of `ticker_lookup` instead only returns the dataframe (no plot)
    
    Dash cannot use matplotlib plots =/
    '''
    import pandas as pd
    import datetime
    import numpy as np
    
    if type(tickers)==str:
        tickers = [tickers]
    
    #load & sort data
    df = see_data() #Grab all data in ARKFund.db
    df['date'] = df['date'].astype('datetime64[ns]') #Convert date to datetime object so data can be sorted
    df = df.sort_values(['date','fund'],ascending=True) #Sort by ascending date

    #If a date or dates are provided, truncate the search
    if date1 is not None:
        if date2 is None:
            df = df[df['date']>=date1]
        else:
            df = df[(df['date']>=date1)&(df['date']<=date2)]

    def log_reduction(val): #Reduce the y-axis by a factor of X
        import numpy as np
        reduced = [np.round(i/1000,2) for i in val] #Reduce share size by factor of 1000
        return reduced
    def timestamp_to_MonthDay(lst): #Convert "2021-01-14 00:00:00" to "01/14" for all elements in a list
        return [i.strftime("%m/%d") for i in lst]
    
    all_df = pd.DataFrame()
    for ticker in tickers:
        subset = df[df['ticker']==ticker.upper()].groupby('fund')
        for _,r in subset:
            #shares = log_reduction(r['shares'])
            shares = r['shares']
            dates = timestamp_to_MonthDay(r['date']) #This converts the correct x-axis from [0,1,2,...,n] to appropriate labels                
            all_df = all_df.append(pd.DataFrame({'fund':r['fund'],'date':dates,'shares':shares})) #df to return in case its useful
    return all_df
    
def store_logs(changes,new,closed,alerts):
    '''
    function to save closed, opened, and changes to .csv output
    
    reasoning:
        -A closed position may not remain closed ... it may re-open in the future
            -These would be captured once as a closed ... but not necessarily an opened position in the future (may need to adjust code when that happens)
    '''
    import datetime
    import pandas as pd
    set_dir()
    
    #Define some parameters
    d = datetime.datetime.today().date()
    base = str(d.year) + "-" + str(d.month) + "-" + str(d.day)
    dirr = "Logs/"
    dirr2 = "Logs/alerts/"
    dirr3 = "Logs/changes/"
    
    #Load in previous logs for new & closed positions
    df_new = pd.read_csv(r"Logs\new_positions.csv")
    df_closed = pd.read_csv(r"Logs\closed_positions.csv")
    
    #Need to convert str to datetime64[ns]
    df_new['initiation_date'] = df_new['initiation_date'].astype('datetime64[ns]')
    df_closed['close_date'] = df_closed['close_date'].astype('datetime64[ns]')
    
    #Append data together
    new = new.append(df_new).sort_values(by='initiation_date',ascending=False)
    closed = closed.append(df_closed).sort_values(by='close_date',ascending=False)
    
    #Delete any duplicate entries
    new = new.drop_duplicates(ignore_index=True)
    closed = closed.drop_duplicates(ignore_index=True)
    
    #Changes and alert can just be regularly updated (because I'll have a log date associated to these files)
    changes.to_csv(dirr3 + base+" changes.csv",index=False)
    alerts.to_csv(dirr2 + base + " alerts.csv",index=False)    
    new.to_csv(dirr + "new_positions.csv",index=False)
    closed.to_csv(dirr + "closed_positions.csv",index=False)
    print("Daily changes, new/closed, and alert positions have been saved")
    
def compute_transactions(ticker,start_date,end_date):
    transaction_log = see_data() #Grab all data
    
    #Filter by ticker
    transaction_log = transaction_log[transaction_log['ticker']==ticker]
    
    #Filter by date
    transaction_log['date'] = transaction_log['date'].astype("datetime64[ns]")
    transaction_log = transaction_log[(transaction_log['date']>=start_date)&(transaction_log['date']<=end_date)]
    
    #Grab only select columns & sort by fund then date
    transaction_log = transaction_log[['date','fund','shares','weight']].sort_values(by=['fund','date'])

    #Compute transactions
    transactions=[]
    for fund,subset in transaction_log.groupby('fund'):
        transactions.append(subset['shares'].diff().values) #Compute difference in share price each day per fund

    #Flatten the list of lists and create column from that information
    transaction_log['change_in_shares'] = [item for sublist in transactions for item in sublist]
    
    #Clean up transactions
    transaction_log = transaction_log.dropna() #Drop NaN values (initialization of position)
    transaction_log = transaction_log[transaction_log['change_in_shares']!=0] #Drop 0's as they mean no transaction occured
    
    #Rename 'shares' to 'total_shares'
    transaction_log = transaction_log.rename(columns={'shares':'shares_after_transaction'})
    
    #Reorganize columns
    transaction_log = transaction_log[['date','fund','weight','change_in_shares','shares_after_transaction']]
    
    return transaction_log
      
def update_arkfund(display_changes=False,manual_update=False,path = r"C:\Users\Brandon\Desktop\ARK Fund CSV Files"):
    import glob
    import os
    import sqlite3
    import pandas as pd
    import finviz
    
    #Change directory
    set_dir(path=path)

    #Load all excel files & Concat together
    files = glob.glob("*.csv") #Find all

    if "ARKFund.db" in os.listdir():
        #Connect to db
        conn = sqlite3.connect('ARKFund.db')

        #Create cursor object
        c = conn.cursor()
    else:
        #Create db
        conn = sqlite3.connect('ARKFund.db') #Yes ... its the same line of code to connect or create

        #Create cursor
        c = conn.cursor()

        #Define table structure
        c.execute('''CREATE TABLE arkfunds 
            (date TEXT, fund TEXT, company TEXT, ticker TEXT, shares INTEGER, weight REAL, sector TEXT,cap TEXT, market_cap INT)
                ''')
        conn.commit() #save

    print("--- Connection to ARKFunds.db established ---")

    print("Processing %.0f files:"%len(files))

    existing_files = glob.glob("Processed\*.csv")
    existing_files = [i[10:] for i in existing_files]
    
    df_all = pd.DataFrame()
    new_data=False #Set default switch
    for file in files:
        if file not in existing_files:
            df = pd.read_csv(file) #Read csv file
            df_all = df_all.append(df) #Append to mega df
            new_data=True
        else:
            print("\t%s already exists in the database -- Removing file"%file)
            os.remove(file)
            print("File: %s has been deleted"%file)            
            
    if new_data: #If there is data to process
        #Grab sector info
        #1) Check if there are any new unique tickers that havent existed before
        #2) Grab the info if new tickers
        
        #Clean up the ticker column of dataframe
        df_all['ticker'] = df_all['ticker'].str.split().str.get(0) #Split & grab the first word of the ticker column to save as ticker
            #This converts things like "TAK UN" to "TAK" while still keeping things like "AAPL" as "AAPL"
        
        sectors = update_sectors(df_all) #Use the function to update any ticker that didnt exist AND obtain df of [ticker,sector]
        
        #Match "Ticker" in arkfunds.db to "sector" from sectors.db
        sec = []
        for i in df_all['ticker']:
            try:
                sec.append(sectors[sectors['ticker']==i]['sector'].iloc[0])
            except:
                sec.append("NA")
        print("Updating ARKfund with Sector.db info")
        df_all['sector'] = sec #create a new column called "sector" by matching the `ticker` to `sector`
        
        #Convert date column into datetime object 
        #df_all['date'] = df_all['date'].astype("datetime64[ns]") 
        ###Does not work! -- SQLite3 can only accept types TEXT, INT, REAL ... this results in datetime --> TEXT upon saving
        
        print("Computing capitalization of new data")
        #Do this by loading in sectors.db data and grabbing the data from there (already loaded as sectors)
        cap_designation = []
        valuation = []
        count = 2
        total = len(df_all['ticker'])
        for i in df_all['ticker']: 
            if count%50 == 0 or count == total: #Provide progress updates
                print("\t%s/%s"%(count,total))
            temp = sectors[sectors['ticker']==i]
            cap_designation.append(temp['cap'].iloc[0])
            valuation.append(temp['market_cap'].iloc[0])
            count += 1
        
        df_all['cap'] = cap_designation
        df_all['market_cap'] = valuation
        
        #Rename 'weight(%)' to 'weight'
        print("Renaming weight(%) to weight")
        df_all = df_all.rename(columns={"weight(%)":"weight"})

        #Update ARKFunds.db database
        print("Writing results to database")
        df_all.to_sql(name='arkfunds', con=conn, if_exists='append', index=False)

        conn.commit() #Save database
        
        #Now that all the work has been done, move the files (do this last to avoid double entry of files)
        for file in files:
            os.rename(file, "Processed/"+file) #Move csv file to the processed folder so it doesn't read next time
            print("\t%s has been uploaded"%file)
    else:
        print("No new data to process")
        sectors = see_data(1) #Grab sectors data to provide as output

    conn.close() #Close SQLite Database connection
    print("--- Connection closed ---")
    print("SQL Database has been successfully updated.")
    
    #Backup servers as necessary (Current trigger is: Friday (weekday == 4))
    update_capitalization(manual_update=manual_update) #Updates all info for sectors.db then ARKFund.db ... a bit redundant because we just loaded data today (but runs quite fast)
    backup_data() #function checks weekday and returns nothing if weekday != 4 ... it backs up both ".db" files
    
    changes, new, closed, alerts = change_in_portfolio() #Determine changes, new positions, closed positions, alerts
    store_logs(changes,new,closed,alerts)
    if display_changes:
        print("New positions:")
        display(new)
        print("Closed positions:")
        display(closed)
        print("Alerts:")
        display(alerts)
        
    return df_all,sectors, changes, new, closed, alerts #df_all = df of newly appended data .. NOT the data in arkfunds.db | sectors = sector all info from sectors.db
