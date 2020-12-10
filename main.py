import pandas as pd
import regex as re
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import yfinance
from layout import *



# Dash Set up
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Basic Layout
app.layout = html.Div([
	html.H1("Stock Price Dashboard - Created by Jingtian Xu", style = {
		"textAlign": 'center', "fontSize": '30px', "margin-bottom": "30px"
	}),
	dcc.Tab(label='Stock Price Dashboard - Created by Jingtian Xu', value='price-tab',children=[
		html.Div([html.H2(id='stock-name',
				        style={'width':'30%','display':'inline-block'}),
				    html.H4(id='ticker',
				        style={'width':'10%','display':'inline-block'})],
				    style={'width':'90%','margin':'auto'}),
			# Position 0, Title
		html.Div(get_info_box(),
				    style={'width':'90%','margin':'auto'}),
			# Position 1, Info and dropdown
		html.Div(get_stats_graph_layout('tab'),
				    style={'width':'90%','margin':'auto'})
			# Position 2, Table of stats and graph
		])# Tab 1, End price-tab

		])




# Identify the ticker and its market
def verify_ticker(ticker, mkt):
	# For Hong Kong Stocks
	if mkt == 'hk':
		tick = re.findall('^\d{1,5}$', ticker)
		if len(tick)>0:
			tick = str(tick[0])[::-1]
			while(len(tick)<4):
				tick += '0'
			tick = tick[::-1]
			tick += '.HK'
			return True, tick
		# If entered ticker invalid
		else:
			return False, None
	# For US stocks
	elif mkt == 'us':
		tick = re.findall('^[A-Za-z]{1,4}$', ticker)
		if len(tick)>0:
			return True, tick[0].upper()
		# If entered ticker invalid
		else:
			return False, None
	return False, None

# Obtain 50- ,100- and 200-day moving average
def getMA(stock, time, date_list):
	if 'mo' in time or time=='ytd' or time=='1y':
		df = stock.history(period='2y')
	elif time=='2y' or time=='3y' or time=='4y':
		df = stock.history(period='5y')
	else:
		df = stock.history(period='10y')
	df = df.reset_index()[['Date','Open','Low','High','Close']]
	df['MA50'] = df.Close.rolling(50).mean()
	df['MA100'] = df.Close.rolling(100).mean()
	df['MA200'] = df.Close.rolling(200).mean()

	df = df.loc[(df['Date']>=date_list.min()) & (df['Date']<=date_list.max())]
	return df

# Generate stock price and graph
@app.callback([Output('stock-name','children'),
	           Output('ticker','children'),
	           Output('stock-price','children'),
	           Output('stock-price-change','children'),
	           Output('stock-price-change','style'),
	           Output('stock-price-percentchange','children'),
	           Output('stock-price-percentchange','style'),
	           Output('error-message','children'),
	           Output('vis','figure'),
	           Output('table','children')],
	          [Input('submit','n_clicks'),
	           Input('time-interval','value')],
	          [State('ticker-input','value'),
	           State('market-dropdown', 'value')])
def get_ticker(n_clicks, time, ticker, mkt):
	# For default setting
	if ticker == '':
		return 'Please Enter a Stock Ticker', \
		       '','','',{'width':'20%', 'display':'inline-block'},'', \
		       {'width':'20%', 'display':'inline-block'},'', \
		       {'data':None}, None
	# Verify ticker format in respective to stock market
	stockFormat, ticker = verify_ticker(ticker, mkt)
	# Catch incorrect
	if stockFormat is False:
		return 'Wrong Ticker', '#######', '$##.##', '##.##', \
		       {'width':'20%', 'display':'inline-block'}, '##.##%', \
		       {'width':'20%', 'display':'inline-block'}, \
		       'Error! Please try again.', {'data':None}, None
	# Obtain stock price and stats
	stock = yfinance.Ticker(ticker)
	# Catch if stock exists
	if stock.history(period='ytd').shape[0] == 0:
		return 'Wrong Ticker', '#######', '$##.##', '##.##', \
		       {'width':'20%', 'display':'inline-block'}, '##.##%', \
		       {'width':'20%', 'display':'inline-block'}, \
		       'Error! Please try again.', {'data':None}, None
	### Stock Stats for Info Box ###
	try:
		# Name and price
		stock_name = stock.info['longName']
		price_list = stock.history(period=time)['Close'].tolist()
		price = f'${price_list[-1]:.2f}'
		# Price Change
		price_change = price_list[-1] - price_list[-2]
		price_percent_change = (price_list[-1]/price_list[-2])-1
		if price_change > 0:
			price_change_colour = {'color':'green'}
		else:
			price_change_colour = {'color':'red'}
		price_change_colour['display']= 'inline-block'
		price_change_colour['width']= '20%'
		price_change_colour['font-size'] = '150%'
		price_change = f'{price_change:.2f}'
		price_percent_change = f'{price_percent_change*100:,.2f}%'

		df = getMA(stock, time,
			       stock.history(period=time).reset_index()['Date'])

		fig = getCandlestick(df)
		table = getTable(stock.history(period=time).reset_index(),
			                 stock.info)

	except:
		return 'Sorry! Company Not Available', '#######', '$##.##', '##.##', \
		       {'width':'20%', 'display':'inline-block'}, '##.##%', \
		       {'width':'20%', 'display':'inline-block'}, \
		       'Error! Please try again another Company.', {'data':None}, None


	return stock_name, ticker, price, price_change, price_change_colour, \
	       price_percent_change, price_change_colour, '', fig, table


if __name__ == '__main__':
    app.run_server(debug=True)
