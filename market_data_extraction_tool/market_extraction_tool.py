#!/usr/bin/env python
# coding: utf-8
# To install: requests, numpy, pandas, pandas_datareader, matplotlib, yahoo_fin

import os
import json
import requests
import requests_html
import time
import arrow

from multiprocessing import Process
from datetime import datetime
from yahoo_fin import options

import numpy as np
import pandas as pd
import pandas_datareader.data as web
import matplotlib.pyplot as plt
import matplotlib as mpl

#Register Pandas Formatters and Converters with matplotlib
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

def change_working_directory():
	"""
	Asks the user whether or not they want to change the working directory, i.e. where
	the market data (intraday, daily, options) that the following program requests and
	saves.
	No argument.
	"""
	while True:
		value = input("Do you wish to change the working directory to your desktop? (Y/N): ")
		if (value == "Y" or value == "N"):
			break
	if value == "Y":
		current_directory = os.getcwd()
		temporary_directory = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + "//Market Data Extract"
		if(os.path.isdir(temporary_directory) == False):
			os.makedirs(temporary_directory)
			print("The path " + temporary_directory + " was created.")
		new_directory = os.chdir(temporary_directory)
		print("You swapped from the working directory " + str(current_directory) + " to " + str(os.getcwd()))
	else:
		print("Your current directory remains " + str(os.getcwd()) + ".")

def import_web_intraday(ticker):
	"""
	Queries the stock market data provider AlphaVantage's website. AV provides stocks, 
	forex, and cryptocurrencies. AV limits access for free users: 
	- maximum of : 5 unique queries per minute; 500 unique queries per 24h period
    - Intraday history is capped at the past five days (current + 4)
    - After-hour data is not available
	The provided data is formatted as a JSON file. It follows a minute frequency from 
	open (09:30am) to closing (04:00pm). Each minute ticks is a list as follow:
    open, close, low, high, average, and volume.
	:param <ticker>: String ; acronym of a company traded on a financial market
    """
	website = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol='+ticker+'&interval=1min&apikey=’+YOUR_API_KEY+’&outputsize=full&datatype=json'
	raw_json_intraday_data = requests.get(website)
	return raw_json_intraday_data.json()

def import_web_daily(ticker):
	"""
	Queries the stock market data provider IEX's API. IEX provides stocks, forex, 
	and cryptocurrencies data. IEX limits access for free users:
	- maximum of: 5 years of daily data (/!\ standard in finance is usually 10)
	The provided data is formatted as a panda dataframe.
	:param <ticker>: String ; acronym of a company traded on a financial market
	"""
	end = datetime.today()
	start = end.replace(year=end.year-5)
	daily_data = web.DataReader(ticker, 'iex', start, end)
	return daily_data

def partition_save_intraday(ticker,json_extract):
	"""
	Saves a JSON array containing a company's intraday data in a folder named after 
	the company's acronym. It does:
	1. Creates an empty dictionary. Stores in it each day value covered in the JSON
	array, formatted as "yyyy-mm-dd". 
	2. Splits the JSON array into separate JSON dictionaries (one per unique day 
	covered in the inition JSON array. Each created dictionary is saved as a single
	JSON file the folder mentioned above. If a file shares the same name, both are 
	merged:
		2.1 Checks for a directory named <ticker>\intraday_data exists
		2.2 Checks for a file named <ticker>_<date> in the directory. If so: merges 
		the created dictionary with the data stored in the existing file
		2.3 Saves the data (merged when applicable) in the folder under the name 
		<ticker>_<date>
	:param <ticker>: String ; acronym of a company traded on a financial market
	:param <json_extract>: JSON Array ; Array of intraday data of company <ticker>
	"""
	# Step 1
	date = {}
	for item in json_extract:
		date[item[:10]] = "date"
	# Step 2
	for day in date.keys():
		daily_time_series = {}
		# Step 2.1
		for item in json_extract:
			if(item[:10] == day):
				daily_time_series[item] = json_extract[item]
		# Step 2.2
		path = ticker + "\\intraday_data"
		if(os.path.isdir(path) == False):
			os.makedirs(path)
		data_file_name = ticker + "_" + day
		# Step 2.3
		try:
			with open(os.path.join(path,data_file_name),'r') as file:
				existing_data_in_file = json.load(file)
				for item in existing_data_in_file:
					daily_time_series[item] = existing_data_in_file[item]
		except Exception as e:
			print(f"{ticker}:")
			print(e)
		with open(os.path.join(path,data_file_name), 'w') as f:
			json.dump(daily_time_series, f)

