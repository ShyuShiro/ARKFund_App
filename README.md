# ARKFund_App
Applet to download, explore, and analyze ARK fund data

# Disclaimer
This app is for exploration, visualization, and analysis of ARK Fund data. I'm in no way trying to provide any financial guidance, nor am I selling this information for any profits. 

This project exists because I'm interested in programming, data science, and personal-finance. This project is aimmed specifically at ARK funds because Cathie Wood has done a phenominal job (in 2020 particularly) at creating a very profitable ETF.

If this project is in any way infringing on ARK investments, I will be unhappy but I will take this project off github and just post a snapshot & summary of what I'm doing instead. I just assume (and its never safe to assume) it is safe to have a public project on this given the information is publicly available for download.

# Background
Cathie Wood has gained a lot of attention in 2020 because of her amazing returns on the various ARK Funds (ARKK, ARKQ, ARKG, ARKF, ARKW, and most recently... ARKX which was just announced!)

Her fund portfolios are publicly available to download at the end of every trading session & you can subscribe to her daily mailing list --- the email report only shows a subset of her transactions (buy/sell) for the session.

# Goal of project:
1) Create an automatic downloading process to get all "*.cvs" files from the various https://ark-funds.com/ webpages.
2) Automatically push all these .csv files into 1 singular database (sqlite3)
3) Create functions to aid in exploration + analysis of the ARK Fund data (Ex: ticker_lookup() allows searching a specific ticker among the entire database & plotting ARK's share count throughout time)
4) Create visualizations for exploration (Ex: portfolio_diff() shows the sector breakdown between 2 provided dates to show how money is shifting within the fund)
5) Run analysis on the data in ARK
-- a) How long (avg) before an investment becomes positive? (Breakdown by small/mid/large cap)
-- b) How big is the drawdown (avg) of an investment before it becomes position? (Breakdown by small/mid/large 
cap)
-- ???
6) Push all this into an applet (Dash/plotly)

# 0 - Getting this to work on your PC
I'm not going to walk through every detail ... but hopefully I'll provide enough to enable you to clone & get this script running on your own computer! (I'm a PC guy, so unfortunately you're on your own Mac & Linux users. It can't be too much different I don't think).

- 1) Clone
- 2) Download python if you don't already have (I'm running 3.9) & set up your PATH environment
- 3) Download all necessary packages (I'm going to list a few, hopefully this is all of them)
	- numpy
	- pandas
	- datetime
	- sqlite3
	- os
	- BeautifulSoup4
	- request
	- finviz
	- matplotlib
	- glob
	- shutil
	- jupyter
	- notebook
	- ipykernel
	- dash (once the applet is finished)
	- plotly (once the applet is finished)
- 4) Change the { python.exe path } and {DownloadArkFunds.py path} paths in "ARKFund_DownloadScheduler.bat" according to your PC paths.
- 5) Follow "Automating Portfolio downloads" for details on how to setup Task Scheduler (or youtube)

# 1 - Automating portfolio downloads (`DownloadArkFunds.py`)

Utilizes `request` in the python library, a little bit of `BeautifulSoup4`, and a a small bit of snooping with F12 in the browser. 

Script purpose is to download the "*.csv" files https://ark-funds.com/ by finding the <a> element with id "ark{}-hcsv" where {} is filled with ['q','w','k','f','g']

To make this __automated__ this project used "Task Scheduler" on Windows10 along with a ".bat" file (`ARKFund_DownloadScheduler.bat`).

.bat file contents:
- { python.exe path } { script.py path }

