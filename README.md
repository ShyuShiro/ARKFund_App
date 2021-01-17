# ARKFund_App
Applet to download, explore, and analyze ARK fund data


# Background
Cathie Wood has gained a lot of attention in 2020 because of her amazing returns on the various ARK Funds (ARKK, ARKQ, ARKG, ARKF, ARKW, and most recently... ARKX which was just announced!)

Most profound of all, her funds are publicly available to download at the end of every trading session & you can subscribe to her daily mailing list --- showing a subset of her transactions (buy/sell) for the session.

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
