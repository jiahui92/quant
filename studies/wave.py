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


def find_wave(row: dict, nowDate: datetime, waveWidth = 60, waveShift = 0):
    start = nowDate - timedelta(((waveWidth+waveShift)+40)*1.5)
    history_data: List[BarData] = load_bar_data(
        symbol=row['symbol'],
        exchange=Exchange[row['exchange']],
        start=start,
        end=nowDate,
        interval=Interval.DAILY,
    )

    if len(history_data) < (waveWidth+waveShift):
        return None, False, False, 0, 0, 0, 0, []

    waveStart = -(waveWidth + waveShift)
    df = getDataFrame(history_data)

    # 波浪的前段区域为： 0 ~ 1/2
    preMinIndex = df['low_price'][waveStart:waveStart+int(waveWidth/2)].idxmin()
    preMin = df['low_price'][preMinIndex]
    # 波浪的中间区域为： 1/3 ~ 2/3
    midMaxIndex = df['high_price'][waveStart+int(waveWidth/3):waveStart+int(waveWidth*2/3)].idxmax()
    midMax = df['high_price'][midMaxIndex]
    # 波浪的后段区域为： 1/2 ~ 1
    lastMinIndex = df['low_price'][waveStart+int(waveWidth*5/6):waveStart+waveWidth-1].idxmin()
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
    willWithdrawal = (nowPrice - minWithdrawal) / minWithdrawal * 100

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

    isStable = False
    # 股价是否已经平稳了，目前股价在近5天的均价 正负-1%~5%内
    if len(df['close_price']) > 5:
        isStable = df['close_price'].iloc[-1] / df['close_price'][-5:].mean() > 1.02

    # 波浪的周期
    waveLen = lastMinIndex - preMinIndex
    return [df, isWave, isStable, waveLen, willWithdrawal, withdrawaled, profit, dotArr]


def plot_wave(row):
    # nowDate = datetime(2023, 12, 8)
    nowDate = datetime.now()
    df, isWave, isStable, waveLen, willWithdrawal, withdrawaled, profit, dotArr = find_wave(row, nowDate, 300, 0)
    isGoodWithdrawal = -10 < willWithdrawal < 10

    # if (symbol == '300093'): print(preWithdrawal, preMin, lastMin)
    isNotST = row['name'].find("ST") == -1
    if isNotST and isStable and isWave and isGoodWithdrawal and withdrawaled > 45 and 60 < waveLen:
        title = f"预期回撤:{int(willWithdrawal)} 最大已回撤:{int(withdrawaled)} 利润:{int(profit)}  {row['symbol']} {row['name']} {row['industry']}"
        floatMarketValue = (row['float_share']*df.iloc[-1]['close_price'])
        axtitle = f"流通市值:{int(floatMarketValue)}亿 PE:{row['pe']} 利润同比:{int(row['profit_yoy'])}% 股东人数:{int(row['holder_num']/10000)}万"

        print(title)

        isGoodPeg = 0 < row['pe'] / row['profit_yoy'] <= 1
        pegPath = ''
        if isGoodPeg:
            pegPath = 'PEG-'
        savePath = "./studies/png2/" + pegPath + row['industry'] + row['symbol'] + ".png"

        plt = utils.getStockPlot(df, dotArr, title, axtitle, savePath)
        plt.close()

        # plt.show()
