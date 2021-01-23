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

#Before loading the applet -- Run the main function
df_today,sectors,new,closed,alerts = update_arkfund(display_changes=False,manual_update='disable') #Leaving `path` argument as default

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
                end_date=max_date
            )],
        className='three columns'),
        
        html.Div([
            dcc.Input(
                id="ticker_input",
                type="text",
                value="NNDM",
                placeholder="Example ticker: 'TSLA'",
            )],
        className='one columns')
    ],className='row'),
    
    #Row 2
    html.Div([
        html.Div([
            html.H3(id='textbox1',
                children='',
        )],
        className='two columns'),
        
        html.Div([
            html.Button(id='ticker_button',
                children='Update',
                n_clicks=0
        )],
        className='two columns')
        
        
    ],className='row'),
    
    #Row 3
    html.Div([
            html.Div([
                dcc.Graph(id='ticker_lookup_chart') #Ticker_lookup chart
            ],className='six columns')
    ],className='row')
]) #Close app.layout

########################################################################################
############      Define Callback functions        #####################################

#Callback for Date selection
@app.callback([Output("textbox1","children")],
              [Input("date1","start_date"),Input("date1","end_date"),Input("ticker_input",'value')]
              )
def update_textbox(start_date,end_date,ticker):
    if start_date is None or end_date is None or ticker is None:
        output_string = ["Select a start date"]
    else:
        output_string = ["You selected " + start_date + " to " + end_date + " for ticker: " + ticker]
    return output_string #report data,column-headers

@app.callback([Output("ticker_lookup_chart","figure")],
              [Input("ticker_button",'n_clicks')],
              [State("ticker_input",'value')]
              )
def update_ticker_lookup_chart(n_clicks,ticker):
    lookup = ticker_lookup_dash(ticker) #lookup is a pandas dataframe
    fig = go.Figure()
    for fund,dat in lookup.groupby('fund'):
        fig.add_trace(go.Scatter(
                        x=dat['date'], #x-val
                        y=dat['shares'], #y-val
                        mode='lines+markers', #plot as line + dots
                        text="Shares: %d"%[i for i in dat['shares']], #Show the values next to the datapoints
                        textposition="bottom center",
                        textfont=dict(
                            family="sans serif",
                            size=16,
                            color="Crimson"
                        ),
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
        )
    )

    return [fig] #Needs to be returned as a list
    

if __name__ == '__main__':
    app.run_server(debug=True,port=8050)
