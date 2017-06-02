# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import time
from datetime import datetime, timedelta

import tushare as ts
from django.http import HttpResponse
from dwebsocket import accept_websocket

from stock.data import stock_charts_util
from stock.data.stock_data import StockData


# Create your views here.
def get_index(request):
    index = StockData().get_index()
    min_date, max_date = StockData().get_date_range()
    return HttpResponse(json.dumps({'min': str(min_date), 'max': str(max_date),
                                    'index': {int(code): row.to_dict() for code, row in index.iterrows()}}))


def market(request):
    start = time.time()
    result = {
        'volumes': [],
        'surged_limit': [],
        'surged_over_five_per': [],
        'decline_limit': [],
        'decline_over_five_per': [],
    }
    date = datetime.strptime(request.GET['date'], '%Y-%m-%d').date()
    index = StockData().get_index()
    info = StockData().get_info(date=date, date_start=date - timedelta(days=14))
    print time.time() - start

    dates = info['date'].drop_duplicates()
    for row in dates:
        result['volumes'].append((str(row), int(info[info['date'] == row]['volume'].sum())))
    print time.time() - start

    info_today = info[info['date'] == date]
    info_yesterday = info[info['date'] == date - timedelta(days=1)]

    info_today['name'] = index['name']
    info_today['adjclose_last'] = info_yesterday['adjclose']
    info_today['raising'] = (info_today.adjclose - info_today.adjclose_last) / info_today.adjclose_last

    for code, stk in info_today.iterrows():
        line = {'code': int(code), 'name': stk['name'], 'close': stk['close'], 'rate': stk['raising']}
        if stk['raising'] >= 0.1:
            result['surged_limit'].append(line)
        elif stk['raising'] > 0.05:
            result['surged_over_five_per'].append(line)
        elif stk['raising'] <= -0.1:
            result['decline_limit'].append(line)
        elif stk['raising'] < -0.05:
            result['decline_over_five_per'].append(line)

    result['total'] = len(info_today)
    result['surged'] = len(info_today[info_today.raising > 0])
    result['balanced'] = len(info_today[info_today.raising == 0])
    result['declined'] = len(info_today[info_today.raising < 0])

    print time.time() - start
    return HttpResponse(json.dumps(result))


def stock_list(request):
    date = datetime.strptime(request.GET['date'], '%Y-%m-%d').date()
    info = StockData().get_info(date=date, date_start=date - timedelta(days=1))
    info_today = info[info['date'] == date]
    info_yesterday = info[info['date'] == date - timedelta(days=1)]
    index = StockData().get_index()

    info_today['name'] = index['name']
    info_today['close_last'] = info_yesterday['close']
    info_today['adjclose_last'] = info_yesterday['adjclose']
    info_today['raising'] = (info_today.adjclose - info_today.adjclose_last) / info_today.adjclose_last

    result = []
    for code, row in info_today.dropna().iterrows():
        result.append((int(code), row['name'], row['open'], row['high'], row['low'], row['close'], row['close_last'],
                       row['raising'], row['volume']))

    return HttpResponse(json.dumps(result))


def stock(request):
    result = {'dates': [], 'data': [], 'volume': []}
    code = int(request.GET['code'])
    infos = StockData().get_info(code=code, limit=500)
    index = StockData().get_index()
    result['name'] = index['name'][code]
    for code, row in infos.iloc[::-1].dropna().iterrows():
        result['dates'].append(str(row['date']))
        result['data'].append((row['open'], row['close'], row['low'], row['high']))
        result['volume'].append(row['volume'])
    return HttpResponse(json.dumps(result))


@accept_websocket
def realtime_list(request):
    if request.is_websocket():
        while not request.websocket.closed:
            if request.websocket.has_messages():
                msg = request.websocket.read()
                if msg is None:
                    break
            result = []
            start = time.time()
            df = ts.get_today_all()
            for _, row in df.iloc[::-1].iterrows():
                if row['volume'] > 0:
                    result.append((row['code'], row['name'], row['open'], row['high'], row['low'], row['trade'],
                                   row['settlement'], row['changepercent'] / 100, row['volume'], row['turnoverratio'] / 100))
            request.websocket.send(json.dumps(result))
            time.sleep(10)
    else:
        return HttpResponse('This path accepts WebSocket connections.')


@accept_websocket
def realtime_price(request):
    if request.is_websocket():
        while not request.websocket.closed:
            if request.websocket.has_messages():
                msg = request.websocket.read()
                if msg is None:
                    break
            result = {'ticks': [], 'prices': [], 'volumes': []}
            try:
                df = ts.get_today_ticks('%06d' % int(request.GET['code']))
                print ''
                today = datetime.now().strftime('%Y-%m-%d')
                current_minute = ''
                for _, row in df.iloc[::-1].iterrows():
                    minute = row['time'][:5]
                    if minute != current_minute:
                        current_minute = minute
                        result['ticks'].append(today + ' ' + minute)
                        result['prices'].append(row['price'])
                        result['volumes'].append(row['volume'])
            except:
                pass
            result['quotes'] = ts.get_realtime_quotes('%06d' % int(request.GET['code'])).iloc[0].to_dict()
            request.websocket.send(json.dumps(result))
            time.sleep(10)
    else:
        return HttpResponse('This path accepts WebSocket connections.')
