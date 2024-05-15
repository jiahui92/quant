import os
import re
import statistics

import numpy
import pandas
from vnpy_ctastrategy.backtesting import load_bar_data
from datetime import datetime, timedelta
from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    Interval,
    Status,
)
from typing import Callable, List, Dict, Optional, Type
from vnpy.trader.object import OrderData, TradeData, BarData, TickData
import pandas_ta as ta
import pandas as pd
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import utils.index as utils


def maBollStart():
    zx_df = pd.read_excel('./assets/zixuan.xlsx', dtype={'ts_code': str})
    df = pandas.DataFrame(columns=zx_df.columns)
    df_stock = utils.getStockDataFrame(True)

    for index, row in zx_df.iterrows():
        if pd.isna(row['ts_code']): continue
        symbol = row['ts_code'].split('.')[0]
        exchange = utils.get_exchange(row['ts_code'])
        df_stock_filter = df_stock[df_stock["ts_code"] == row["ts_code"]]

        nowPrice, ma5Percent, ma10Percent, ma20Percent, ma60Percent, bollHighPercent, bollLowPercent = maBoll(
            row['name'], symbol, exchange)
        row['nowPrice'] = nowPrice

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


        row['ma5 %'] = ma5Percent
        row['ma10 %'] = ma10Percent
        row['ma20 %'] = ma20Percent
        row['ma60 %'] = ma60Percent
        row['boll'] = pd.NaT
        row['High %'] = bollHighPercent
        row['Low %'] = bollLowPercent

        df = pandas.concat([df, row.to_frame().T], axis=0, ignore_index=True)

    style_df = df.style.apply(add_df_style, axis=1, subset=[
        'ts_code', 'name', 'div.dyn %', 'peg', 'ma5 %', 'ma10 %', 'ma20 %', 'ma60 %', 'High %', 'Low %'
    ])

    # current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    style_df.to_excel(f"./assets/temp_zixuan.xlsx", engine='openpyxl', index=False)


def add_df_style(row: pandas.Series):
    # darkgreen = 'background-color: mediumseagreen;'
    # darkred = 'background-color: salmon;'
    lightgreen = 'background-color: lightgreen;'
    lightred = 'background-color: lightpink;'
    lightyellow = 'background-color: lightyellow;'

    result = []
    for key, value in row.items():
        # 字符串不需要染色，只处理数值
        if isinstance(value, str) or pandas.isna(value):
            result.append('')
        elif re.search('High', key):
            if value < 3: result.append(lightred)
            elif value > 10: result.append(lightgreen)
            else: result.append('')
        elif re.search('Low', key) and value > -3:
            result.append(lightgreen)
        elif re.search('div', key):
            if value >= 5:
                result.append(lightgreen)
            else: result.append('')
        elif re.search('peg', key):
            if 0 <= value <= 0.8:
                result.append(lightgreen)
            else: result.append('')
        else:
            if -3 < value < 0 or value > 8:
                result.append(lightgreen)
            elif 0 < value < 5:
                result.append(lightred)
            elif value == 0:
                result.append(lightyellow)
            else:
                result.append('')

    # name处重点标注颜色
    if result.count(lightgreen) >= 5: result[1] = lightgreen
    if result.count(lightred) >= 4: result[1] = lightred

    # 上涨 或 下跌趋势
    if isinstance(row['ma5 %'], (int, float)):
        if 0 >= row['ma5 %'] >= row['ma10 %'] >= row['ma20 %']:
            result[0] = lightgreen
        elif 0 <= row['ma5 %'] <= row['ma10 %'] <= row['ma20 %']:
            result[0] = lightred
        elif statistics.stdev([row['ma5 %'], row['ma10 %'], row['ma20 %']]) <= 0.5:
            result[0] = lightyellow

    return result


def maBoll(name, symbol, exchange):
    emptyResult = pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT, pd.NaT
    if exchange == None: return emptyResult

    nowDate = datetime.now()
    if nowDate.hour < 15:
        nowDate -= timedelta(days=1)
    start = nowDate - timedelta(100)
    history_data: List[BarData] = load_bar_data(
        symbol=symbol,
        exchange=Exchange[exchange],
        start=start,
        end=nowDate,
        interval=Interval.DAILY,
    )
    df = utils.getDataFrame(history_data)

    lastIndex = len(history_data) - 1
    if lastIndex == -1:
        print(name + ": 数据错误")
        return emptyResult
    nowPrice = df['close_price'].iloc[lastIndex]
    ma5 = utils.get_ma_price(df['close_price'], 5)
    ma10 = utils.get_ma_price(df['close_price'], 10)
    ma20 = utils.get_ma_price(df['close_price'], 20)
    ma60 = utils.get_ma_price(df['close_price'], 60)
    ma5weekly = utils.get_ma_price(df['close_price'], 5 * 5)
    ma10weekly = utils.get_ma_price(df['close_price'], 10 * 5)
    ma20weekly = utils.get_ma_price(df['close_price'], 20 * 5)
    std = df['close_price'][lastIndex - 20:lastIndex].std()
    bollHigh = ma20 + 2 * std
    bollLow = ma20 - 2 * std

    # 近期高价（弧形）?
    # 量？
    # 月线维度

    ma5Percent = utils.get_percent(nowPrice, ma5)
    ma10Percent = utils.get_percent(nowPrice, ma10)
    ma20Percent = utils.get_percent(nowPrice, ma20)
    ma60Percent = utils.get_percent(nowPrice, ma60)
    bollHighPercent = utils.get_percent(nowPrice, bollHigh)
    bollLowPercent = utils.get_percent(nowPrice, bollLow)

    # print(row["name"], ma5Percent, ma10Percent, ma20Percent, bollHighPercent, bollLowPercent)
    # table.add_row([
    #     row["name"], nowPrice,
    #     ma5Percent, ma10Percent, ma20Percent, ma30Percent, ma60Percent,
    #     bollHighPercent, bollLowPercent
    # ])
    return nowPrice, ma5Percent, ma10Percent, ma20Percent, ma60Percent, bollHighPercent, bollLowPercent

    # 输出结果
    #   标记某个股票的长时间段的结果

    # 已买：顶点提示，支撑点提示！！！

    #
    # # if (symbol == '300093'): print(preWithdrawal, preMin, lastMin)
    # isNotST = row['name'].find("ST") == -1
    # if isNotST and isStable and isWave and isGoodWithdrawal and withdrawaled > 45 and 60 < waveLen:
    #     title = f"预期回撤:{int(willWithdrawal)} 最大已回撤:{int(withdrawaled)} 利润:{int(profit)}  {row['symbol']} {row['name']} {row['industry']}"
    #     floatMarketValue = (row['float_share']*df.iloc[-1]['close_price'])
    #     axtitle = f"流通市值:{int(floatMarketValue)}亿 PE:{row['pe']} 利润同比:{int(row['profit_yoy'])}% 股东人数:{int(row['holder_num']/10000)}万"
    #
    #     print(title)
    #
    #     isGoodPeg = 0 < row['pe'] / row['profit_yoy'] <= 1
    #     pegPath = ''
    #     if isGoodPeg:
    #         pegPath = 'PEG-'
    #     savePath = "./studies/png2/" + pegPath + row['industry'] + row['symbol'] + ".png"
    #
    #     plt = utils.getStockPlot(df, dotArr, title, axtitle, savePath)
    #     plt.close()

    # plt.show()

if __name__ == "__main__":
    utils.calculate_function_runtime(maBollStart)