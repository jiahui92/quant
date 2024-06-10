import math
import re
import statistics
import time

import pandas
from datetime import datetime, timedelta

import pandas as pd

import utils.index as utils
import talib
import tushare as ts

def kdj_realtime_start():
    # calc_kdj_buying_point()
    while True:
        calc_kdj_buying_point()
        time.sleep(5*60)

def calc_kdj_buying_point():
    stock_df = utils.getStockDataFrame()
    stock_df = stock_df[['ts_code', 'name', 'industry', 'total_share', 'profit_yoy']]

    df = pandas.DataFrame(columns=stock_df.columns)
    df_stock = utils.getStockDataFrame(True)

    request_count = 1

    for index, row in stock_df.iterrows():
        # if index > 100: continue
        # if index < 6225: continue

        if pd.isna(row['ts_code']): continue
        symbol = row['ts_code'].split('.')[0]
        exchange = utils.get_exchange(row['ts_code'])
        df_stock_filter = df_stock[df_stock["ts_code"] == row["ts_code"]]

        if exchange == None: continue

        bar_datas = utils.get_bar_data(row['ts_code'], 100)
        if len(bar_datas) == 0: continue
        nowPrice = bar_datas[-1].close_price

        print(f"{index}/{len(stock_df)}")
        # 过滤掉小于100亿的股票
        if pandas.isna(nowPrice) or nowPrice * row['total_share'] < 100 or row['profit_yoy'] < -20:
            continue

        data_dicts = [{
            'high': bar_data.high_price,
            'low': bar_data.low_price,
            'close': bar_data.close_price,
        } for bar_data in bar_datas]
        data_old = pd.DataFrame(data_dicts)

        kdj_old = utils.calculate_kdj(data_old)
        rsi_old = talib.RSI(data_old['close'], timeperiod=6)
        if kdj_old['J'].iloc[-1] > 20 or rsi_old.iloc[-1] > 30:
        # if kdj_old['J'].iloc[-1] > 30:
            continue

        print(f"请求数据:{row['ts_code']} {row['name']} count:{request_count}")
        request_count += 1

        tick_df = ts.realtime_quote(ts_code=row['ts_code'])
        if len(tick_df) < 1: continue
        tick = tick_df[tick_df['TS_CODE'] == row['ts_code']].iloc[0]

        # 把实时数据当成今天的数据
        data_dicts.append({
            'high': tick['HIGH'],
            'low': tick['LOW'],
            'close': tick['PRICE'],
        })

        data = pd.DataFrame(data_dicts)

        kdj = utils.calculate_kdj(data)
        rsi = talib.RSI(data['close'], timeperiod=6)

        if kdj['J'].iloc[-1] > 30:
            continue
        # 筛选今天到达买卖点的股票
        if not (kdj['K'].iloc[-1] > kdj['D'].iloc[-1] and kdj['K'].iloc[-2] < kdj['D'].iloc[-2]):
            continue

        row['K'] = round(kdj['K'].iloc[-1], 1)
        row['D'] = round(kdj['D'].iloc[-1], 1)
        row['J'] = round(kdj['J'].iloc[-1], 1)
        row['RSI'] = round(rsi.iloc[-1], 1)

        macd, macd_signal, macd_hist = talib.MACD(data['close'])

        stock_row = None
        if len(df_stock_filter) > 0:
            stock_row = df_stock_filter.iloc[0]

        if stock_row is not None:
            # 计算股息率
            dividend_pct, end_date = utils.get_dividend_pct(row["ts_code"], nowPrice)
            row['div %'] = dividend_pct * 100

            profit_yoy = stock_row['profit_yoy'] / 100
            row['div.dyn %'] = round((1 + profit_yoy) * dividend_pct * 100, 2)  # 动态股息率

            # 计算peg
            peg = utils.safe_division(stock_row['pe'], stock_row['profit_yoy'])
            row['peg'] = round(peg, 1)
            row['profit %'] = stock_row['profit_yoy']
        else:
            row['div %'] = ''
            row['div.dyn %'] = ''
            row['peg'] = ''
            row['profit %'] = ''




        # row['ma5 %'] = ma5Percent
        # row['ma10 %'] = ma10Percent
        # row['ma20 %'] = ma20Percent
        # row['ma60 %'] = ma60Percent
        # row['boll'] = pd.NaT
        # row['High %'] = bollHighPercent
        # row['Low %'] = bollLowPercent


        arr = row['ts_code'].split('.')
        if len(arr) == 2:
            row['link'] = f"https://quote.eastmoney.com/{arr[1]}{arr[0]}.html"

        df = pandas.concat([df, row.to_frame().T], axis=0, ignore_index=True)

    # 把desc挪到最后一列
    columns_to_move = ['desc', 'link']
    new_columns = [col for col in df.columns if col not in columns_to_move] + columns_to_move
    df = df.reindex(columns=new_columns)

    df = df.sort_values(by="J")

    print(df)
    df.to_excel('./assets/temp_kdj_realtime.xlsx', engine='openpyxl', index=False)


if __name__ == "__main__":
    kdj_realtime_start()