def partition_save_daily(ticker, data_extract):
	"""
	Saves the retrieved dataframe in a folder named after the company's acronym.
	It does:
	1. Checks for folder named <ticker> and creates it if non-existent. Checks 
	for a file named <ticker> in the folder. If so: merges the retrieved and existing
	data.
	2. Saves the data (merged when applicable) in the folder under the name <ticker>
	:param <ticker>: String ; acronym of a company traded on a financial market
	:param <data_extract>: Dataframe ; Dataframe of daily data of company <ticker>
	"""
	# Step 1
	if(os.path.isdir(ticker) == False):
		os.mkdir(ticker)
	data_file_name = ticker
	data_extract_dictionary = data_extract.to_dict(orient="index")
	try:
		with open(os.path.join(ticker,data_file_name),'r') as file:
			existing_data_in_file = json.load(file)
			for item in existing_data_in_file:
				data_extract_dictionary[item] = existing_data_in_file[item]
	except Exception as e:
		print(f"{ticker}:")
		print(e)
	# Step 2
	with open(os.path.join(ticker,data_file_name), 'w') as f:
		json.dump(data_extract_dictionary, f)

def save_intraday(ticker):
	"""
	Saves AV's available intraday data for the company <ticker>.
	:param <ticker>: String ; acronym of a company traded on a financial market
	"""
	raw_json = import_web_intraday(ticker)
	time_series_json = raw_json['Time Series (1min)']
	partition_save_intraday(ticker,time_series_json)

def save_daily(ticker):
	"""
	Saves IEX's available intraday data for the company <ticker>.
	:param <ticker>: String ; acronym of a company traded on a financial market
	"""
	raw_dataframe = import_web_daily(ticker)
	partition_save_daily(ticker,raw_dataframe)

def extract_save_option_data(ticker):
	"""
	Imports from the yahoo finance database online the option data of a company and
	saves it. The option data is split per type (call or put), expiration date, and
	day of import as they are highly volatile. It does:
	1. Checks for nested directories:
		<ticker>\options_data_<ticker>\<expiration_date>_<ticker>_<options>
	Creates it if non-existent. 
	2. Checks in the folder for a file named:
		<expiration_date>_<ticker>_<calls/puts>_as-at_<date_extract> 
	If so: merges the existing and newly extracted data.
    3. Saves the data (merged when applicable) in the folder under the company's 
	acronym.
	:param <ticker>: String ; acronym of a company traded on a financial market
	"""
	extract_dates = options.get_expiration_dates(ticker)
	today = datetime.today().strftime("%Y-%m-%d")
	for expiration_date in extract_dates:
		extract = options.get_options_chain(ticker)
		format_date = arrow.get(expiration_date, 'MMMM D, YYYY').format('YYYY-MM-DD')
		path = ticker + "\\options_data_" + ticker + "\\" + format_date + "_" + ticker + "_options"
		option_types = ["calls", "puts"]
		for option in option_types:
			extract_chain = extract[option]
			extract_chain = extract_chain.to_dict(orient="index")
			data_file_name = format_date + "_" + ticker + "_" + option + "_as-at_" + today
			# Step 1
			if not os.path.exists(path):
				os.makedirs(path)
			# Step 2
			if os.path.isfile(os.path.join(path,data_file_name)) == True:
				try:
					with open(os.path.join(path,data_file_name),'r') as file:
						existing_data_in_file = json.load(file)
						for item in existing_data_in_file:
							extract_chain[item] = existing_data_in_file[item]
				except Exception as e:
					print(f"{ticker}:")
					print(e)
			#Step 3
			with open(os.path.join(path,data_file_name), 'w') as f:
				json.dump(extract_chain, f)
				print(f"{ticker}: {format_date} {option} options data retrieved successfully!\n")