Meanwhile the Task Scheduler was set to run Daily (even Sat and Sun because you can't specify otherwise). Utilizing the `datetime` package the script is set download only if the weekday (day of the week) is [0,1,2,3,4] --- according to `datetime` moduel Monday = 0 and Friday = 4.

**CSV Files are downloaded to the location of the ".bat" file if you set "Start in specified Location" parameter to where the ".bat" file is during Task Scheduler setup**

*Note: This is not a perfect catch-all solution however as holidays such as Martin Luther King Weekend (01/18/21) fall on Monday and the fund data will download again. This can be handled by identifying unique ".csv" files and only processing if there is a new entry into the database.*

*Note2: To silence the cmd window prompt that opens during Task Scheudler execution -- Set "Security Options" to "Run whether user is logged on or not" and that will stop the cmd window from opening when the task is queued/executed*

# 2 - sectors.db (`ARK Visualizations.ipynb` > `update_sectors()`)

## Function calls:

None

## Details:

The ".csv" files come with headers:
- Date
- Company
- Ticker
- Shares
- Weight(%)

To gain further insight on company investments `finviz` python package was used to gather the sector & market cap for each __unique__ company ticker.

*Note: Not all company investments have finviz info because they are not all NADAQ/NYSE companies. Example -- ticker "ARCT UQ" for a therapuetic holding company. In this case, the python script provides a "NA" for sector*

Because any company's sector doesn't change significantly between subsequent trading periods, this information can be stored in a sectors.db sql database for quick reference.

However, this information will need to be updated periodically -- no current functionality.

# 3 - arkfunds.db (`ARK Visualizations.ipynb` > `update_arkfund()`)

## Function calls:
- update_sectors(): Once today's ".csv" is loaded into memory --- check if any new unique tickers appear & grab sector info for all old/new tickers
- capitalization(): Once today's ".csv" is loaded into memory --- compute market cap & cap-size via `finviz` for all __new__ tickers

## Details:

The .csv files downloaded from (#1) are processed into a sqlite database for efficient storage via `pandas` and `sqlite3`. 

# 4 - Grab data from arkfunds.db (`ARK Visualizations.ipynb` > `see_data(db=0)`)

## Function calls:
- None

## Arguements:
- db = which database to grab from (0 = arkfunds.db | 1 = sectors.db)

## Details:
A simple quick "SELECT * FROM {db}" query.

Once the database is sufficiently large ... this function will expand to include a time-frame parameter so that >1 yr of data is not queried each time.

## Output:
- pd dataframe of queried data

# 5 - ticker visualization (`ARK Visualizations.ipynb` > `ticker_lookup(tickers,together=True,funds=None)`)

## Function calls:
- see_data()

## Arguements
- tickers = list of tickers to visualize.
- together = Whether or not all funds should be grouped into a singular plot per ticker (default = True = Singular plot per ticker).
- funds = Which ARK fund(s) to include in the ticker search (default = None = All 5 ARKK/Q/F/G/W funds)

## Details:
Function provides a date vs kilo-shares (x,y) plot for all tickers/funds requested. 1 kilo-share = 1000 shares.

Currently the function does not accept parameters for date(s). However in the future dates OR a limiter such as "previous 15 trading sessions" will need to be used to prevent charts from showing too much.

## Output:
- Chart(s) of tickers throughout fund's timeline.
- The pandas df utilized to generate each chart is provided as output as well --- in case another function can utilize the output for its input in the future

# 6 - sector investment changes (`ARK Visualizations.ipynb` > `portfolio_diff(date1,date2,fund='ARKG')`)

## Function calls:
- see_data()

## Arguements:
- date1 = Initial date
- date2 = Final date
- fund = ['ARKK','ARKQ','ARKW','ARKF','ARKG'] (Default = "ARKG")

## Deatils:
Function provides a snapshot difference of the sectors of date1 vs date2.

*Note: the .csv files have a `weight` column which is suppose to tally to 100%, but totals to numbers like 96% instead. The pie chart shows the portfolio makeup according to the information provided (ie: If the given date's ['weight(%)'] column only sums to 96%, the pie will automatically standardize the values and sum to 100%)*

## Output:
- Pie charts of date1 and date2 for the sector investment in a specific fund.
- pandas df printout of the change in sector investments (positive = moneyflow into the sector | negative = moneyflow out of the sector | eg: "Technology +0.15" would suggest a 0.15% increase of weight = moneyflow)

# 7 - Share changes, New positions, Closed positions (`ARK Visualizations.ipynb` > `change_in_portfolio(date1,date2,fund=None)`)

## Function calls:
- see_data()

## Arguments:
- date1 = Initial date
- date2 = Final date
- fund = ['ARKK','ARKQ','ARKW','ARKF','ARKG'] (Default = None = All 5 funds)

## Details:
Compare the data from date1 and date2 and note any differences. In special cases, ARK funds can open a new position in a ticker or even close their position all-together in a ticker. As investors, it signals as a "good buy opportunity" if ARK is investing into a brand new ticker. Similarly it suggests a "good short opportunity" if ARK no longer invests into a fund (suggesting maybe the investment is no longer worth it))

## Output:
3 dataframes
- Changes = simple share differences (ie: Buy & Sells)
- new = any new positions opened between the 2 dates
- closed = any positions which share size diminished to 0 between the 2 dates
