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
        start=datetime(2023, 6, 1),
        end=datetime(2023, 10, 31),
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

    if isWave and isGoodWithdrawal and withdrawaled > 30:
        title = f"预期回撤:{int(withdrawal)} 最大已回撤:{int(withdrawaled)} 利润:{int(profit)}  {row['symbol']} {row['name']} {row['industry']}"
        savePath = "./studies/png2/"+row['industry']+row['symbol']+".png"
        print(title)

        # timeStr =df['datetime'][preMinIndex].strftime('%Y-%m-%d %H:%M:%S')
        # series = pandas.Series([timeStr, df['low_price'][preMinIndex]])
        # data = {
        #     datetime
        # }
        newDf = df.loc[preMinIndex:preMinIndex]
        res = df['low_price'][preMinIndex:preMinIndex+1]
        ok_res = df['low_price']
        # print(res, type(res))
        # print(ok_res, type(ok_res))

        # df['preMin'] = numpy.NaN
        # df['preMin'][preMinIndex] = df['low_price'][preMinIndex]


        dotArr = [
            {
                'annotate': 'preMin',
                'color': 'green',
                'dotSeries': utils.makeSingleDotSeries(df['low_price'], preMinIndex),
                # 'dotSeries': df['preMin'],
                # 'dot': res,
                # 'dot': pandas.Series(newDf.iloc[0]),
                # 'dot': pandas.Series(newDf.iloc[0]),
                # 'dot': df['low_price'],
                # 'dot': df.loc[preMinIndex:preMinIndex]['low_price'],
            },
            # {
            #     'annotate': 'midMax',
            #     'color': 'red',
            #     'dot': [df['datetime'][midMaxIndex], df['high_price'][midMaxIndex]],
            # },
            # {
            #     'annotate': 'lastMin',
            #     'color': 'blue',
            #     'dot': [df['datetime'][lastMinIndex], df['low_price'][lastMinIndex]],
            # },
            # {
            #     'annotate': 'nowPrice',
            #     'color': 'grey',
            #     'dot': [df['datetime'][nowPriceIndex], df['close_price'][nowPriceIndex]],
            # },
        ]
        plt = utils.getStockPlot(df, title, savePath, dotArr)
        plt.close()

        # plt.show()



# 波浪策略
def wave():
    history_data: List[BarData] = load_bar_data(
        symbol="300308",
        exchange=Exchange.SZSE,
        start=datetime(2023, 1, 1),
        end=datetime(2023, 12, 30),
        # start=datetime(2022, 11, 1),
        # end=datetime(2023, 3, 30),
        interval=Interval.DAILY,
    )

    bar_data_dict_list = []
    for index, bardata in enumerate(history_data):
        bar_dict = {
            "index": index,
            "datetime": bardata.datetime,
            "close_price": bardata.close_price,
        }
        bar_data_dict_list.append(bar_dict)

    df = pandas.DataFrame(bar_data_dict_list)

    df['maLast'] = ta.sma(df['close_price'], length=5, offset=-5)
    df['maMiddle'] = ta.sma(df['close_price'], length=5, offset=0)
    df['maPrev'] = ta.sma(df['close_price'], length=5, offset=5)

    max_price_serias = []
    for index in range(len(df['close_price'])):
        max_price = df['close_price'][index-10:index].max()
        max_price_serias.append(max_price)
    df['max_price'] = pandas.Series(max_price_serias)

    min_price_serias = []
    for index in range(len(df['close_price'])):
        min_price = df['close_price'][index-10:index].min()
        min_price_serias.append(min_price)
    df['min_price'] = pandas.Series(min_price_serias)


    # 取最近10天最大值
    # arc_top_pattern = (df['maMiddle'] > df['maPrev']) & (df['maMiddle'] > df['maLast'])
    # arc_top_pattern = (df['maMiddle'] > df['maPrev']) & (df['maMiddle'] > df['maLast']) & (df['close_price'] == df['max_price'])
    # arc_top_points = df[arc_top_pattern]

    threshold = 0.08

    arc_points = []
    for index, row in df.iterrows():
        if index == None or index - 10 < 0: continue
        now_price = row['close_price']
        max_price = df['close_price'][index-10:index].max()
        min_price = df['close_price'][index-20:index-10].min()
        # 近期最高点跌了10%
        is_down_10 = (max_price - now_price) / max_price >= threshold
        # 近期高点前是否涨了上来的（形成圆弧顶）
        is_up_10 = (max_price - min_price) / max_price >= threshold
        # 是否接近了上次低点
        is_near_last_low_point = 0 < (now_price - min_price) / now_price <= threshold * 0.2
        if is_down_10 and is_up_10 and is_near_last_low_point:
            arc_points.append(df.iloc[index])
    arc_points_df = pandas.DataFrame(arc_points)

    plt.figure(figsize=(12, 6))
    plt.plot(df['datetime'], df['close_price'], label='close_price')
    # plt.plot(df['datetime'], df['max_price'], label='max_price')
    # plt.plot(df['datetime'], df['min_price'], label='min_price')
    # plt.plot(df['datetime'], df['maLast'], label='MA:20-30')
    # plt.plot(df['datetime'], df['maMiddle'], label='MA:10-20')
    # plt.plot(df['datetime'], df['maPrev'], label='MA:0-10')
    # plt.scatter(arc_top_points['datetime'], arc_top_points['close_price'], color='red', label='Arc Top')
    # plt.scatter(arc_top_points['datetime'], arc_points['close_price'], color='red', label='Arc Top')
    plt.scatter(arc_points_df['datetime'], arc_points_df['close_price'], color='red', label='Arc Top')

    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.tight_layout()
    plt.show()

    print(df['max_price'])
    print(df['min_price'])




# 10 20 30 20 10
# ma20=15
# ma30=20
# ma50=18
# ma15~25=20

# (ma35-ma20)/20*35
