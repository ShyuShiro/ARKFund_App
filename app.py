import dash
import plotly
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
from datetime import date, timedelta, datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
import numpy as np

#To be able to import the ARK.py file and its modules, the directory needs to be added to PATH
import os
import sys

path = r'C:\Users\Brandon\Desktop\ARK Fund CSV Files'
module_path = os.path.abspath(path)
if module_path not in sys.path:
    sys.path.append(module_path)

#Now import ARK.py functions
from ARK import *

def start_up():
    '''
    Wrapper function to execute updating of database & tables
    '''
    set_dir(path) #Set directory

    #Before loading the applet -- Run the main function
    df_today,sectors,changes,_,_,alerts = update_arkfund(display_changes=False,manual_update=False) #Leaving `path` argument as default

    #Grab new/close position log files
    new = pd.read_csv(r"Logs\new_positions.csv") #Load in the full log file of new positions
    closed = pd.read_csv(r"Logs\closed_positions.csv") # --------- of the closed positions

    #Sort the changes df by ticker
    changes = changes.sort_values(by='ticker')

    #Remove unnecessary start vs end date columns for Changes & Alerts
    current_trading_session = changes['end_date'].iloc[0] #Grab the trading session info for reference
    current_trading_session = str(current_trading_session)[:10] #Truncate to YYYY-MM-DD from the original datetime64 obj.
    changes = changes.drop(['start_date','end_date'],axis=1)
    alerts = alerts.drop(['start_date','end_date'],axis=1)

    df = see_data() #Load all of ARKFund.db as df

    if df_today.empty: #If this script runs without loading a some data
        df_today = df[df['date']==df['date'].iloc[-1]]
    return df_today,sectors,changes,alerts,df,current_trading_session,new,closed

df_today,sectors,changes,alerts,df,current_trading_session,new,closed = start_up() #Run on start up of dash app
    
#Load in dash app with external CSS elements
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#Define some theme settings
colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'button':'#D6D8DC',
    'sell': '#ff6666',
    'buy': '#99ff99',
    'big_buy': '#00ff00',
    'big_sell': '#ff4d4d',
    }

fund_colors = {
    'ARKK': '#33adff', #Fund 1 - Steel blue
    'ARKQ': '#ffaa80', #Fund 2 - Tan
    'ARKW': '#deb0ff', #Fund 3 - light purple
    'ARKG': '#cccc00', #Fund 4 - Yucky Yellow (LOL)
    'ARKF': '#46e4f0', #Fund 5 - Teal
}

#Define formatting for tables (https://dash.plotly.com/datatable/conditional-formatting)
base_table_formatting=[ #Base formatting that is going to be similar across all tables
        {
            'if': {
                'row_index': 'odd',  # number | 'odd' | 'even'
            },
            'backgroundColor': 'rgba(175,175,175,0.7)',
        },    
    
        {
            'if': {
                'column_type': 'text'  # 'text' | 'any' | 'datetime' | 'numeric'
            },
            'textAlign': 'left'
        },
    
        {
            'if': {
                'column_type': 'numeric'  # 'text' | 'any' | 'datetime' | 'numeric'
            },
            'textAlign': 'center'
        },

        {
            'if': {
                'state': 'active'  # 'active' | 'selected'
            },
           'backgroundColor': 'rgba(0, 116, 217, 0.3)',
           'border': '1px solid rgb(0, 116, 217)'
        },
    
    ]
for i,j in fund_colors.items():
    base_table_formatting.append(
        {
            'if': {
                'filter_query': '{fund} = %s'%i  # If fund is equal to i-th key
            },
           'backgroundColor': '%s'%j, #Set color to the j-th value
        },
    )

#Define formatting for transaction table
transaction_table_formatting = base_table_formatting.copy()
transaction_table_formatting.append(
        {
            'if': {
                'filter_query': '{change_in_shares} > 0', # If transaction is positive
                'column_id': 'change_in_shares'
            },
            'backgroundColor': colors['buy'] #Color as buy
        }
)
transaction_table_formatting.append(
        {
            'if': {
                'filter_query': '{change_in_shares} < 0', # If transaction is negative
                'column_id': 'change_in_shares'
            },
            'backgroundColor': colors['sell'] #Color as sell
        },    
)

#Define formatting for changes table
changes_table_formatting = base_table_formatting.copy()
changes_table_formatting.append(
        {
            'if': {
                'filter_query': '{change} > 0', # If change is positive -- buy color
                'column_id': ['change','percent_change']
            },
            'backgroundColor': colors['buy']
        }
)
changes_table_formatting.append(
        {
            'if': {
                'filter_query': '{change} < 0', # If change is negative -- sell color
                'column_id': ['change','percent_change']
            },
            'backgroundColor': colors['sell']
        },  
)


