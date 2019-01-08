# coding=utf-8
from datetime import datetime
from io import StringIO

import pandas
import requests
import tushare


def df_map(df, mapping):
    new_df = pandas.DataFrame()
    for key in mapping:
        new_df[key] = df[mapping[key]]
    return new_df


def history_netease(code, date_start, date_end):
    if code < 600000:
        code += 1000000
    r = requests.get('http://quotes.money.163.com/service/chddata.html?code=' + ('%07d' % code)
                     + '&start=' + date_start.strftime('%Y%m%d') + '&end=' + date_end.strftime('%Y%m%d')
                     + '&fields=TCLOSE;HIGH;LOW;TOPEN;VOTURNOVER')
    df = pandas.read_csv(StringIO(r.text))
    df['股票代码'] = pandas.to_numeric(df['股票代码'].str.slice(1))
    return df_map(df, {'code': '股票代码', 'date': '日期', 'open': '开盘价', 'high': '最高价',
                       'low': '最低价', 'close': '收盘价', 'volume': '成交量'})


def fund_history(code, date_start, date_end):
    r = requests.get('http://stock.finance.sina.com.cn/fundInfo/api/openapi.php/CaihuiFundInfoService.getNav?symbol=' + ('%06d' % code)
                     + '&datefrom=' + date_start.strftime('%Y-%m-%d') + '&dateto=' + date_end.strftime('%Y-%m-%d')
                     + '&num=100000')
    df = pandas.io.json.json_normalize(r.json()['result']['data']['data'])
    df['code'] = code
    df['fbrq'] = df['fbrq'].str.slice(0, 10)
    return df_map(df, {'code': 'code', 'date': 'fbrq', 'open': 'jjjz', 'high': 'jjjz',
                       'low': 'jjjz', 'close': 'jjjz', 'volume': 'ljjz'})


def history(code, date_start, date_end):
    return fund_history(code, date_start, date_end)
    # return history_netease(code, date_start, date_end)


def today_list_netease():
    r = requests.get(
        'http://quotes.money.163.com/hs/service/diyrank.php?query=STYPE%3AEQA%3BEXCHANGE%3ACNSESZ&count=10000&'
        'fields=SYMBOL,SNAME,PRICE,PERCENT,OPEN,YESTCLOSE,HIGH,LOW,VOLUME,HS&sort=SYMBOL&order=asc',
        timeout=10)
    df = pandas.io.json.json_normalize(r.json()['list'])
    df['SYMBOL'] = pandas.to_numeric(df['SYMBOL'])
    return df_map(df, {'code': 'SYMBOL', 'name': 'SNAME', 'rate': 'PERCENT', 'price': 'PRICE',
                       'open': 'OPEN', 'high': 'HIGH', 'low': 'LOW', 'yest_close': 'YESTCLOSE',
                       'volume': 'VOLUME', 'turn_over': 'HS'})


def today_list_tushare():
    df = tushare.get_today_all()
    df['changepercent'] /= 100
    df['turnoverratio'] /= 100
    return df_map(df, {'code': 'code', 'name': 'name', 'rate': 'changepercent', 'price': 'trade',
                       'open': 'open', 'high': 'high', 'low': 'low', 'yest_close': 'settlement',
                       'volume': 'volume', 'turn_over': 'turnoverratio'})


def fund_today_list():
    r = requests.get(
        'http://quotes.money.163.com/fn/service/netvalue.php?query=STYPE:FDO&fields='
        'PUBLISHDATE,SYMBOL,SNAME,NAV,PCHG,M12RETRUN,SLNAVG,LJFH,ZJZC&sort=SYMBOL&order=asc&count=10000',
        timeout=10)
    df = pandas.io.json.json_normalize(r.json()['list']).dropna()
    return df_map(df, {'code': 'SYMBOL', 'name': 'SNAME', 'rate': 'PCHG', 'price': 'NAV',
                       'open': 'NAV', 'high': 'NAV', 'low': 'NAV', 'yest_close': 'NAV',
                       'volume': 'ZJZC', 'turn_over': 'LJFH'})


def today_list():
    return fund_today_list()
    # return today_list_netease()
    # return today_list_tushare()


def today_ticks_netease(code):
    if code < 600000:
        code += 1000000
    r = requests.get(
        'http://img1.money.126.net/data/hs/time/today/' + ('%07d' % code) + '.json',
        timeout=10)
    df = pandas.DataFrame(r.json()['data'])
    df[0] = df[0].str.slice(start=0, stop=2) + ':' + df[0].str.slice(start=2, stop=4)
    return df_map(df, {'tick': 0, 'price': 1, 'volume': 3})


def today_ticks_tushare(code):
    df = tushare.get_today_ticks('%06d' % code)
    df['time'] = df['time'].str.slice(start=0, stop=5)
    df = df.drop_duplicates('time').iloc[::-1].reset_index()
    return df_map(df, {'tick': 'time', 'price': 'price', 'volume': 'amount'})


def today_ticks(code):
    return today_ticks_netease(code)
    # return today_ticks_tushare(code)


def today_quotes(code):
    df = tushare.get_realtime_quotes('%06d' % code)
    return df.iloc[0]


def stock_news(code):
    return tushare.get_notices('%06d' % code)


if __name__ == '__main__':
    print(history(1, datetime(2018, 12, 1), datetime(2018, 12, 10)))
