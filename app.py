from datetime import date, timedelta
import time as t
import yfinance as yf
import pandas as pandas
import plotly
import csv
import plotly.graph_objects as go
import requests
from flask import Flask, render_template, request
from Ohlc import Ohlc, to_timestamp
from datetime import datetime

app = Flask(__name__)

@app.route("/news")
def news_display():
    if request.method == 'POST':
        print(request)
        print(request.content)

    elif request.method == 'GET':
        print(request)
        print(request.content)

    return render_template('news.html')


@app.route("/accepted")
def accepted():
    url1 = 'https://siddhi4.bpmcep.ics.unisg.ch/engine-rest/task/'
    response = requests.post(url1,json={})

    print(response)
    responseJson = response.json()

    taskId = responseJson[0]['id']  # get ID of the task
    url = f'https://siddhi4.bpmcep.ics.unisg.ch/engine-rest/task/{taskId}/complete'
    new_request = {
        "variables": {"approved": {"value": True},
                      "item": {"value": "stocks"},
                      "quantity": {"value": 2},
                      "repeats": {"value": 0}
                      }
    }
    complete_url = url

    # Call method "complete" with prepared url
    complete = requests.post(complete_url, json=new_request)
    print('complete status code: ', complete.status_code)






    return render_template('accepted.html')

