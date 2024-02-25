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
from utils.index import getStockDataFrame

table = PrettyTable()
table.field_names = ["name", "nowPrice", "ma5", "ma10", "ma20", "ma30", "ma60", "bollHigh", "bollLow"]

def maBoolStart():
    # 设计数据结果
    #   默认上证指数、收藏指数等
    stockArr = [
        {"symbol": '000001', "exchange": "SSE", "name": "上证指数", "tags": ['main']},
        {"symbol": '300394', "exchange": "SZSE", "name": "天孚通信", "tags": ['持仓']},
        {"symbol": '603259', "exchange": "SSE", "name": "药明康德", "tags": ['持仓']},
        {"symbol": '688981', "exchange": "SSE", "name": "中芯国际", "tags": ['持仓']},
        {"symbol": '872808', "exchange": "BSE", "name": "曙光数创", "tags": ['持仓']},
        # 纳指
        # 纳指科技
        # 纳指生物
    ]

    for item in stockArr:
        maBoll(item)

    print(table)

def maBoll(row):
    # nowDate = datetime(2023, 12, 8)
    # nowDate = datetime.now()

    # isInclude = utils.list_include(stockArr, "code", row["ts_code"])
    # if not isInclude: return

    nowDate = datetime.now()
    start = nowDate - timedelta(100)
    history_data: List[BarData] = load_bar_data(
        symbol=row['symbol'],
        exchange=Exchange[row['exchange']],
        start=start,
        end=nowDate,
        interval=Interval.DAILY,
    )
    df = utils.getDataFrame(history_data)

    lastIndex = len(history_data) - 1
    if lastIndex == -1:
        print(row['name'] + ": 数据错误")
        return
    nowPrice = df['close_price'].iloc[lastIndex]
    ma5 = utils.get_ma_price(df['close_price'], 5)
    ma10 = utils.get_ma_price(df['close_price'], 10)
    ma20 = utils.get_ma_price(df['close_price'], 20)
    ma30 = utils.get_ma_price(df['close_price'], 30)
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
    ma30Percent = utils.get_percent(nowPrice, ma30)
    ma60Percent = utils.get_percent(nowPrice, ma60)
    bollHighPercent = utils.get_percent(nowPrice, bollHigh)
    bollLowPercent = utils.get_percent(nowPrice, bollLow)

    # print(row["name"], ma5Percent, ma10Percent, ma20Percent, bollHighPercent, bollLowPercent)
    table.add_row([
        row["name"], nowPrice,
        ma5Percent, ma10Percent, ma20Percent, ma30Percent, ma60Percent,
        bollHighPercent, bollLowPercent
    ])

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