#Define formatting for alerts table
alerts_table_formatting = base_table_formatting.copy()
alerts_table_formatting.append(
        {
            'if': {
                'filter_query': '{change} > 0', # If change is positive -- buy color
                'column_id': ['change','percent_change']
            },
            'backgroundColor': colors['buy']
        }
)
alerts_table_formatting.append(    
        {
            'if': {
                'filter_query': '{change} < 0', # If change is negative -- sell color
                'column_id': ['change','percent_change']
            },
            'backgroundColor': colors['sell']
        },
)

min_date = date(2021,1,4) #Hard code ... this is the earliest date of data in ARKFund.db 
max_str = datetime.strptime(df['date'].iloc[-1], '%m/%d/%Y') #Define max date as the most current date in the database
max_date = date(max_str.year,max_str.month,max_str.day) #Convert to datetime obj

app.layout = html.Div(children=[
    #Row 1    
    dbc.Row([ 
        dbc.Col(
            #Date selector
            html.Div([
                dcc.DatePickerRange(
                    id='date1',
                    min_date_allowed=min_date,
                    max_date_allowed=max_date+timedelta(1),
                    initial_visible_month=date.today(),
                    clearable=True,
                    start_date=min_date, #Initialize as 1/4
                    end_date=max_date #Initialize as today's date
                )
            ]),className='two columns',align='start'
        ),
        dbc.Col(
            html.Div([
                dcc.Dropdown(  #Ticker search box
                    id = 'ticker_input',
                    options= [{'label': i, 'value': i} for i in df['ticker'].unique()],
                    value = "NNDM", #Default value
                    placeholder="Select a ticker", #display text if no value selected
                )
            ]),className='two columns',align='start'
        ),
        dbc.Col(
            html.Div([
                html.A(html.Button(id='update_db',children='Update Database',n_clicks=0),href='/') #Update database button
            ]),className='two columns',align='start'
        ),
        
#        dbc.Col(
#            html.Div([
#
#            ],className="One of four columns")),

#         dbc.Col(
#             html.Div([ #Update button
#                 html.Button(id='ticker_button',
#                             children='Update',
#                             n_clicks=0
#                 )
#             ],className='One of four columns')),
        
    ],no_gutters=True),

    
    #Row 2
    dbc.Row([

        #ticker table --- ticker specific transactions
        dbc.Col(
            html.Div([
                dcc.Graph(id='ticker_lookup_chart'), #Ticker_lookup chart
            ],className="six columns"),
        ),
            
        dbc.Col(
            html.Div([
                html.H1(id='textbox1',
                          children = "Ticker Transactions - "
                ),
                dash_table.DataTable(
                    id='transactions_table',
                    style_cell={'textAlign': 'left',
                                'font_family': 'Arial',
                                'font_size': '18px'},
                    style_as_list_view=True,
                    fixed_rows={'headers': True}, #Allow headers to follow scrolling -- Vertical scrolling
                    style_table={'height': 550, # defaults to 500 
                                'overflowX': 'auto'},  #Horizontal scrolling
                    style_data_conditional= transaction_table_formatting #Define all the color-coding
                )
            ]),className='six columns')       
    ]),
    
    #Line break
    html.Hr(),
    
    #Row 3
    html.Div([
            html.Div([
                html.H1("Alerts for session - " + current_trading_session),
                dash_table.DataTable(
                    id='alerts_table',
                    style_cell={'textAlign': 'left',
                               'font_family': 'Arial',
                                'font_size': '18px'},
                    columns=[{"name": i, "id": i} for i in alerts.columns],
                    data=alerts.to_dict('records'),
                    style_as_list_view=True,
                    style_table={'overflowX': 'auto'},
                    style_data_conditional=alerts_table_formatting #Define all the color-coding
                )
            ],className='six columns')
    ],className='row'),
    
    #Row 4
    html.Div([
        
            #Changes table
            html.Div([
                html.H1("Changes in last trading session - " + current_trading_session),
                dash_table.DataTable(
                    id='changes_table',
                        style_data={
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'lineHeight': '15px'
                        },
                    style_cell={'textAlign': 'left',
                                'font_family': 'Arial',
                                'font_size': '18px'},
                    columns=[{"name": i, "id": i} for i in changes.columns],
                    data=changes.to_dict('records'),
                    style_as_list_view=True,
                    fixed_rows={'headers': True}, #Allow headers to follow scrolling -- Vertical scrolling
                    style_table={
                                #'height': 600, # defaults to 500 
                                'overflowX': 'auto' #Horizontal scrolling
                                },  
                    style_data_conditional=changes_table_formatting #Define all the color-coding
                )
            ],className='six columns'),
        
            #New table
            html.Div([html.H1("Recently Opened Positions"),
                dash_table.DataTable(
                    id='new_table',
                    style_cell={'textAlign': 'left',
                               'font_family': 'Arial',
                                'font_size': '18px'},
                    columns=[{"name": i, "id": i} for i in new.columns],
                    data=new.to_dict('records'),
                    style_as_list_view=True,
                    style_data_conditional = base_table_formatting
                )
            ],className='three columns'),
        
            #Closed table
            html.Div([html.H1("Recently Closed Positions"),
                dash_table.DataTable(
                    id='closed_table',
                    style_cell={'textAlign': 'left',
                               'font_family': 'Arial',
                                'font_size': '18px'},
                    columns=[{"name": i, "id": i} for i in closed.columns],
                    data=closed.to_dict('records'),
                    style_as_list_view=True,
                    style_data_conditional = base_table_formatting
                )
            ],className='three columns'),
    ],className='row')
    
]) #Close app.layout