@app.route('/', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        interest = request.form['interest']
        quantity = int(request.form['quantity'])

        # Create a new resource
        # REPLACE WITH YOUR SERVER HERE
        response = requests.post(
            'https://siddhi4.bpmcep.ics.unisg.ch/engine-rest/process-definition/key/investement-reccomandation/start',
            json={
                "variables": {
                    "amount": {
                        "value": quantity,
                        "type": "long"
                    },
                    "interest": {
                        "value": interest,
                        "type": "string"
                    }
                }
            })

        print(response.content)
        if response.status_code == 200:
            jsonResponse = response.json()
            instanceID = jsonResponse.get("id")
        else:
            instanceID = "null"

        if interest == 'crypto':
            END_DATE = date.today().strftime("%d/%m/%Y")
            START_DATE1 = (date.today() - timedelta(days=7)).strftime("%d/%m/%Y")
            START_DATE2 = (date.today() - timedelta(days=90)).strftime("%d/%m/%Y")
            PERIOD = 86400  # Time period in seconds (e.g., 1 day = 86400)
            start_ts1 = to_timestamp(START_DATE1)
            start_ts2 = to_timestamp(START_DATE2)
            end_ts = to_timestamp(END_DATE)
            params1 = {
                'after': start_ts1,
                'before': end_ts,
                'periods': PERIOD,
            }
            params2 = {
                'after': start_ts2,
                'before': end_ts,
                'periods': PERIOD,
            }

            exchange_resp = requests.get(f'https://api.cryptowat.ch/markets/gemini?apikey=KX7N0V7H7YVBFB0W5EO3')
            pairs_unfiltered = [i['pair'] for i in exchange_resp.json()['result'] if i['active']]
            pairs = []
            for pair in pairs_unfiltered:
                if 'usd' in pair:
                    pairs.append(pair)

            ohlc_resp1 = []
            for pair in pairs:
                ohlc_resp1.append(requests.get(
                    f'https://api.cryptowat.ch/markets/gemini/{pair}/ohlc?apikey=KX7N0V7H7YVBFB0W5EO3',
                    params=params2))
            ohlcs = []
            for coin in ohlc_resp1:
                ohlcs.append([Ohlc(i) for i in coin.json()['result'][f'{PERIOD}']])

            columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'qt_volume']
            dataframes = []
            best_performing_coin_7_days = [-100, -199, -98, -97, -96]
            for coin in ohlc_resp1:
                data = [tuple([datetime.fromtimestamp(i[0])] + i[1:]) for i in coin.json()['result'][f'{PERIOD}']]
                dataframes.append(pandas.DataFrame.from_records(data, columns=columns))

            dict_coins = {
                0: "",
                1: "",
                2: "",
                3: "",
                4: ""
            }
            for i in range(len(dataframes)-1):
                if dataframes[i].empty:
                    del dataframes[i]
                    del pairs[i]
            for i in range(len(dataframes)):
                openprice = dataframes[i]['open'].iloc[0]
                closeprice = dataframes[i]['close'].iloc[-1]
                x = 0
                for j in dataframes[i]['open']:
                    if 0.99 < j < 1.01:
                        x+=1

                performance = closeprice / openprice
                if (performance > min(best_performing_coin_7_days)) and (x<40):
                    dict_coins[best_performing_coin_7_days.index(min(best_performing_coin_7_days))] = i
                    best_performing_coin_7_days[
                        best_performing_coin_7_days.index(min(best_performing_coin_7_days))] = performance

            figures_not_offline = []
            figures = []
            for key in dict_coins:
                figures_not_offline.append(go.Figure(data=[go.Candlestick(x=dataframes[dict_coins[key]]['date'],open=dataframes[dict_coins[key]]["open"],high=dataframes[dict_coins[key]]["high"],low=dataframes[dict_coins[key]]["low"],close=dataframes[dict_coins[key]]["close"])]))
            print(figures_not_offline)
            for i in range(5):
                figures_not_offline[i].update_layout(
                    title=pairs[dict_coins[i]],
                    yaxis_title=pairs[dict_coins[i]] + " Price (USD)"
            )
            for figure in figures_not_offline:
                figures.append(plotly.offline.plot(figure,auto_open=False,output_type="div"))
            url = 'https://siddhi4.bpmcep.ics.unisg.ch/engine-rest/external-task/'
            fetchAndLockPayload = {"workerId": "myExampleWorker",  # ID of the resource to which the task is assigned
                                   "maxTasks": 1,  # get only one running instance of the process
                                   "usePriority": False,  # don't sort instance by priority
                                   "topics":
                                       [{"topicName": "got_crypto_info",
                                         # name of task's topic (identifies the nature of the work to be performed)
                                         "lockDuration": 30000  # duration of the lock
                                         }]
                                   }
            y = True
            while y:
                fetchAndLock_url = url + 'fetchAndLock'
                # Call API FetchAndLock with prepared url
                response = requests.post(fetchAndLock_url, json=fetchAndLockPayload)

                #print('Fetch and lock status code: ', response.status_code)
                #print('Fetch and lock response: ', response.text)

                responseJson = response.json()  # JSON of the response

                if len(responseJson) != 0:

                    # Get the first item of the response
                    task = responseJson[0]

                    taskId = task['id']  # get ID of the task
                    value = task['variables']['amount']['value']  # get value of variable amount

                    # Put you Business Logic here...
                    # Example: Print the value of the receipt if the amount is greater than 24
                    print_rec_value = (int(value) > 24)

                    # Prepare the new request...
                    # Example: add to the request the values that you want to send back to Camunda server, e.g., print_rec = true
                    new_request = {
                        "workerId": "myExampleWorker",
                        "variables": {"print_rec": {"value": print_rec_value}}
                    }
                    complete_url = (url + str(taskId) + '/complete')

                    # Call method "complete" with prepared url
                    complete = requests.post(complete_url, json=new_request)
                    #print('complete status code: ', complete.status_code)
                    y= False

                    # Complete the task and update the process variables
                    # Method: POST /task/{id}/complete

                else:
                    t.sleep(0.2)

            return render_template('response.html', interest=interest, quantity=quantity, code=response.status_code, message=response.content, figures=figures)

        elif interest == 'stocks':
            marketcaps = pandas.read_csv("static/market_cap.csv")
            big_stocks = marketcaps[marketcaps.marketcap>100000000000]
            all_tickers = []
            all_name = []
            for entry in big_stocks['Symbol']:
                all_tickers.append(entry)
            for entry in big_stocks['Name']:
                all_name.append(entry)


            dict_stocks = {
                0: "",
                1: "",
                2: "",
                3: "",
                4: ""
            }


            data_stocks = yf.Tickers(all_tickers)
            historical_data_stocks = []
            columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'qt_volume']
            for ticker in all_tickers:
                df = data_stocks.tickers[f'{ticker}'].history(period="3mo")
                df.columns = [ 'open', 'high', 'low', 'close','volume', 'dividends', 'stock_splits']
                historical_data_stocks.append(df)
            best_performing_stocks = [-100, -199, -98, -97, -96]

            for i in range(len(historical_data_stocks)):
                openprice = historical_data_stocks[i]['open'].iloc[0]
                closeprice = historical_data_stocks[i]['close'].iloc[-1]

                performance = closeprice / openprice
                if performance > min(best_performing_stocks):
                    dict_stocks[best_performing_stocks.index(min(best_performing_stocks))] = i
                    best_performing_stocks[
                        best_performing_stocks.index(min(best_performing_stocks))] = performance

            figures_not_offline = []
            figures = []
            for key in dict_stocks:
                figures_not_offline.append(go.Figure(data=[
                    go.Candlestick(x=historical_data_stocks[dict_stocks[key]].index, open=historical_data_stocks[dict_stocks[key]]["open"],
                                   high=historical_data_stocks[dict_stocks[key]]["high"], low=historical_data_stocks[dict_stocks[key]]["low"],
                                   close=historical_data_stocks[dict_stocks[key]]["close"])]))
            for i in range(5):
                figures_not_offline[i].update_layout(
                    title=all_name[dict_stocks[i]],
                    yaxis_title=all_tickers[dict_stocks[i]] + " Price (USD)"
                )
            for figure in figures_not_offline:
                figures.append(plotly.offline.plot(figure, auto_open=False, output_type="div"))
            url = 'https://siddhi4.bpmcep.ics.unisg.ch/engine-rest/external-task/'
            fetchAndLockPayload = {"workerId": "myExampleWorker",  # ID of the resource to which the task is assigned
                                   "maxTasks": 1,  # get only one running instance of the process
                                   "usePriority": False,  # don't sort instance by priority
                                   "topics":
                                       [{"topicName": "got_stocks_info",
                                         # name of task's topic (identifies the nature of the work to be performed)
                                         "lockDuration": 30000  # duration of the lock
                                         }]
                                   }
            y = True
            while y:
                fetchAndLock_url = url + 'fetchAndLock'
                # Call API FetchAndLock with prepared url
                response = requests.post(fetchAndLock_url, json=fetchAndLockPayload)

                # print('Fetch and lock status code: ', response.status_code)
                # print('Fetch and lock response: ', response.text)

                responseJson = response.json()  # JSON of the response

                if len(responseJson) != 0:

                    # Get the first item of the response
                    task = responseJson[0]

                    taskId = task['id']  # get ID of the task
                    value = task['variables']['amount']['value']  # get value of variable amount

                    # Put you Business Logic here...
                    # Example: Print the value of the receipt if the amount is greater than 24
                    print_rec_value = (int(value) > 24)

                    # Prepare the new request...
                    # Example: add to the request the values that you want to send back to Camunda server, e.g., print_rec = true
                    new_request = {
                        "workerId": "myExampleWorker",
                        "variables": {"print_rec": {"value": print_rec_value}}
                    }
                    complete_url = (url + str(taskId) + '/complete')

                    # Call method "complete" with prepared url
                    complete = requests.post(complete_url, json=new_request)
                    # print('complete status code: ', complete.status_code)
                    y = False

                    # Complete the task and update the process variables
                    # Method: POST /task/{id}/complete

                else:
                    t.sleep(0.2)

            return render_template('response.html', interest=interest, quantity=quantity, figures=figures)

    return render_template('order.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
