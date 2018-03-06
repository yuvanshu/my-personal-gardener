#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
# import sqlite3
import "github.com/mattn/go-sqlite3"

from flask import Flask
from flask import request
from flask import make_response
from flask import render_template


# Flask app should start in global layout

app = Flask(__name__)

@app.route('/hello')
def hello():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    #print('Request:')
    #print(json.dumps(req, indent=4))
    res = processRequest(req)
    res = json.dumps(res, indent=4)
    print(res)

    # Extract current fcast
    # curr_fcast = res['query']['results']['channel']['item']['forecast']
    # curr_fcast_text = curr_fcast['text']
    
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def processRequest(req):
    if req.get('result').get('action') == 'water-recommendation':
        result = req.get('result')
        parameters = result.get('parameters')
        #print(json.dumps(parameters, indent=4))
        baseurl = 'https://query.yahooapis.com/v1/public/yql?'
        yql_query = makeYqlQuery(req)
        if yql_query is None:
            return {}
        yql_url = baseurl + urlencode({'q': yql_query}) + '&format=json'
        result = urlopen(yql_url).read()
        data = json.loads(result)
        #print(data)
        res = makeWebhookResult(data, parameters)
    return res


def makeYqlQuery(req):
    result = req.get('result')
    parameters = result.get('parameters')
    city = parameters.get('geo-city')
    if city is None:
        return None
    #print(city)
    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" \
        + city + "')"


def makeWebhookResult(data, parameters):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    #print(json.dumps(parameters, indent=4))
    if result is None:
        return {'speech': 'No Result', 'displayText': 'No Result',
                'source': 'apiai-weather-webhook-sample'}
    channel = result.get('channel')
    if channel is None:
        return {'speech': 'No Channel', 'displayText': 'No Channel',
                'source': 'apiai-weather-webhook-sample'}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if location is None or item is None or units is None:
        return {'speech': 'No location or item or units',
                'displayText': 'No location or item or units',
                'source': 'apiai-weather-webhook-sample'}

    condition = item.get('condition')
    if condition is not None:
        plant = parameters.get('plant-type')
        moist = parameters.get('number')
        city = parameters.get('geo-city')
        temp = float(condition.get('temp'))
        #fcast = parameters.get('Forcast')
        fcast = condition.get('text')
        decision = ' need '
		
sqlite_file = 'plant_db'    # name of the sqlite database file
table_name = 'plantdatabase'   # name of the table to be queried
id_column = 'row_id'
some_id = 1
column_1 = 'plant_name'
column_2 = 'moisture_low'
column_3 = 'moisture_high' 
column_4 = 'temp_threshold'   

# Connecting to the database file
conn = sqlite3.connect(sqlite_file)
c = conn.cursor()

c.execute("""SELECT plant_name, moisture_low, moisture_high, temp_threshold FROM plantdatabase WHERE plant_name = ?;""", (plant,)) 

for row in c.fetchall():
    plant_name     = row[0]
    moisture_low   = row[1]
    moisture_high  = row[2]
    temp_threshold = row[3]

# Closing the connection to the database file
conn.close()

if plant = plant_name: 
   if fcast in ["Rain", "Rainy"] :
      decision = ' does not need '
    elif moist > moisture_high :
      decision = ' does not need '
    elif moist < moisture_low :
      decision = ' needs '
    elif moist >= moisture_low and moist <= moisture_high and temp >= temp_threshold and fcast in ["Sunny", "Cloudy", "Partly Cloudy", "Mostly Cloudy", "Partly Sunny", "Mostly Sunny"] :
      decision = ' needs '
    elif moist >= moisture_low and moist <= moisture_high and fcast in ["Sunny", "Mostly Sunny", "Partly Sunny"] :
      decision = ' needs '
    elif moist >= moisture_low and moist <= moisture_high and temp < temp_threshold and fcast in ["Cloudy", "Partly Cloudy", "Mostly Cloudy"] :
      decision = ' does not need '      
    result = {}
    result['speech'] = "Yuvanshu. The temperature is {0} degrees Fahrenheit and the weather forecast is {1} in  {2} and the soil moisture is {3} percent. Based on your data, your  {4}  {5} water  ".format( temp, fcast, city,  moist,  plant, decision )
    result['displayText'] = result['speech']
    result['source'] = 'apiai-weather-webhook-sample'
    return result

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print('Starting app on port %d' % port)

    app.run(debug=False, port=port, host='0.0.0.0')
