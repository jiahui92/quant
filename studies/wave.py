import numpy
import pandas
from vnpy_ctastrategy.backtesting import load_bar_data
from datetime import datetime
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
import utils.index as utils


def getDataFrame(history_data):
    bar_data_dict_list = []
    for index, bardata in enumerate(history_data):
        bar_dict = {
            "index": index,
            "datetime": bardata.datetime,
            "open_price": bardata.open_price,
            "close_price": bardata.close_price,
            "low_price": bardata.low_price,
            "high_price": bardata.high_price,
            "turnover": bardata.turnover, # 成交额
            "volume": bardata.volume, # 成交额
        }
        bar_data_dict_list.append(bar_dict)
    df = pandas.DataFrame(bar_data_dict_list)
    # df['date'] = df['datetime']
    return df



# 优化
## 最大值取high_price, 最小值取low_price
## 排除未平稳走势图形(或者近期走势大涨或平稳)
## 取不到北交所的数据

## 回测
### 入参：波浪周期、波浪高度、回测时间段
### 买入时机：profit, withdrawal
### 卖出时机:1个星期内不是突破走势
### 排除下跌中继图形？
### 排除已跌破位图形？
### 排除已经提前到达-50反弹过了
### 排除最高点离现在比较近的图形？



def find_wave(row):
    history_data: List[BarData] = load_bar_data(
        symbol=row['symbol'],
        exchange=Exchange[row['exchange']],
        start=datetime(2023, 2, 1),
        end=datetime(2023, 6, 30),
        # start=datetime(2022, 11, 1),
        # end=datetime(2023, 3, 30),
        interval=Interval.DAILY,
    )

    waveWidth = 60
    waveShift = 30
    if len(history_data) < (waveWidth+waveShift):
        return

    waveStart = -(waveWidth + waveShift)
    df = getDataFrame(history_data)
    preMinIndex = df['low_price'][waveStart:waveStart+30].idxmin()
    preMin = df['low_price'][preMinIndex]
    midMaxIndex = df['high_price'][waveStart+20:waveStart+40].idxmax()
    midMax = df['high_price'][midMaxIndex]
    lastMinIndex = df['low_price'][waveStart+50:waveStart+59].idxmin()
    lastMin = df['low_price'][lastMinIndex]
    nowPriceIndex = len(history_data)-1-waveShift
    nowPrice = df['close_price'].iloc[nowPriceIndex]

    # 判断波浪
    isWave = (
        (midMax - preMin) / preMin > 0.2 and
        (midMax - lastMin) / lastMin > 0.2 and
        preMinIndex < midMaxIndex < lastMinIndex
    )

    # 判断近期是否平稳（使用方差？）
    # 预期利润
    profit = (midMax - nowPrice) / nowPrice * 100
    withdrawaled = (midMax - nowPrice) / midMax * 100
    # isGoodProfit = profit > 20

    # 预期回撤
    # preWithdrawal = (lastMin-preMin)/preMin*100
    # lastWithdrawal = (nowPrice-lastMin)/lastMin*100
    # isGoodWithdrawal = -10 < preWithdrawal < 10 and -5 < lastWithdrawal < 5
    minWithdrawal = min([nowPrice, preMin, lastMin])
    withdrawal = (nowPrice - minWithdrawal) / minWithdrawal * 100
    isGoodWithdrawal = -10 < withdrawal < 10

    # if (symbol == '300093'): print(preWithdrawal, preMin, lastMin)

    if isWave and isGoodWithdrawal and withdrawaled > 40:
        title = f"预期回撤:{int(withdrawal)} 最大已回撤:{int(withdrawaled)} 利润:{int(profit)}  {row['symbol']} {row['name']} {row['industry']}"
        floatMarketValue = (row['float_share']*df.iloc[-1]['close_price'])
        axtitle = f"流通市值:{int(floatMarketValue)}亿 PE:{row['pe']} 利润同比:{int(row['profit_yoy'])}% 股东人数:{int(row['holder_num']/10000)}万"
        savePath = "./studies/png2/"+row['industry']+row['symbol']+".png"
        print(title)

        dotArr = [
            {
                'annotate': 'preMin',
                'color': 'green',
                'dotSeries': utils.makeSingleDotSeries(df['low_price'], preMinIndex),
            },
            {
                'annotate': 'midMax',
                'color': 'red',
                'dotSeries': utils.makeSingleDotSeries(df['high_price'], midMaxIndex),
            },
            {
                'annotate': 'lastMin',
                'color': 'blue',
                'dotSeries': utils.makeSingleDotSeries(df['low_price'], lastMinIndex),
            },
            {
                'annotate': 'nowPrice',
                'color': 'grey',
                'dotSeries': utils.makeSingleDotSeries(df['close_price'], nowPriceIndex),
            },
        ]
        plt = utils.getStockPlot(df, dotArr, title, axtitle, savePath)
        plt.close()

        # plt.show()
