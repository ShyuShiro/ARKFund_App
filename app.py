import dash
import plotly
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
from datetime import date, timedelta, datetime
import plotly.express as px
import plotly.graph_objects as go

#To be able to import the ARK.py file and its modules, the directory needs to be added to PATH
import os
import sys
module_path = os.path.abspath(r'C:\Users\Brandon\Desktop\ARK Fund CSV Files')
if module_path not in sys.path:
    sys.path.append(module_path)

#Now import ARK.py functions
from ARK import *
set_dir()

#Before loading the applet -- Run the main function
df_today,sectors,changes,_,_,alerts = update_arkfund(display_changes=False,manual_update='disable') #Leaving `path` argument as default

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
    
#Load in dash app with external CSS elements
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#Define some theme settings
colors = {
    'background': '#111111',
    'text': '#7FDBFF',
    'button':'#D6D8DC'
    }

min_date = date(2021,1,4) #Hard code ... this is the earliest date of data in ARKFund.db 
max_str = datetime.strptime(df['date'].iloc[-1], '%m/%d/%Y')
max_date = date(max_str.year,max_str.month,max_str.day)

app.layout = html.Div(children=[
    #Row 1
    html.Div([
        #Date selector 1
        html.Div([
            dcc.DatePickerRange(
                id='date1',
                min_date_allowed=min_date,
                max_date_allowed=max_date+timedelta(1),
                initial_visible_month=date.today(),
                clearable=True,
                start_date=min_date, #Initialize as 1/4
                end_date=max_date #Initialize as today's date
            )],
        className='three columns'),
        
        html.Div([ #Ticker search box
            dcc.Dropdown(
                id = 'ticker_input',
                options= [{'label': i, 'value': i} for i in df['ticker'].unique()],
                value = "NNDM", #Default value
                placeholder="Select a ticker", #display text if no value selected
            )],className='two columns'),
        
        html.Div([ #Update button
            html.Button(id='ticker_button',
                children='Update',
                n_clicks=0
            )
        ],className='two columns')
    ],className='row'),
    
    #Row 2
    html.Div([
            #ticker table --- ticker specific transactions
                html.Div([
                    dcc.Graph(id='ticker_lookup_chart'), #Ticker_lookup chart
                ],className='six columns'),
                
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
                        style_table={'height': 600, # defaults to 500 
                                    'overflowX': 'auto'},  #Horizontal scrolling
                    )],className='six columns')        
    ],className='row'),
    
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
                    style_cell={'textAlign': 'left',
                                'font_family': 'Arial',
                                'font_size': '18px'},
                    columns=[{"name": i, "id": i} for i in changes.columns],
                    data=changes.to_dict('records'),
                    style_as_list_view=True,
                    fixed_rows={'headers': True}, #Allow headers to follow scrolling -- Vertical scrolling
                    style_table={'height': 600, # defaults to 500 
                                'overflowX': 'auto'},  #Horizontal scrolling
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
                )
            ],className='three columns')
    ],className='row')
    
]) #Close app.layout

########################################################################################
############      Define Callback functions        #####################################

#Call back for ticker chart creation
@app.callback([Output("ticker_lookup_chart","figure")],
              [Input("ticker_button",'n_clicks'),Input("date1","start_date"),Input("date1","end_date")],
              [State("ticker_input",'value')]
              )
def update_ticker_lookup_chart(n_clicks,date1,date2,ticker):
    lookup = ticker_lookup_dash(ticker,date1,date2) #lookup is a pandas dataframe
    fig = go.Figure()
    for fund,dat in lookup.groupby('fund'):
        fig.add_trace(go.Scatter(
                        x=dat['date'], #x-val
                        y=dat['shares'], #y-val
                        mode='lines+markers', #plot as line + dots
                        name=fund)) #Name each line for legend plotting
    #fig.update_traces(textposition='top center')
    fig.update_layout(
        title={
            'text': ticker,
            #'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        #xaxis_title="X Axis Title",
        yaxis_title="shares",
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
              [Input("ticker_button",'n_clicks'),Input("date1","start_date"),Input("date1","end_date")],
              [State("ticker_input",'value')])
def update_textbox_transaction_log(n_clicks,start_date,end_date,ticker):
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

if __name__ == '__main__':
    app.run_server(debug=True,port=8050)