def extract_info_intraday(company_list):
	"""
	Calls the extract and save functions above for each company listed in a the list
	<company_list> (see below).
	:param <company_list>: List ; list of publicly traded companies' acronyms
	"""
	try:
		for company in company_list:
			save_intraday(company)
			print(f"{company}: intraday market data retrieved successfully!\n")
			if ((company_list.index(company)+1) % 5 == 0 and company_list.index(company)+1 != len(company_list)):
				print("ALPHAVANTAGE REQUEST LIMIT REACHED - WAITING FOR 1 MINUTE\n")
				time.sleep(60)
				print("1 MINUTE PASSED - RETURN TO REQUESTING ALPHAVANTAGE\n")
	except Exception as e:
		print(f"{company}:")
		print(e)

def extract_info_daily_and_options(company_list):
	"""
	Calls the extract and save functions above for each company listed in a the list
	<company_list> (see below).
	:param <company_list>: List ; list of publicly traded companies' acronyms
	"""
	try:
		for company in company_list:
			save_daily(company)
			print(f"{company} daily market data retrieved successfully!\n")
			extract_save_option_data(company)
	except Exception as e:
		print(f"{company}:")
		print(e)

def extract_info_all(company_list):
	"""
	Calls the extract and save functions above for each company listed in a the list
	<company_list> (see below).
	:param <company_list>: List ; list of publicly traded companies' acronyms
	"""
	try:
		for company in company_list:
			save_intraday(company)
			print(f"{company} intraday market data retrieved successfully!\n")
			save_daily(company)
			print(f"{company} daily market data retrieved successfully!\n")
			extract_save_option_data(company)
			if ((company_list.index(company)+1) % 5 == 0 and company_list.index(company)+1 != len(company_list)):
				print("ALPHAVANTAGE REQUEST LIMIT REACHED - WAITING FOR 1 MINUTE\n")
				time.sleep(60)
				print("1 MINUTE PASSED - RETURN TO REQUESTING ALPHAVANTAGE\n")
	except Exception as e:
		print(f"{company}:")
		print(e)