########################################################################################
############      Define Callback functions        #####################################

#Call back for ticker chart creation
@app.callback([Output("ticker_lookup_chart","figure")],
              [Input("date1","start_date"),Input("date1","end_date"),Input("ticker_input",'value')],
              )
def update_ticker_lookup_chart(date1,date2,ticker):
    lookup = ticker_lookup_dash(ticker,date1,date2) #lookup is a pandas dataframe
    price_end_date = datetime.strptime(date2, '%Y-%m-%d') + timedelta(1) #Convert date2 into datetime obj and add 1 day --- yfinance doesn't grab "1/25" if the endate is "1/25", it grabs "1/24" as the final entry
    price = yf.Ticker(ticker).history(start=date1,end=price_end_date) #Grab ticker's closing prices
    ticker_dates = list(price['Close'].index.astype("str").str.replace("-","/").str.extract(r'/(\d{2}/\d{2})')[0]) #dates to the prices (conversion from "2021-01-04TCU00:00:00" to "01/04")
    ticker_close = np.round(price['Close'].values.astype(float),2) #closing price -- round to 2 decimals
    
    #Create figure
    fig = make_subplots(specs=[[{"secondary_y": True}]]) #Create figure
    #Create line for price
    fig.add_trace(
            go.Scatter(
                x=ticker_dates,
                y=ticker_close, 
                name="Price",
                line=dict(color="#FFC300")), #Define a color for the price line
        secondary_y=True, #Plot on secondary axis
    )
    
    for fund,dat in lookup.groupby('fund'):
        fig.add_trace(
                go.Scatter(
                    x=dat['date'], #x-val
                    y=dat['shares'], #y-val
                    mode='lines+markers', #plot as line + dots
                    name=fund
                ),
            secondary_y=False #Plot on primary axis
         ) #Name each line for legend plotting
    

    #Define y & secondary-y axis names
    
    fig.update_yaxes(title_text="Shares", secondary_y=False)
    fig.update_yaxes(title_text="Closing Price ($)", secondary_y=True)
    
    fig.update_layout(
        title={
            'text': ticker,
            'y':0.9, #percent of y-relative location
            'x':0.18, #percent of x-relative location
            'xanchor': 'center',
            'yanchor': 'top',
            'font_size': 40
        },
        #xaxis_title="X Axis Title",
        #yaxis_title="shares",
        height=600,
        #autosize=True, #Automatically determines width and height for the chart ... but it not great
#        transition = {
#            'easing':'elastic' #The transition animation when chart updates
#        },
        legend_title="Funds: ",
        showlegend=True, #Show legend even if there is only 1 line
        font=dict(
            family="Courier New, monospace",
            size=18,
            color="RebeccaPurple"
            ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="LightBlue",
            bordercolor="Black",
            borderwidth=1
        ),
        dragmode='pan', #Set default mode to pan instead of zoom
        hovermode="x unified", #to cause the label to appear for ALL lines based on the x-axis location hover (https://plotly.com/python/hover-text-and-formatting/)
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        )
    )

    return [fig] #Needs to be returned as a list

#Callback for Transaction Table
@app.callback([Output("textbox1","children"),Output('transactions_table','columns'),Output('transactions_table','data')],
              [Input("date1","start_date"),Input("date1","end_date"),Input("ticker_input",'value')]
             )
def update_textbox_transaction_log(start_date,end_date,ticker):
    if ticker is None:
        output_string = ["Select a ticker"] #Return generic statement
        columns = [] #Return no data
    else:
        output_string = ["Ticker Transaction Log - " + ticker] #Return specific ticker info
        transaction_log = compute_transactions(ticker,start_date,end_date)
        
        #Convert date column from datetime64[ns] to str & grab only YYYY-MM-DD
        transaction_log['date'] = transaction_log['date'].astype('str')
        transaction_log['date'] = transaction_log['date'].str.extract(r'(\d{4}-\d{2}-\d{2})')

        columns=[{"name": i, "id": i} for i in transaction_log.columns] #Return specific ticker data table
        data=transaction_log.to_dict('records')
    return output_string,columns,data

#Callback for reloading app
@app.callback([Output("update_db","children")], #This is just a dummy output variable ... not going to change it
              [Input("update_db","n_clicks"),Input("ticker_input","value")]
             )
def reload_app(n_clicks,ticker):
    if n_clicks > 0:
        n_clicks = 0 #Reset counter
        df_today,sectors,changes,alerts,df,current_trading_session,new,closed = start_up() #Run start_up function
        text = ['Updating...']
    else:
        text = ['Update Database']
    return text

if __name__ == '__main__':
    app.run_server(debug=True,port=8050)