def short_term_analysis(ticker):
	"""
	Extracts intraday data of a single company from AV's website or from an existing
	local file. It does:
	1. Checks if data for the company exists locally. If so: retrieves it. If not:
	requests it from AV's website. The data is extracted as a JSON array and formatted
	as a DataFrame.
	2. Formats the dataframe to fit the following format:
			DATE (index)| MARKET DATA
			date 1		| open | low | high | etc.
			date 2		| open | low | high | etc.
			etc. 		| etc.
		2.1 Modifies the type of each instance of the MARKET DATA from a string to 
		a float.
		2.2 Creates an empty set of each single day covered in the data formatted as
		"yyyy-mm-dd".
		2.3 Modifies the type of each instance of the DATE (index) from a string or 
		integer to a datetime.
		2.4 Formats the data into a "plottable" array. FYI, The minute data provided by
		AV runs from 09:31:00am to 04:00:00pm. The opening bell tick (09:30:00am) is 
		missing. AV's data is actually delayed by a minute, i.e. the opening value of a 
		stock at 09:30:00am corresponds to the “1. open” value  linked to the index 
		"09:31:00am". The actual daily data per minute of a stock can be approximated 
		as such: “1. open” 09:31:00am datum + “4. close” 09:31:00am to 04:00:00pm data.
	3. Plots the data
	:param <ticker>: String ; acronym of a company traded on a financial market
	"""   
	# Step 1
	path = ticker + "\\intraday_data"
	covered_date_filenames = os.listdir(path)[-5:]
	market_data = {}
	try:
		for filename in covered_date_filenames:
			with open(os.path.join(ticker,"intraday_data",filename),'r') as file:
				load_dict = json.load(file)
			market_data = {**market_data, **load_dict}
		market_data_minute_time_series = pd.DataFrame(market_data).transpose()
		print("Data loaded from existing local file.")
	except Exception as e:
		print(f"{ticker}:")
		print(e)
		market_data = import_web_intraday(ticker)
		market_data_minute_time_series = pd.DataFrame(market_data["Time Series (1min)"]).transpose()
		market_data_minute_time_series = market_data_minute_time_series.reindex(index=market_data_minute_time_series.index[::-1])
		print("Data loaded from data repository online.")    
	# Step 2
	# Step 2.1
	for column in market_data_minute_time_series.keys():
		market_data_minute_time_series[column] = market_data_minute_time_series[column].astype('float64')     
	# Step 2.2 
	dates_in_time_series = sorted(set([x[:10] for x in market_data_minute_time_series.index.tolist()]))
	# Step 2.3
	market_data_minute_time_series.index = pd.to_datetime(market_data_minute_time_series.index, format = '%Y-%m-%d %H:%M:%S')
	# Step 2.4
	i = 0
	for index in market_data_minute_time_series.index:
		if str(index)[-8:] == "09:31:00" and str(market_data_minute_time_series.iloc[i-1])[-8:] != "09:30:00":
			market_data_minute_time_series.loc[pd.Timestamp(str(index)[:11]+"09:30:00")] = [0,0,0,market_data_minute_time_series.iloc[i][0],0]
		i += 1
	market_data_minute_time_series = market_data_minute_time_series.sort_index()
	# Step 3
	plt.style.use('ggplot')
	fig, ax = plt.subplots(1, len(dates_in_time_series), figsize=(16,7))
	plt.suptitle(ticker, size = 20, y=0.93)
	i = 0
	for group_name, df_group in market_data_minute_time_series.groupby(pd.Grouper(freq='D')):
		if df_group.empty == False:
			ax[i].plot(df_group['4. close'], color = "blue")
			xfmt = mpl.dates.DateFormatter('%m-%d %H:%M')
			ax[i].xaxis.set_major_locator(mpl.dates.MinuteLocator(byminute=[30], interval = 1))
			ax[i].xaxis.set_major_formatter(xfmt)
			ax[i].get_xaxis().set_tick_params(which='major', pad=4)
			ax[i].set_ylim(min(market_data_minute_time_series['4. close'])-
				round(0.005*min(market_data_minute_time_series['4. close']),0),
				max(market_data_minute_time_series['4. close'])+
				round(0.005*max(market_data_minute_time_series['4. close']),0))
		fig.autofmt_xdate()
		i += 1
	plt.show()

# Oil & Gas: XOM, CVX, COP, EOG, OXY
# Tech: AAPL, GOOGL, GOOG, FB, MSFT
# Banking: JPM, BAC, C,WFC, GS
# Recent IPO: LYFT, PINS
firms = ['XOM','CVX','COP','EOG','OXY','AAPL','GOOGL','GOOG','FB','MSFT','JPM','BAC','C','WFC','GS','LYFT','PINS']

if __name__=='__main__':
	change_working_directory()
	#concurrent running
	try:
		process_1 = Process(target = extract_info_intraday, args=(firms,))
		process_1.start()
		process_2 = Process(target = extract_info_daily_and_options, args=(firms,))
		process_2.start()
	except Exception as e:
		print(e)
	#sequential running
	#extract_info_intraday(firms)
	#extract_info_daily_and_options(firms)
	#extract_info_all(firms)

#single_company_to_analyze = "GS"
#short_term_analysis(single_company_to_analyze)




